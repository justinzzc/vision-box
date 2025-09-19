#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统计分析API接口
"""

from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, text
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.models import PublishedService, ServiceCall, ServiceStats, ServiceToken, User
from app.api.v1.auth import get_current_active_user
from loguru import logger

router = APIRouter()


# Pydantic模型
class ServiceStatsResponse(BaseModel):
    """服务统计响应模型"""
    service_id: str
    service_name: str
    total_calls: int
    successful_calls: int
    failed_calls: int
    success_rate: float
    avg_response_time: float
    total_detections: int
    unique_ips: int
    active_tokens: int
    last_called_at: Optional[datetime]
    created_at: datetime


class CallLogResponse(BaseModel):
    """调用日志响应模型"""
    id: str
    service_id: str
    token_id: Optional[str]
    request_id: str
    client_ip: Optional[str]
    http_method: str
    request_path: str
    status_code: int
    processing_time: Optional[float]
    detection_count: Optional[int]
    success: bool
    error_message: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]


class CallLogListResponse(BaseModel):
    """调用日志列表响应模型"""
    logs: List[CallLogResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class DailyStatsResponse(BaseModel):
    """日统计响应模型"""
    date: date
    total_calls: int
    successful_calls: int
    failed_calls: int
    success_rate: float
    avg_response_time: float
    total_detections: int
    unique_ips: int


class StatsOverviewResponse(BaseModel):
    """统计概览响应模型"""
    total_services: int
    active_services: int
    total_calls_today: int
    total_calls_this_month: int
    avg_success_rate: float
    top_services: List[Dict[str, Any]]
    recent_activity: List[Dict[str, Any]]


class PerformanceMetrics(BaseModel):
    """性能指标模型"""
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    p95_response_time: float
    total_requests: int
    requests_per_minute: float
    error_rate: float


# 工具函数
async def get_service_by_id(service_id: str, db: AsyncSession, user: User) -> PublishedService:
    """根据ID获取服务"""
    query = select(PublishedService).where(
        and_(
            PublishedService.id == service_id,
            PublishedService.is_delete == False
        )
    )
    
    if not user.is_superuser:
        query = query.where(PublishedService.user_id == user.id)
    
    result = await db.execute(query)
    service = result.scalar_one_or_none()
    
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="服务不存在或无权限访问"
        )
    
    return service


# API端点
@router.get("/overview", response_model=StatsOverviewResponse, summary="统计概览")
async def get_stats_overview(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取用户的统计概览"""
    try:
        # 获取服务统计
        services_query = select(PublishedService).where(
            and_(
                PublishedService.user_id == current_user.id,
                PublishedService.is_delete == False
            )
        )
        services_result = await db.execute(services_query)
        services = services_result.scalars().all()
        
        total_services = len(services)
        active_services = len([s for s in services if s.status == "active"])
        
        # 今日调用统计
        today = date.today()
        today_calls_query = select(func.count(ServiceCall.id)).where(
            and_(
                ServiceCall.service_id.in_([s.id for s in services]),
                func.date(ServiceCall.created_at) == today
            )
        )
        today_calls_result = await db.execute(today_calls_query)
        total_calls_today = today_calls_result.scalar() or 0
        
        # 本月调用统计
        month_start = today.replace(day=1)
        month_calls_query = select(func.count(ServiceCall.id)).where(
            and_(
                ServiceCall.service_id.in_([s.id for s in services]),
                func.date(ServiceCall.created_at) >= month_start
            )
        )
        month_calls_result = await db.execute(month_calls_query)
        total_calls_this_month = month_calls_result.scalar() or 0
        
        # 平均成功率
        if services:
            avg_success_rate = sum(s.success_rate for s in services) / len(services)
        else:
            avg_success_rate = 0.0
        
        # 热门服务（按调用次数排序）
        top_services = sorted(
            [{
                "service_id": s.id,
                "service_name": s.service_name,
                "total_calls": s.total_calls,
                "success_rate": s.success_rate
            } for s in services],
            key=lambda x: x["total_calls"],
            reverse=True
        )[:5]
        
        # 最近活动
        recent_calls_query = select(ServiceCall).where(
            ServiceCall.service_id.in_([s.id for s in services])
        ).order_by(desc(ServiceCall.created_at)).limit(10)
        recent_calls_result = await db.execute(recent_calls_query)
        recent_calls = recent_calls_result.scalars().all()
        
        recent_activity = []
        for call in recent_calls:
            service = next((s for s in services if s.id == call.service_id), None)
            if service:
                recent_activity.append({
                    "service_name": service.service_name,
                    "status_code": call.status_code,
                    "success": call.success,
                    "processing_time": call.processing_time,
                    "created_at": call.created_at.isoformat()
                })
        
        return StatsOverviewResponse(
            total_services=total_services,
            active_services=active_services,
            total_calls_today=total_calls_today,
            total_calls_this_month=total_calls_this_month,
            avg_success_rate=avg_success_rate,
            top_services=top_services,
            recent_activity=recent_activity
        )
        
    except Exception as e:
        logger.error(f"获取统计概览失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取统计概览失败"
        )


@router.get("/services/{service_id}/stats", response_model=ServiceStatsResponse, summary="获取服务统计")
async def get_service_stats(
    service_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取指定服务的统计信息"""
    try:
        service = await get_service_by_id(service_id, db, current_user)
        
        # 获取唯一IP数量
        unique_ips_query = select(func.count(func.distinct(ServiceCall.client_ip))).where(
            ServiceCall.service_id == service_id
        )
        unique_ips_result = await db.execute(unique_ips_query)
        unique_ips = unique_ips_result.scalar() or 0
        
        # 获取活跃令牌数量
        active_tokens_query = select(func.count(ServiceToken.id)).where(
            and_(
                ServiceToken.service_id == service_id,
                ServiceToken.is_active == True,
                ServiceToken.is_revoked == False,
                ServiceToken.is_delete == False
            )
        )
        active_tokens_result = await db.execute(active_tokens_query)
        active_tokens = active_tokens_result.scalar() or 0
        
        # 获取总检测数量
        total_detections_query = select(func.sum(ServiceCall.detection_count)).where(
            and_(
                ServiceCall.service_id == service_id,
                ServiceCall.detection_count.isnot(None)
            )
        )
        total_detections_result = await db.execute(total_detections_query)
        total_detections = total_detections_result.scalar() or 0
        
        # 获取平均响应时间
        avg_response_time_query = select(func.avg(ServiceCall.processing_time)).where(
            and_(
                ServiceCall.service_id == service_id,
                ServiceCall.processing_time.isnot(None)
            )
        )
        avg_response_time_result = await db.execute(avg_response_time_query)
        avg_response_time = avg_response_time_result.scalar() or 0.0
        
        return ServiceStatsResponse(
            service_id=service.id,
            service_name=service.service_name,
            total_calls=service.total_calls,
            successful_calls=service.successful_calls,
            failed_calls=service.failed_calls,
            success_rate=service.success_rate,
            avg_response_time=float(avg_response_time),
            total_detections=int(total_detections),
            unique_ips=unique_ips,
            active_tokens=active_tokens,
            last_called_at=service.last_called_at,
            created_at=service.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取服务统计失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取服务统计失败"
        )


@router.get("/services/{service_id}/logs", response_model=CallLogListResponse, summary="获取服务调用日志")
async def get_service_logs(
    service_id: str,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status_filter: Optional[str] = Query(None, description="状态筛选(success/error)"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    client_ip: Optional[str] = Query(None, description="客户端IP筛选"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取服务调用日志"""
    try:
        # 验证服务权限
        await get_service_by_id(service_id, db, current_user)
        
        # 构建查询
        query = select(ServiceCall).where(
            and_(
                ServiceCall.service_id == service_id,
                ServiceCall.is_delete == False
            )
        )
        
        # 状态筛选
        if status_filter == "success":
            query = query.where(ServiceCall.success == True)
        elif status_filter == "error":
            query = query.where(ServiceCall.success == False)
        
        # 日期筛选
        if start_date:
            query = query.where(func.date(ServiceCall.created_at) >= start_date)
        if end_date:
            query = query.where(func.date(ServiceCall.created_at) <= end_date)
        
        # IP筛选
        if client_ip:
            query = query.where(ServiceCall.client_ip == client_ip)
        
        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await db.execute(count_query)
        total = count_result.scalar()
        
        # 分页
        offset = (page - 1) * page_size
        query = query.order_by(desc(ServiceCall.created_at)).offset(offset).limit(page_size)
        
        result = await db.execute(query)
        logs = result.scalars().all()
        
        # 转换为响应模型
        log_responses = []
        for log in logs:
            log_responses.append(CallLogResponse(
                id=log.id,
                service_id=log.service_id,
                token_id=log.token_id,
                request_id=log.request_id,
                client_ip=log.client_ip,
                http_method=log.http_method,
                request_path=log.request_path,
                status_code=log.status_code,
                processing_time=log.processing_time,
                detection_count=log.detection_count,
                success=log.success,
                error_message=log.error_message,
                created_at=log.created_at,
                completed_at=log.completed_at
            ))
        
        total_pages = (total + page_size - 1) // page_size
        
        return CallLogListResponse(
            logs=log_responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取服务调用日志失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取服务调用日志失败"
        )


@router.get("/services/{service_id}/daily-stats", response_model=List[DailyStatsResponse], summary="获取日统计")
async def get_daily_stats(
    service_id: str,
    days: int = Query(30, ge=1, le=365, description="统计天数"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取服务的日统计数据"""
    try:
        # 验证服务权限
        await get_service_by_id(service_id, db, current_user)
        
        # 计算日期范围
        end_date = date.today()
        start_date = end_date - timedelta(days=days-1)
        
        # 查询日统计数据
        query = text("""
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as total_calls,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_calls,
                SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failed_calls,
                AVG(CASE WHEN processing_time IS NOT NULL THEN processing_time ELSE 0 END) as avg_response_time,
                SUM(CASE WHEN detection_count IS NOT NULL THEN detection_count ELSE 0 END) as total_detections,
                COUNT(DISTINCT client_ip) as unique_ips
            FROM service_calls 
            WHERE service_id = :service_id 
                AND DATE(created_at) BETWEEN :start_date AND :end_date
                AND is_delete = 0
            GROUP BY DATE(created_at)
            ORDER BY DATE(created_at)
        """)
        
        result = await db.execute(query, {
            "service_id": service_id,
            "start_date": start_date,
            "end_date": end_date
        })
        
        rows = result.fetchall()
        
        # 构建响应数据
        daily_stats = []
        for row in rows:
            success_rate = (row.successful_calls / row.total_calls * 100) if row.total_calls > 0 else 0
            
            daily_stats.append(DailyStatsResponse(
                date=row.date,
                total_calls=row.total_calls,
                successful_calls=row.successful_calls,
                failed_calls=row.failed_calls,
                success_rate=success_rate,
                avg_response_time=float(row.avg_response_time),
                total_detections=int(row.total_detections),
                unique_ips=row.unique_ips
            ))
        
        return daily_stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取日统计失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取日统计失败"
        )


@router.get("/services/{service_id}/performance", response_model=PerformanceMetrics, summary="获取性能指标")
async def get_performance_metrics(
    service_id: str,
    hours: int = Query(24, ge=1, le=168, description="统计小时数"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取服务性能指标"""
    try:
        # 验证服务权限
        await get_service_by_id(service_id, db, current_user)
        
        # 计算时间范围
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        # 查询性能数据
        perf_query = text("""
            SELECT 
                AVG(processing_time) as avg_response_time,
                MIN(processing_time) as min_response_time,
                MAX(processing_time) as max_response_time,
                COUNT(*) as total_requests,
                SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as error_count
            FROM service_calls 
            WHERE service_id = :service_id 
                AND created_at BETWEEN :start_time AND :end_time
                AND processing_time IS NOT NULL
                AND is_delete = 0
        """)
        
        result = await db.execute(perf_query, {
            "service_id": service_id,
            "start_time": start_time,
            "end_time": end_time
        })
        
        row = result.fetchone()
        
        if not row or row.total_requests == 0:
            return PerformanceMetrics(
                avg_response_time=0.0,
                min_response_time=0.0,
                max_response_time=0.0,
                p95_response_time=0.0,
                total_requests=0,
                requests_per_minute=0.0,
                error_rate=0.0
            )
        
        # 查询P95响应时间
        p95_query = text("""
            SELECT processing_time
            FROM service_calls 
            WHERE service_id = :service_id 
                AND created_at BETWEEN :start_time AND :end_time
                AND processing_time IS NOT NULL
                AND is_delete = 0
            ORDER BY processing_time
            LIMIT 1 OFFSET :offset
        """)
        
        p95_offset = int(row.total_requests * 0.95)
        p95_result = await db.execute(p95_query, {
            "service_id": service_id,
            "start_time": start_time,
            "end_time": end_time,
            "offset": p95_offset
        })
        
        p95_row = p95_result.fetchone()
        p95_response_time = p95_row.processing_time if p95_row else row.max_response_time
        
        # 计算每分钟请求数
        requests_per_minute = row.total_requests / (hours * 60)
        
        # 计算错误率
        error_rate = (row.error_count / row.total_requests * 100) if row.total_requests > 0 else 0
        
        return PerformanceMetrics(
            avg_response_time=float(row.avg_response_time),
            min_response_time=float(row.min_response_time),
            max_response_time=float(row.max_response_time),
            p95_response_time=float(p95_response_time),
            total_requests=row.total_requests,
            requests_per_minute=requests_per_minute,
            error_rate=error_rate
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取性能指标失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取性能指标失败"
        )