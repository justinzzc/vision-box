#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Token管理API接口
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.models import PublishedService, ServiceToken, User
from app.api.v1.auth import get_current_active_user
from loguru import logger

router = APIRouter()


# Pydantic模型
class TokenCreate(BaseModel):
    """令牌创建模型"""
    token_name: str = Field(..., min_length=1, max_length=200, description="令牌名称")
    expires_hours: Optional[int] = Field(None, ge=1, le=8760, description="过期时间(小时)")
    permissions: Optional[List[str]] = Field(None, description="权限列表")
    rate_limit_override: Optional[str] = Field(None, description="覆盖的频率限制")
    ip_whitelist: Optional[List[str]] = Field(None, description="IP白名单")


class TokenResponse(BaseModel):
    """令牌响应模型"""
    id: str
    service_id: str
    token_name: str
    token_prefix: str
    is_active: bool
    is_revoked: bool
    usage_count: str
    last_used_at: Optional[datetime]
    last_used_ip: Optional[str]
    expires_at: Optional[datetime]
    days_until_expiry: int
    is_expired: bool
    is_valid: bool
    created_at: datetime
    updated_at: datetime


class TokenCreateResponse(BaseModel):
    """令牌创建响应模型"""
    token_id: str
    token_name: str
    access_token: str
    expires_at: Optional[datetime]
    message: str


class TokenListResponse(BaseModel):
    """令牌列表响应模型"""
    tokens: List[TokenResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


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


async def get_token_by_id(token_id: str, service_id: str, db: AsyncSession, user: User) -> ServiceToken:
    """根据ID获取令牌"""
    # 先验证服务权限
    await get_service_by_id(service_id, db, user)
    
    query = select(ServiceToken).where(
        and_(
            ServiceToken.id == token_id,
            ServiceToken.service_id == service_id,
            ServiceToken.is_delete == False
        )
    )
    
    result = await db.execute(query)
    token = result.scalar_one_or_none()
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="令牌不存在或无权限访问"
        )
    
    return token


# API端点
@router.post("/{service_id}/tokens", response_model=TokenCreateResponse, summary="生成访问令牌")
async def create_token(
    service_id: str,
    token_data: TokenCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """为指定服务生成新的访问令牌"""
    try:
        # 验证服务权限
        service = await get_service_by_id(service_id, db, current_user)
        
        # 检查令牌名称是否已存在
        query = select(ServiceToken).where(
            and_(
                ServiceToken.service_id == service_id,
                ServiceToken.token_name == token_data.token_name,
                ServiceToken.is_delete == False
            )
        )
        result = await db.execute(query)
        existing_token = result.scalar_one_or_none()
        
        if existing_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="令牌名称已存在"
            )
        
        # 生成令牌
        token_instance, access_token = ServiceToken.generate_token(
            service_id=service_id,
            token_name=token_data.token_name,
            expires_hours=token_data.expires_hours
        )
        
        # 设置权限和限制
        if token_data.permissions:
            token_instance.permissions = str(token_data.permissions)
        
        if token_data.rate_limit_override:
            token_instance.rate_limit_override = token_data.rate_limit_override
        
        if token_data.ip_whitelist:
            token_instance.ip_whitelist = str(token_data.ip_whitelist)
        
        db.add(token_instance)
        await db.commit()
        
        logger.info(f"用户 {current_user.username} 为服务 {service.service_name} 创建了令牌: {token_data.token_name}")
        
        return TokenCreateResponse(
            token_id=token_instance.id,
            token_name=token_instance.token_name,
            access_token=access_token,
            expires_at=token_instance.expires_at,
            message="令牌创建成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"创建令牌失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建令牌失败"
        )


@router.get("/{service_id}/tokens", response_model=TokenListResponse, summary="获取服务令牌列表")
async def get_tokens(
    service_id: str,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    include_revoked: bool = Query(False, description="是否包含已撤销的令牌"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取指定服务的所有令牌"""
    try:
        # 验证服务权限
        await get_service_by_id(service_id, db, current_user)
        
        # 构建查询
        query = select(ServiceToken).where(
            and_(
                ServiceToken.service_id == service_id,
                ServiceToken.is_delete == False
            )
        )
        
        # 是否包含已撤销的令牌
        if not include_revoked:
            query = query.where(ServiceToken.is_revoked == False)
        
        # 获取总数
        from sqlalchemy import func
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await db.execute(count_query)
        total = count_result.scalar()
        
        # 分页
        offset = (page - 1) * page_size
        query = query.order_by(ServiceToken.created_at.desc()).offset(offset).limit(page_size)
        
        result = await db.execute(query)
        tokens = result.scalars().all()
        
        # 转换为响应模型
        token_responses = []
        for token in tokens:
            token_responses.append(TokenResponse(
                id=token.id,
                service_id=token.service_id,
                token_name=token.token_name,
                token_prefix=token.token_prefix,
                is_active=token.is_active,
                is_revoked=token.is_revoked,
                usage_count=token.usage_count,
                last_used_at=token.last_used_at,
                last_used_ip=token.last_used_ip,
                expires_at=token.expires_at,
                days_until_expiry=token.days_until_expiry,
                is_expired=token.is_expired,
                is_valid=token.is_valid,
                created_at=token.created_at,
                updated_at=token.updated_at
            ))
        
        total_pages = (total + page_size - 1) // page_size
        
        return TokenListResponse(
            tokens=token_responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取令牌列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取令牌列表失败"
        )


@router.get("/{service_id}/tokens/{token_id}", response_model=TokenResponse, summary="获取令牌详情")
async def get_token(
    service_id: str,
    token_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取指定令牌的详细信息"""
    token = await get_token_by_id(token_id, service_id, db, current_user)
    
    return TokenResponse(
        id=token.id,
        service_id=token.service_id,
        token_name=token.token_name,
        token_prefix=token.token_prefix,
        is_active=token.is_active,
        is_revoked=token.is_revoked,
        usage_count=token.usage_count,
        last_used_at=token.last_used_at,
        last_used_ip=token.last_used_ip,
        expires_at=token.expires_at,
        days_until_expiry=token.days_until_expiry,
        is_expired=token.is_expired,
        is_valid=token.is_valid,
        created_at=token.created_at,
        updated_at=token.updated_at
    )


@router.put("/{service_id}/tokens/{token_id}/activate", summary="激活令牌")
async def activate_token(
    service_id: str,
    token_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """激活令牌"""
    try:
        token = await get_token_by_id(token_id, service_id, db, current_user)
        
        token.activate()
        await db.commit()
        
        logger.info(f"用户 {current_user.username} 激活了令牌: {token.token_name}")
        
        return {"message": "令牌已激活", "status": "active"}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"激活令牌失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="激活令牌失败"
        )


@router.put("/{service_id}/tokens/{token_id}/deactivate", summary="停用令牌")
async def deactivate_token(
    service_id: str,
    token_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """停用令牌"""
    try:
        token = await get_token_by_id(token_id, service_id, db, current_user)
        
        token.deactivate()
        await db.commit()
        
        logger.info(f"用户 {current_user.username} 停用了令牌: {token.token_name}")
        
        return {"message": "令牌已停用", "status": "inactive"}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"停用令牌失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="停用令牌失败"
        )


@router.delete("/{service_id}/tokens/{token_id}", summary="撤销令牌")
async def revoke_token(
    service_id: str,
    token_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """撤销指定令牌"""
    try:
        token = await get_token_by_id(token_id, service_id, db, current_user)
        
        token.revoke()
        await db.commit()
        
        logger.info(f"用户 {current_user.username} 撤销了令牌: {token.token_name}")
        
        return {"message": "令牌已撤销", "status": "revoked"}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"撤销令牌失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="撤销令牌失败"
        )


@router.delete("/{service_id}/tokens/{token_id}/permanent", summary="永久删除令牌")
async def delete_token_permanent(
    service_id: str,
    token_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """永久删除令牌（逻辑删除）"""
    try:
        token = await get_token_by_id(token_id, service_id, db, current_user)
        
        token.soft_delete()
        await db.commit()
        
        logger.info(f"用户 {current_user.username} 删除了令牌: {token.token_name}")
        
        return {"message": "令牌已删除", "status": "deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"删除令牌失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除令牌失败"
        )