#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API网关和认证中间件
"""

import time
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from collections import defaultdict

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.database import get_db
from app.models import ServiceToken, PublishedService, ServiceCall
from loguru import logger


class RateLimiter:
    """速率限制器"""
    
    def __init__(self):
        self.requests = defaultdict(list)
        self.cleanup_interval = 300  # 5分钟清理一次
        self.last_cleanup = time.time()
    
    def is_allowed(self, key: str, limit: int, window: int = 60) -> Tuple[bool, Dict]:
        """检查是否允许请求"""
        now = time.time()
        
        # 定期清理过期记录
        if now - self.last_cleanup > self.cleanup_interval:
            self._cleanup_expired_records(now)
            self.last_cleanup = now
        
        # 获取时间窗口内的请求记录
        window_start = now - window
        requests_in_window = [
            req_time for req_time in self.requests[key]
            if req_time > window_start
        ]
        
        # 更新请求记录
        self.requests[key] = requests_in_window
        
        # 检查是否超过限制
        current_count = len(requests_in_window)
        allowed = current_count < limit
        
        if allowed:
            self.requests[key].append(now)
        
        # 计算重置时间
        reset_time = int(now + window) if requests_in_window else int(now)
        remaining = max(0, limit - current_count - (1 if allowed else 0))
        
        return allowed, {
            "limit": limit,
            "remaining": remaining,
            "reset": reset_time,
            "current": current_count + (1 if allowed else 0)
        }
    
    def _cleanup_expired_records(self, now: float):
        """清理过期的请求记录"""
        cutoff = now - 3600  # 保留1小时内的记录
        for key in list(self.requests.keys()):
            self.requests[key] = [
                req_time for req_time in self.requests[key]
                if req_time > cutoff
            ]
            if not self.requests[key]:
                del self.requests[key]


class ServiceAuthMiddleware(BaseHTTPMiddleware):
    """服务认证中间件"""
    
    def __init__(self, app):
        super().__init__(app)
        self.rate_limiter = RateLimiter()
        self.service_paths = ["/api/services/", "/api/v1/services/"]
    
    async def dispatch(self, request: Request, call_next):
        """处理请求"""
        # 检查是否是服务调用路径
        if not self._is_service_call(request.url.path):
            return await call_next(request)
        
        # 提取服务ID
        service_id = self._extract_service_id(request.url.path)
        if not service_id:
            return await call_next(request)
        
        # 只对detect端点进行认证和限流
        if not request.url.path.endswith("/detect"):
            return await call_next(request)
        
        try:
            # 验证Token和权限
            token_info = await self._authenticate_request(request, service_id)
            if not token_info:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"error": "无效的访问令牌", "code": "INVALID_TOKEN"}
                )
            
            service, token = token_info
            
            # 检查服务状态
            if not service.is_active:
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"error": "服务已禁用", "code": "SERVICE_DISABLED"}
                )
            
            # 速率限制检查
            rate_limit_key = f"service:{service_id}:token:{token.id}"
            limit = token.rate_limit_override or service.rate_limit
            
            try:
                limit_value = int(limit) if isinstance(limit, str) else limit
            except (ValueError, TypeError):
                limit_value = service.rate_limit
            
            allowed, rate_info = self.rate_limiter.is_allowed(
                rate_limit_key, limit_value, 60
            )
            
            if not allowed:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "请求频率超过限制",
                        "code": "RATE_LIMIT_EXCEEDED",
                        "rate_limit": rate_info
                    },
                    headers={
                        "X-RateLimit-Limit": str(rate_info["limit"]),
                        "X-RateLimit-Remaining": str(rate_info["remaining"]),
                        "X-RateLimit-Reset": str(rate_info["reset"])
                    }
                )
            
            # IP白名单检查
            if token.ip_whitelist:
                client_ip = self._get_client_ip(request)
                try:
                    whitelist = json.loads(token.ip_whitelist)
                    if isinstance(whitelist, list) and client_ip not in whitelist:
                        return JSONResponse(
                            status_code=status.HTTP_403_FORBIDDEN,
                            content={"error": "IP地址不在白名单中", "code": "IP_NOT_ALLOWED"}
                        )
                except (json.JSONDecodeError, TypeError):
                    pass
            
            # 将认证信息添加到请求状态
            request.state.service = service
            request.state.token = token
            request.state.rate_info = rate_info
            
            # 记录请求开始时间
            start_time = time.time()
            
            # 执行请求
            response = await call_next(request)
            
            # 记录请求结束时间
            end_time = time.time()
            processing_time = end_time - start_time
            
            # 异步记录调用日志
            await self._log_service_call(
                request, service, token, response.status_code, processing_time
            )
            
            # 添加速率限制头
            response.headers["X-RateLimit-Limit"] = str(rate_info["limit"])
            response.headers["X-RateLimit-Remaining"] = str(rate_info["remaining"])
            response.headers["X-RateLimit-Reset"] = str(rate_info["reset"])
            
            return response
            
        except Exception as e:
            logger.error(f"服务认证中间件错误: {str(e)}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": "服务认证失败", "code": "AUTH_ERROR"}
            )
    
    def _is_service_call(self, path: str) -> bool:
        """检查是否是服务调用路径"""
        return any(path.startswith(service_path) for service_path in self.service_paths)
    
    def _extract_service_id(self, path: str) -> Optional[str]:
        """从路径中提取服务ID"""
        try:
            # 路径格式: /api/services/{service_id}/detect
            parts = path.strip("/").split("/")
            if len(parts) >= 3 and parts[1] == "services":
                return parts[2]
            # v1路径格式: /api/v1/services/{service_id}/detect
            elif len(parts) >= 4 and parts[1] == "v1" and parts[2] == "services":
                return parts[3]
        except (IndexError, ValueError):
            pass
        return None
    
    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP地址"""
        # 检查代理头
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    async def _authenticate_request(self, request: Request, service_id: str) -> Optional[Tuple]:
        """认证请求"""
        # 获取Authorization头
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
        
        token = auth_header[7:]  # 移除"Bearer "前缀
        
        # 获取数据库会话
        async for db in get_db():
            try:
                # 查询服务和令牌
                service_query = select(PublishedService).where(
                    and_(
                        PublishedService.id == service_id,
                        PublishedService.is_delete == False
                    )
                )
                service_result = await db.execute(service_query)
                service = service_result.scalar_one_or_none()
                
                if not service:
                    return None
                
                # 查询有效的令牌
                token_query = select(ServiceToken).where(
                    and_(
                        ServiceToken.service_id == service_id,
                        ServiceToken.is_active == True,
                        ServiceToken.is_revoked == False,
                        ServiceToken.is_delete == False
                    )
                )
                token_result = await db.execute(token_query)
                tokens = token_result.scalars().all()
                
                # 验证令牌
                for token_obj in tokens:
                    if token_obj.verify_token(token):
                        # 更新令牌使用统计
                        client_ip = self._get_client_ip(request)
                        token_obj.update_usage(client_ip)
                        await db.commit()
                        return service, token_obj
                
                return None
                
            except Exception as e:
                logger.error(f"认证请求时发生错误: {str(e)}")
                return None
            finally:
                await db.close()
    
    async def _log_service_call(self, request: Request, service: PublishedService, 
                               token: ServiceToken, status_code: int, processing_time: float):
        """记录服务调用日志"""
        try:
            async for db in get_db():
                try:
                    # 获取请求信息
                    client_ip = self._get_client_ip(request)
                    user_agent = request.headers.get("User-Agent", "")
                    referer = request.headers.get("Referer", "")
                    
                    # 生成请求ID
                    import uuid
                    request_id = str(uuid.uuid4())
                    
                    # 创建调用记录
                    call_record = ServiceCall(
                        service_id=service.id,
                        token_id=token.id,
                        request_id=request_id,
                        client_ip=client_ip,
                        user_agent=user_agent,
                        referer=referer,
                        http_method=request.method,
                        request_path=str(request.url.path),
                        status_code=status_code,
                        processing_time=processing_time,
                        success=200 <= status_code < 300,
                        model_used=service.model_name,
                        confidence_threshold=service.confidence_threshold
                    )
                    
                    # 设置请求头（过滤敏感信息）
                    safe_headers = {}
                    for key, value in request.headers.items():
                        if key.lower() not in ["authorization", "cookie", "x-api-key"]:
                            safe_headers[key] = value
                    call_record.set_request_headers(safe_headers)
                    
                    db.add(call_record)
                    
                    # 更新服务统计
                    service.increment_call_count(200 <= status_code < 300)
                    
                    await db.commit()
                    
                except Exception as e:
                    logger.error(f"记录服务调用日志失败: {str(e)}")
                    await db.rollback()
                finally:
                    await db.close()
                    
        except Exception as e:
            logger.error(f"记录服务调用日志时发生错误: {str(e)}")


class APIGatewayMiddleware(BaseHTTPMiddleware):
    """API网关中间件"""
    
    def __init__(self, app):
        super().__init__(app)
        self.start_time = time.time()
    
    async def dispatch(self, request: Request, call_next):
        """处理请求"""
        start_time = time.time()
        
        # 添加请求ID
        import uuid
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # 记录请求开始
        logger.info(
            f"Request started: {request.method} {request.url.path} "
            f"[{request_id}] from {request.client.host if request.client else 'unknown'}"
        )
        
        try:
            # 执行请求
            response = await call_next(request)
            
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 添加响应头
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(round(process_time, 4))
            response.headers["X-API-Version"] = "1.0.0"
            
            # 记录请求完成
            logger.info(
                f"Request completed: {request.method} {request.url.path} "
                f"[{request_id}] {response.status_code} in {process_time:.4f}s"
            )
            
            return response
            
        except Exception as e:
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 记录错误
            logger.error(
                f"Request failed: {request.method} {request.url.path} "
                f"[{request_id}] {str(e)} in {process_time:.4f}s"
            )
            
            # 返回错误响应
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "内部服务器错误",
                    "code": "INTERNAL_ERROR",
                    "request_id": request_id
                },
                headers={
                    "X-Request-ID": request_id,
                    "X-Process-Time": str(round(process_time, 4))
                }
            )


class CORSMiddleware(BaseHTTPMiddleware):
    """CORS中间件"""
    
    def __init__(self, app, allow_origins=None, allow_methods=None, allow_headers=None):
        super().__init__(app)
        self.allow_origins = allow_origins or ["*"]
        self.allow_methods = allow_methods or ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        self.allow_headers = allow_headers or ["*"]
    
    async def dispatch(self, request: Request, call_next):
        """处理CORS"""
        # 处理预检请求
        if request.method == "OPTIONS":
            response = JSONResponse(content={})
        else:
            response = await call_next(request)
        
        # 添加CORS头
        origin = request.headers.get("Origin")
        if origin and ("*" in self.allow_origins or origin in self.allow_origins):
            response.headers["Access-Control-Allow-Origin"] = origin
        elif "*" in self.allow_origins:
            response.headers["Access-Control-Allow-Origin"] = "*"
        
        response.headers["Access-Control-Allow-Methods"] = ", ".join(self.allow_methods)
        response.headers["Access-Control-Allow-Headers"] = ", ".join(self.allow_headers)
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Max-Age"] = "86400"
        
        return response