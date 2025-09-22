#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
服务发布API接口
"""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.config import get_settings
from app.models import PublishedService, ServiceToken, ServiceCall, ServiceStats, User
from app.api.v1.auth import get_current_active_user
from loguru import logger

settings = get_settings()
router = APIRouter()


# Pydantic模型
class ServiceCreate(BaseModel):
    """服务创建模型"""
    service_name: str = Field(..., min_length=1, max_length=200, description="服务名称")
    description: Optional[str] = Field(None, max_length=1000, description="服务描述")
    model_name: str = Field(..., description="检测模型")
    confidence_threshold: float = Field(0.5, ge=0.0, le=1.0, description="置信度阈值")
    detection_classes: Optional[List[str]] = Field(None, description="检测类别列表")
    rate_limit: int = Field(100, ge=1, le=10000, description="调用频率限制(次/分钟)")
    max_file_size: int = Field(10485760, ge=1024, le=104857600, description="最大文件大小(字节)")
    allowed_formats: Optional[List[str]] = Field(None, description="允许的文件格式")


class ServiceUpdate(BaseModel):
    """服务更新模型"""
    service_name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    model_name: Optional[str] = None
    confidence_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)
    detection_classes: Optional[List[str]] = None
    rate_limit: Optional[int] = Field(None, ge=1, le=10000)
    max_file_size: Optional[int] = Field(None, ge=1024, le=104857600)
    allowed_formats: Optional[List[str]] = None


class ServiceResponse(BaseModel):
    """服务响应模型"""
    id: str
    user_id: str
    service_name: str
    description: Optional[str]
    status: str
    model_name: str
    confidence_threshold: float
    detection_classes: List[str]
    api_endpoint: str
    rate_limit: int
    max_file_size: int
    allowed_formats: List[str]
    total_calls: int
    successful_calls: int
    failed_calls: int
    success_rate: float
    last_called_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class ServiceListResponse(BaseModel):
    """服务列表响应模型"""
    services: List[ServiceResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ServiceCreateResponse(BaseModel):
    """服务创建响应模型"""
    service_id: str
    api_endpoint: str
    access_token: str
    status: str
    message: str


# 工具函数
def generate_api_endpoint(service_id: str) -> str:
    """生成API端点"""
    return f"/api/v1/pubbed_services/{service_id}/detect"


async def get_service_by_id(service_id: str, db: AsyncSession, user: User = None, include_deleted: bool = False) -> PublishedService:
    """根据ID获取服务"""
    query = select(PublishedService).where(PublishedService.id == service_id)
    
    if not include_deleted:
        query = query.where(PublishedService.is_delete == False)
    
    if user and not user.is_superuser:
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
@router.post("/", response_model=ServiceCreateResponse, summary="创建服务")
async def create_service(
    service_data: ServiceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """创建新的API服务"""
    try:
        # 检查服务名称是否已存在
        query = select(PublishedService).where(
            and_(
                PublishedService.user_id == current_user.id,
                PublishedService.service_name == service_data.service_name,
                PublishedService.is_delete == False
            )
        )
        result = await db.execute(query)
        existing_service = result.scalar_one_or_none()
        
        if existing_service:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="服务名称已存在"
            )
        
        # 创建服务
        service_id = str(uuid.uuid4())
        api_endpoint = generate_api_endpoint(service_id)
        
        new_service = PublishedService(
            id=service_id,
            user_id=current_user.id,
            service_name=service_data.service_name,
            description=service_data.description,
            model_name=service_data.model_name,
            confidence_threshold=service_data.confidence_threshold,
            api_endpoint=api_endpoint,
            rate_limit=service_data.rate_limit,
            max_file_size=service_data.max_file_size
        )
        
        # 设置检测类别和允许格式
        if service_data.detection_classes:
            new_service.set_detection_classes(service_data.detection_classes)
        
        if service_data.allowed_formats:
            new_service.set_allowed_formats(service_data.allowed_formats)
        
        db.add(new_service)
        await db.flush()
        
        # 生成默认访问令牌
        token_instance, access_token = ServiceToken.generate_token(
            service_id=service_id,
            token_name="默认令牌",
            expires_hours=24 * 7  # 7天过期
        )
        
        db.add(token_instance)
        await db.commit()
        
        logger.info(f"用户 {current_user.username} 创建了服务: {service_data.service_name}")
        
        return ServiceCreateResponse(
            service_id=service_id,
            api_endpoint=api_endpoint,
            access_token=access_token,
            status="active",
            message="服务创建成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"创建服务失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服务创建失败"
        )


@router.get("/", response_model=ServiceListResponse, summary="获取服务列表")
async def get_services(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    status_filter: Optional[str] = Query(None, description="状态筛选"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    include_deleted: bool = Query(False, description="是否包含已删除的服务"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取用户的服务列表"""
    try:
        logger.info(f"用户 {current_user.username} 获取服务列表, 页码: {page}, 每页数量: {page_size}, 状态筛选: {status_filter}, 搜索关键词: {search}, 包含已删除服务: {include_deleted}")
        # 构建查询
        query = select(PublishedService).where(PublishedService.user_id == current_user.id)
        
        # 是否包含已删除的服务
        if not include_deleted or not current_user.is_superuser:
            query = query.where(PublishedService.is_delete == False)
        
        # 状态筛选
        if status_filter:
            query = query.where(PublishedService.status == status_filter)
        
        # 搜索
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                or_(
                    PublishedService.service_name.ilike(search_pattern),
                    PublishedService.description.ilike(search_pattern)
                )
            )
        
        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await db.execute(count_query)
        total = count_result.scalar()
        
        # 分页
        offset = (page - 1) * page_size
        query = query.order_by(PublishedService.created_at.desc()).offset(offset).limit(page_size)
        
        result = await db.execute(query)
        services = result.scalars().all()
        
        # 转换为响应模型
        service_responses = []
        for service in services:
            service_responses.append(ServiceResponse(
                id=service.id,
                user_id=service.user_id,
                service_name=service.service_name,
                description=service.description,
                status=service.status,
                model_name=service.model_name,
                confidence_threshold=service.confidence_threshold,
                detection_classes=service.get_detection_classes(),
                api_endpoint=service.api_endpoint,
                rate_limit=service.rate_limit,
                max_file_size=service.max_file_size,
                allowed_formats=service.get_allowed_formats(),
                total_calls=service.total_calls,
                successful_calls=service.successful_calls,
                failed_calls=service.failed_calls,
                success_rate=service.success_rate,
                last_called_at=service.last_called_at,
                created_at=service.created_at,
                updated_at=service.updated_at
            ))
        
        total_pages = (total + page_size - 1) // page_size
        
        return ServiceListResponse(
            services=service_responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(f"获取服务列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取服务列表失败"
        )


@router.get("/{service_id}", response_model=ServiceResponse, summary="获取服务详情")
async def get_service(
    service_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取指定服务的详细信息"""
    service = await get_service_by_id(service_id, db, current_user)
    
    return ServiceResponse(
        id=service.id,
        user_id=service.user_id,
        service_name=service.service_name,
        description=service.description,
        status=service.status,
        model_name=service.model_name,
        confidence_threshold=service.confidence_threshold,
        detection_classes=service.get_detection_classes(),
        api_endpoint=service.api_endpoint,
        rate_limit=service.rate_limit,
        max_file_size=service.max_file_size,
        allowed_formats=service.get_allowed_formats(),
        total_calls=service.total_calls,
        successful_calls=service.successful_calls,
        failed_calls=service.failed_calls,
        success_rate=service.success_rate,
        last_called_at=service.last_called_at,
        created_at=service.created_at,
        updated_at=service.updated_at
    )


@router.put("/{service_id}", response_model=ServiceResponse, summary="更新服务")
async def update_service(
    service_id: str,
    service_data: ServiceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """更新服务配置"""
    try:
        service = await get_service_by_id(service_id, db, current_user)
        
        # 检查服务名称是否已存在（排除当前服务）
        if service_data.service_name and service_data.service_name != service.service_name:
            query = select(PublishedService).where(
                and_(
                    PublishedService.user_id == current_user.id,
                    PublishedService.service_name == service_data.service_name,
                    PublishedService.id != service_id,
                    PublishedService.is_delete == False
                )
            )
            result = await db.execute(query)
            existing_service = result.scalar_one_or_none()
            
            if existing_service:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="服务名称已存在"
                )
        
        # 更新字段
        update_data = service_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if field == "detection_classes":
                service.set_detection_classes(value)
            elif field == "allowed_formats":
                service.set_allowed_formats(value)
            else:
                setattr(service, field, value)
        
        service.updated_at = datetime.utcnow()
        await db.commit()
        
        logger.info(f"用户 {current_user.username} 更新了服务: {service.service_name}")
        
        return ServiceResponse(
            id=service.id,
            user_id=service.user_id,
            service_name=service.service_name,
            description=service.description,
            status=service.status,
            model_name=service.model_name,
            confidence_threshold=service.confidence_threshold,
            detection_classes=service.get_detection_classes(),
            api_endpoint=service.api_endpoint,
            rate_limit=service.rate_limit,
            max_file_size=service.max_file_size,
            allowed_formats=service.get_allowed_formats(),
            total_calls=service.total_calls,
            successful_calls=service.successful_calls,
            failed_calls=service.failed_calls,
            success_rate=service.success_rate,
            last_called_at=service.last_called_at,
            created_at=service.created_at,
            updated_at=service.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"更新服务失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新服务失败"
        )


@router.put("/{service_id}/disable", summary="禁用服务")
async def disable_service(
    service_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """禁用服务"""
    try:
        service = await get_service_by_id(service_id, db, current_user)
        
        service.disable()
        await db.commit()
        
        logger.info(f"用户 {current_user.username} 禁用了服务: {service.service_name}")
        
        return {"message": "服务已禁用", "status": "disabled"}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"禁用服务失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="禁用服务失败"
        )


@router.put("/{service_id}/enable", summary="启用服务")
async def enable_service(
    service_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """启用服务"""
    try:
        service = await get_service_by_id(service_id, db, current_user)
        
        service.enable()
        await db.commit()
        
        logger.info(f"用户 {current_user.username} 启用了服务: {service.service_name}")
        
        return {"message": "服务已启用", "status": "active"}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"启用服务失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="启用服务失败"
        )


@router.delete("/{service_id}", summary="删除服务")
async def delete_service(
    service_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """逻辑删除服务"""
    try:
        service = await get_service_by_id(service_id, db, current_user)
        
        service.soft_delete()
        await db.commit()
        
        logger.info(f"用户 {current_user.username} 删除了服务: {service.service_name}")
        
        return {"message": "服务已删除", "status": "deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"删除服务失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除服务失败"
        )


@router.post("/{service_id}/restore", summary="恢复服务")
async def restore_service(
    service_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """恢复已删除的服务（管理员权限）"""
    try:
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="需要管理员权限"
            )
        
        service = await get_service_by_id(service_id, db, current_user, include_deleted=True)
        
        if not service.is_delete:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="服务未被删除"
            )
        
        service.restore()
        await db.commit()
        
        logger.info(f"管理员 {current_user.username} 恢复了服务: {service.service_name}")
        
        return {"message": "服务已恢复", "status": "active"}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"恢复服务失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="恢复服务失败"
        )