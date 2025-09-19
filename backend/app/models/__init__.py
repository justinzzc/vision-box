#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据模型模块
"""

from .user import User
from .file_record import FileRecord, FileType
from .detection_task import DetectionTask, TaskStatus, DetectionType
from .published_service import PublishedService, ServiceStatus
from .service_token import ServiceToken
from .service_call import ServiceCall
from .service_stats import ServiceStats

# 导出所有模型
__all__ = [
    "User",
    "FileRecord",
    "FileType",
    "DetectionTask",
    "TaskStatus",
    "DetectionType",
    "PublishedService",
    "ServiceStatus",
    "ServiceToken",
    "ServiceCall",
    "ServiceStats"
]

# 模型注册表（用于数据库初始化）
MODELS = [
    User,
    FileRecord,
    DetectionTask,
    PublishedService,
    ServiceToken,
    ServiceCall,
    ServiceStats
]

# 枚举类型注册表
ENUMS = {
    "FileType": FileType,
    "TaskStatus": TaskStatus,
    "DetectionType": DetectionType,
    "ServiceStatus": ServiceStatus
}

# 模型关系映射
MODEL_RELATIONSHIPS = {
    "User": {
        "detection_tasks": "DetectionTask",
        "published_services": "PublishedService"
    },
    "FileRecord": {
        "detection_tasks": "DetectionTask"
    },
    "DetectionTask": {
        "user": "User",
        "file_record": "FileRecord"
    },
    "PublishedService": {
        "user": "User",
        "service_tokens": "ServiceToken",
        "service_calls": "ServiceCall",
        "service_stats": "ServiceStats"
    },
    "ServiceToken": {
        "service": "PublishedService"
    },
    "ServiceCall": {
        "service": "PublishedService",
        "token": "ServiceToken"
    },
    "ServiceStats": {
        "service": "PublishedService"
    }
}

# 模型字段映射（用于API序列化）
MODEL_FIELDS = {
    "User": {
        "public": ["id", "username", "email", "full_name", "avatar_url", "bio", "is_active", "created_at"],
        "private": ["password_hash", "api_key_hash", "preferences", "is_superuser", "is_verified"],
        "admin": ["last_login_at", "updated_at"]
    },
    "FileRecord": {
        "public": ["id", "filename", "file_type", "file_size", "width", "height", "duration", "uploaded_at"],
        "private": ["stored_filename", "file_path", "file_hash", "access_token"],
        "admin": ["checksum", "format_info", "accessed_at", "expires_at"]
    },
    "DetectionTask": {
        "public": ["id", "task_name", "description", "detection_type", "status", "progress", "created_at"],
        "private": ["model_name", "confidence_threshold", "result_summary", "processing_time"],
        "admin": ["result_data", "error_message", "memory_usage", "gpu_usage"]
    }
}

def get_model_by_name(model_name: str):
    """根据名称获取模型类"""
    model_map = {
        "User": User,
        "FileRecord": FileRecord,
        "DetectionTask": DetectionTask
    }
    return model_map.get(model_name)

def get_enum_by_name(enum_name: str):
    """根据名称获取枚举类"""
    return ENUMS.get(enum_name)

def get_model_fields(model_name: str, field_type: str = "public"):
    """获取模型字段列表"""
    return MODEL_FIELDS.get(model_name, {}).get(field_type, [])

def get_all_models():
    """获取所有模型类"""
    return MODELS

def get_model_relationships(model_name: str):
    """获取模型关系"""
    return MODEL_RELATIONSHIPS.get(model_name, {})