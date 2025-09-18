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

# 添加历史记录路由别名（兼容前端）
api_router.include_router(
    detection_router,
    prefix="",
    tags=["历史记录"],
    include_in_schema=False
)

# API v1信息
API_V1_INFO = {
    "version": "1.0.0",
    "description": "Vision Box API v1版本",
    "endpoints": {
        "auth": "用户认证相关接口",
        "files": "文件上传和管理接口",
        "detection": "视觉检测相关接口",
        "users": "用户管理接口",
        "system": "系统管理接口"
    }
}

__all__ = [
    "api_router",
    "API_V1_INFO"
]