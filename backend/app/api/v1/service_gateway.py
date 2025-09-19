#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
服务网关API接口 - 第三方调用检测服务
"""

import os
import uuid
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.config import get_settings
from app.models import PublishedService, ServiceToken, ServiceCall, FileRecord
from app.services import DetectionService, FileService
from loguru import logger

settings = get_settings()
router = APIRouter()


# Pydantic模型
class ServiceDetectionRequest(BaseModel):
    """服务检测请求模型"""
    callback_url: Optional[str] = Field(None, description="异步回调地址")
    custom_params: Optional[Dict[str, Any]] = Field(None, description="自定义参数")


class ServiceDetectionResponse(BaseModel):
    """服务检测响应模型"""
    success: bool
    task_id: Optional[str]
    result: Optional[Dict[str, Any]]
    processing_time: float
    message: str
    request_id: str


class ServiceDetectionResult(BaseModel):
    """检测结果模型"""
    detections: list
    class_counts: Dict[str, int]
    total_detections: int
    confidence_threshold: float
    model_used: str
    processing_time: float
    image_info: Optional[Dict[str, Any]]
    annotated_url: Optional[str]


# 工具函数
def validate_file_format(filename: str, allowed_formats: list) -> bool:
    """验证文件格式"""
    if not filename or not allowed_formats:
        return True
    
    ext = os.path.splitext(filename)[1].lower().lstrip('.')
    return ext in [fmt.lower().lstrip('.') for fmt in allowed_formats]


def validate_file_size(file_size: int, max_size: int) -> bool:
    """验证文件大小"""
    return file_size <= max_size


async def get_service_from_request(request: Request) -> PublishedService:
    """从请求中获取服务信息"""
    if not hasattr(request.state, 'service'):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未找到服务信息"
        )
    return request.state.service


async def get_token_from_request(request: Request) -> ServiceToken:
    """从请求中获取令牌信息"""
    if not hasattr(request.state, 'token'):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未找到令牌信息"
        )
    return request.state.token


# API端点
@router.post("/{service_id}/detect", response_model=ServiceDetectionResponse, summary="服务检测接口")
async def service_detect(
    service_id: str,
    request: Request,
    file: UploadFile = File(..., description="待检测的图片或视频文件"),
    callback_url: Optional[str] = Form(None, description="异步回调地址"),
    custom_params: Optional[str] = Form(None, description="自定义参数(JSON字符串)"),
    db: AsyncSession = Depends(get_db)
):
    """第三方调用检测服务接口"""
    start_time = datetime.utcnow()
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
    
    try:
        # 从中间件获取服务和令牌信息
        service = await get_service_from_request(request)
        token = await get_token_from_request(request)
        
        # 验证文件格式
        if not validate_file_format(file.filename, service.get_allowed_formats()):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的文件格式。支持的格式: {', '.join(service.get_allowed_formats())}"
            )
        
        # 读取文件内容
        file_content = await file.read()
        file_size = len(file_content)
        
        # 验证文件大小
        if not validate_file_size(file_size, service.max_file_size):
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"文件大小超过限制。最大允许: {service.max_file_size / 1024 / 1024:.1f}MB"
            )
        
        # 保存文件
        file_service = FileService()
        file_record = await file_service.save_uploaded_file(
            file_content=file_content,
            filename=file.filename,
            content_type=file.content_type
        )
        
        # 添加文件记录到数据库
        db.add(file_record)
        await db.flush()
        
        # 解析自定义参数
        custom_params_dict = {}
        if custom_params:
            try:
                import json
                custom_params_dict = json.loads(custom_params)
            except json.JSONDecodeError:
                logger.warning(f"无法解析自定义参数: {custom_params}")
        
        # 执行检测
        detection_service = DetectionService()
        
        # 根据文件类型选择检测方法
        if file_record.file_type == "image":
            result = await detection_service.detect_image(
                file_path=file_record.file_path,
                model_name=service.model_name,
                confidence=service.confidence_threshold,
                classes=service.get_detection_classes()
            )
        elif file_record.file_type == "video":
            result = await detection_service.detect_video(
                file_path=file_record.file_path,
                model_name=service.model_name,
                confidence=service.confidence_threshold,
                classes=service.get_detection_classes()
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不支持的文件类型"
            )
        
        # 计算处理时间
        end_time = datetime.utcnow()
        processing_time = (end_time - start_time).total_seconds()
        
        # 构建响应结果
        detection_result = ServiceDetectionResult(
            detections=result.get("detections", []),
            class_counts=result.get("class_counts", {}),
            total_detections=result.get("total_detections", 0),
            confidence_threshold=service.confidence_threshold,
            model_used=service.model_name,
            processing_time=processing_time,
            image_info=result.get("image_info"),
            annotated_url=result.get("annotated_url")
        )
        
        # 更新调用记录
        if hasattr(request.state, 'call_record'):
            call_record = request.state.call_record
            call_record.complete_call(
                status_code=200,
                success=True,
                detection_count=result.get("total_detections", 0),
                processing_time=processing_time
            )
            call_record.file_name = file.filename
            call_record.file_size = file_size
            call_record.file_type = file_record.file_type
        
        await db.commit()
        
        # 异步回调处理
        if callback_url:
            asyncio.create_task(
                send_callback(callback_url, {
                    "request_id": request_id,
                    "success": True,
                    "result": detection_result.dict(),
                    "processing_time": processing_time
                })
            )
        
        logger.info(
            f"服务 {service.service_name} 检测完成: {result.get('total_detections', 0)} 个对象, "
            f"处理时间: {processing_time:.2f}s"
        )
        
        return ServiceDetectionResponse(
            success=True,
            task_id=None,  # 同步处理，无需任务ID
            result=detection_result.dict(),
            processing_time=processing_time,
            message="检测完成",
            request_id=request_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        # 计算处理时间
        end_time = datetime.utcnow()
        processing_time = (end_time - start_time).total_seconds()
        
        # 更新调用记录
        if hasattr(request.state, 'call_record'):
            call_record = request.state.call_record
            call_record.set_error(
                error_code="DETECTION_ERROR",
                error_message=str(e),
                status_code=500
            )
            call_record.processing_time = processing_time
        
        await db.rollback()
        
        # 异步回调处理
        if callback_url:
            asyncio.create_task(
                send_callback(callback_url, {
                    "request_id": request_id,
                    "success": False,
                    "error": str(e),
                    "processing_time": processing_time
                })
            )
        
        logger.error(f"服务检测失败: {str(e)}")
        
        return ServiceDetectionResponse(
            success=False,
            task_id=None,
            result=None,
            processing_time=processing_time,
            message=f"检测失败: {str(e)}",
            request_id=request_id
        )


@router.get("/{service_id}/info", summary="获取服务信息")
async def get_service_info(
    service_id: str,
    request: Request
):
    """获取服务基本信息（无需认证）"""
    try:
        async for db in get_db():
            try:
                # 查询服务信息
                query = select(PublishedService).where(
                    PublishedService.id == service_id,
                    PublishedService.is_delete == False,
                    PublishedService.status == "active"
                )
                result = await db.execute(query)
                service = result.scalar_one_or_none()
                
                if not service:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="服务不存在或已禁用"
                    )
                
                return {
                    "service_id": service.id,
                    "service_name": service.service_name,
                    "description": service.description,
                    "model_name": service.model_name,
                    "confidence_threshold": service.confidence_threshold,
                    "detection_classes": service.get_detection_classes(),
                    "allowed_formats": service.get_allowed_formats(),
                    "max_file_size": service.max_file_size,
                    "rate_limit": service.rate_limit,
                    "api_endpoint": service.api_endpoint,
                    "status": service.status,
                    "created_at": service.created_at.isoformat()
                }
                
            finally:
                await db.close()
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取服务信息失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取服务信息失败"
        )


@router.get("/{service_id}/health", summary="服务健康检查")
async def service_health_check(
    service_id: str,
    request: Request
):
    """服务健康检查"""
    try:
        async for db in get_db():
            try:
                # 查询服务状态
                query = select(PublishedService).where(
                    PublishedService.id == service_id,
                    PublishedService.is_delete == False
                )
                result = await db.execute(query)
                service = result.scalar_one_or_none()
                
                if not service:
                    return JSONResponse(
                        status_code=status.HTTP_404_NOT_FOUND,
                        content={
                            "status": "not_found",
                            "message": "服务不存在",
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    )
                
                # 检查服务状态
                is_healthy = service.status == "active" and service.is_active
                
                return {
                    "status": "healthy" if is_healthy else "unhealthy",
                    "service_id": service.id,
                    "service_name": service.service_name,
                    "service_status": service.status,
                    "total_calls": service.total_calls,
                    "success_rate": service.success_rate,
                    "last_called_at": service.last_called_at.isoformat() if service.last_called_at else None,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
            finally:
                await db.close()
                
    except Exception as e:
        logger.error(f"服务健康检查失败: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "message": "健康检查失败",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )


async def send_callback(callback_url: str, data: dict):
    """发送异步回调"""
    try:
        import aiohttp
        import asyncio
        
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                callback_url,
                json=data,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    logger.info(f"回调成功发送到: {callback_url}")
                else:
                    logger.warning(f"回调发送失败: {callback_url}, 状态码: {response.status}")
                    
    except asyncio.TimeoutError:
        logger.error(f"回调超时: {callback_url}")
    except Exception as e:
        logger.error(f"发送回调失败: {callback_url}, 错误: {str(e)}")