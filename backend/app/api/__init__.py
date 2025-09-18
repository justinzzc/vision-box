#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API模块
"""

from fastapi import APIRouter
from .v1 import api_router as v1_router

# 创建主API路由
api_router = APIRouter()

# 包含v1版本的API
api_router.include_router(v1_router)

# API版本信息
API_VERSION = "1.0.0"
API_TITLE = "Vision Box API"
API_DESCRIPTION = "视觉检测应用API接口"

# 支持的API版本
SUPPORTED_VERSIONS = ["v1"]

# API状态
API_STATUS = {
    "version": API_VERSION,
    "title": API_TITLE,
    "description": API_DESCRIPTION,
    "supported_versions": SUPPORTED_VERSIONS,
    "status": "active"
}

__all__ = [
    "api_router",
    "API_VERSION",
    "API_TITLE",
    "API_DESCRIPTION",
    "API_STATUS"
]