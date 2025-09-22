#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API v1版本模块
"""

from fastapi import APIRouter
from .auth import router as auth_router
from .files import router as files_router
from .detection import router as detection_router
from .users import router as users_router
from .system import router as system_router
from .services import router as services_router
from .tokens import router as tokens_router
from .service_gateway import router as service_gateway_router
from .analytics import router as analytics_router

# 创建v1 API路由
api_router = APIRouter()

# 包含各个模块的路由
api_router.include_router(
    auth_router,
    prefix="/auth",
    tags=["认证"]
)

api_router.include_router(
    files_router,
    prefix="/files",
    tags=["文件管理"]
)

api_router.include_router(
    detection_router,
    prefix="/detection",
    tags=["视觉检测"]
)

api_router.include_router(
    users_router,
    prefix="/users",
    tags=["用户管理"]
)

api_router.include_router(
    system_router,
    prefix="/system",
    tags=["系统管理"]
)

# 注册services主路由
api_router.include_router(
    services_router,
    prefix="/pub_services",
    tags=["服务发布"]
)

# 注册tokens路由，使用独立的前缀避免冲突
api_router.include_router(
    tokens_router,
    prefix="/tokens",
    tags=["Token管理"]
)

# 统一使用pubbed_services路由，用于第三方API调用
api_router.include_router(
    service_gateway_router,
    prefix="/pubbed_services",
    tags=["发布服务API"]
)

api_router.include_router(
    analytics_router,
    prefix="/analytics",
    tags=["统计分析"]
)

# 历史记录路由别名已移除，避免路由冲突

# API v1信息
API_V1_INFO = {
    "version": "1.0.0",
    "description": "Vision Box API v1版本",
    "endpoints": {
        "auth": "用户认证相关接口",
        "files": "文件上传和管理接口",
        "detection": "视觉检测相关接口",
        "users": "用户管理接口",
        "system": "系统管理接口",
        "services": "服务发布和管理接口",
        "tokens": "Token管理接口",
        "service_gateway": "服务网关接口",
        "analytics": "统计分析接口"
    }
}

__all__ = [
    "api_router",
    "API_V1_INFO"
]