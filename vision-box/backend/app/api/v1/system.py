#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统管理API接口
"""

import os
import psutil
import platform
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel

from app.core.database import get_db, engine
from app.core.config import get_settings
from app.models import User, DetectionTask, FileRecord, TaskStatus
from app.api.v1.auth import get_current_admin_user

settings = get_settings()
router = APIRouter()


# Pydantic模型
class SystemInfo(BaseModel):
    """系统信息模型"""
    system: Dict[str, Any]
    hardware: Dict[str, Any]
    application: Dict[str, Any]
    database: Dict[str, Any]


class SystemStats(BaseModel):
    """系统统计模型"""
    users: Dict[str, int]
    tasks: Dict[str, int]
    files: Dict[str, Any]
    storage: Dict[str, Any]
    performance: Dict[str, Any]


class HealthCheck(BaseModel):
    """健康检查模型"""
    status: str
    timestamp: datetime
    services: Dict[str, Dict[str, Any]]
    overall_health: str


class LogEntry(BaseModel):
    """日志条目模型"""
    timestamp: datetime
    level: str
    message: str
    source: str
    details: Optional[Dict[str, Any]]


class SystemConfig(BaseModel):
    """系统配置模型"""
    app_name: str
    version: str
    environment: str
    debug_mode: bool
    max_file_size: int
    max_batch_upload: int
    supported_formats: Dict[str, List[str]]


# 工具函数
def get_system_info() -> Dict[str, Any]:
    """获取系统信息"""
    return {
        "platform": platform.platform(),
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
        "hostname": platform.node()
    }


def get_hardware_info() -> Dict[str, Any]:
    """获取硬件信息"""
    try:
        # CPU信息
        cpu_info = {
            "physical_cores": psutil.cpu_count(logical=False),
            "logical_cores": psutil.cpu_count(logical=True),
            "cpu_usage_percent": psutil.cpu_percent(interval=1),
            "cpu_freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
        }
        
        # 内存信息
        memory = psutil.virtual_memory()
        memory_info = {
            "total_gb": round(memory.total / (1024**3), 2),
            "available_gb": round(memory.available / (1024**3), 2),
            "used_gb": round(memory.used / (1024**3), 2),
            "usage_percent": memory.percent
        }
        
        # 磁盘信息
        disk = psutil.disk_usage('/')
        disk_info = {
            "total_gb": round(disk.total / (1024**3), 2),
            "used_gb": round(disk.used / (1024**3), 2),
            "free_gb": round(disk.free / (1024**3), 2),
            "usage_percent": round((disk.used / disk.total) * 100, 2)
        }
        
        return {
            "cpu": cpu_info,
            "memory": memory_info,
            "disk": disk_info
        }
    except Exception as e:
        return {"error": f"获取硬件信息失败: {str(e)}"}


def get_application_info() -> Dict[str, Any]:
    """获取应用信息"""
    return {
        "name": settings.PROJECT_NAME,
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "debug_mode": settings.DEBUG,
        "api_version": settings.API_V1_STR,
        "database_url": settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else settings.DATABASE_URL,
        "upload_directory": settings.UPLOAD_DIR,
        "max_file_size_mb": settings.MAX_FILE_SIZE,
        "cors_origins": settings.BACKEND_CORS_ORIGINS
    }


def get_database_info(db: Session) -> Dict[str, Any]:
    """获取数据库信息"""
    try:
        # 数据库连接测试
        db.execute(text("SELECT 1"))
        connection_status = "connected"
        
        # 表统计
        table_stats = {}
        table_stats["users"] = db.query(User).count()
        table_stats["detection_tasks"] = db.query(DetectionTask).count()
        table_stats["file_records"] = db.query(FileRecord).count()
        
        # 数据库大小（SQLite）
        db_size = 0
        if settings.DATABASE_URL.startswith("sqlite"):
            db_path = settings.DATABASE_URL.replace("sqlite:///", "")
            if os.path.exists(db_path):
                db_size = os.path.getsize(db_path)
        
        return {
            "connection_status": connection_status,
            "database_type": "sqlite" if "sqlite" in settings.DATABASE_URL else "other",
            "database_size_mb": round(db_size / (1024**2), 2),
            "table_counts": table_stats
        }
    except Exception as e:
        return {
            "connection_status": "error",
            "error": str(e)
        }


def check_service_health(service_name: str) -> Dict[str, Any]:
    """检查服务健康状态"""
    try:
        if service_name == "database":
            # 数据库健康检查
            from app.core.database import SessionLocal
            db = SessionLocal()
            db.execute(text("SELECT 1"))
            db.close()
            return {"status": "healthy", "message": "数据库连接正常"}
        
        elif service_name == "storage":
            # 存储健康检查
            if os.path.exists(settings.UPLOAD_DIR) and os.access(settings.UPLOAD_DIR, os.W_OK):
                return {"status": "healthy", "message": "存储目录可访问"}
            else:
                return {"status": "unhealthy", "message": "存储目录不可访问"}
        
        elif service_name == "memory":
            # 内存健康检查
            memory = psutil.virtual_memory()
            if memory.percent < 90:
                return {"status": "healthy", "message": f"内存使用率: {memory.percent}%"}
            else:
                return {"status": "warning", "message": f"内存使用率过高: {memory.percent}%"}
        
        elif service_name == "disk":
            # 磁盘健康检查
            disk = psutil.disk_usage('/')
            usage_percent = (disk.used / disk.total) * 100
            if usage_percent < 85:
                return {"status": "healthy", "message": f"磁盘使用率: {usage_percent:.1f}%"}
            else:
                return {"status": "warning", "message": f"磁盘使用率过高: {usage_percent:.1f}%"}
        
        else:
            return {"status": "unknown", "message": "未知服务"}
    
    except Exception as e:
        return {"status": "error", "message": str(e)}


# API端点
@router.get("/info", response_model=SystemInfo)
async def get_system_information(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """获取系统信息"""
    return SystemInfo(
        system=get_system_info(),
        hardware=get_hardware_info(),
        application=get_application_info(),
        database=get_database_info(db)
    )


@router.get("/stats", response_model=SystemStats)
async def get_system_statistics(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """获取系统统计信息"""
    # 用户统计
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    verified_users = db.query(User).filter(User.is_verified == True).count()
    
    # 任务统计
    total_tasks = db.query(DetectionTask).count()
    completed_tasks = db.query(DetectionTask).filter(DetectionTask.status == TaskStatus.COMPLETED).count()
    failed_tasks = db.query(DetectionTask).filter(DetectionTask.status == TaskStatus.FAILED).count()
    running_tasks = db.query(DetectionTask).filter(DetectionTask.status == TaskStatus.PROCESSING).count()
    
    # 文件统计
    total_files = db.query(FileRecord).count()
    total_images = db.query(FileRecord).filter(FileRecord.file_type == "image").count()
    total_videos = db.query(FileRecord).filter(FileRecord.file_type == "video").count()
    
    # 存储统计
    total_storage_result = db.query(db.func.sum(FileRecord.file_size)).scalar()
    total_storage_bytes = total_storage_result or 0
    
    # 性能统计
    cpu_usage = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    return SystemStats(
        users={
            "total": total_users,
            "active": active_users,
            "verified": verified_users
        },
        tasks={
            "total": total_tasks,
            "completed": completed_tasks,
            "failed": failed_tasks,
            "running": running_tasks
        },
        files={
            "total": total_files,
            "images": total_images,
            "videos": total_videos
        },
        storage={
            "total_bytes": total_storage_bytes,
            "total_mb": round(total_storage_bytes / (1024**2), 2),
            "total_gb": round(total_storage_bytes / (1024**3), 2)
        },
        performance={
            "cpu_usage_percent": cpu_usage,
            "memory_usage_percent": memory.percent,
            "disk_usage_percent": round((disk.used / disk.total) * 100, 2)
        }
    )


@router.get("/health", response_model=HealthCheck)
async def health_check(
    current_user: User = Depends(get_current_admin_user)
):
    """系统健康检查"""
    services = {
        "database": check_service_health("database"),
        "storage": check_service_health("storage"),
        "memory": check_service_health("memory"),
        "disk": check_service_health("disk")
    }
    
    # 计算整体健康状态
    unhealthy_services = [name for name, info in services.items() if info["status"] in ["error", "unhealthy"]]
    warning_services = [name for name, info in services.items() if info["status"] == "warning"]
    
    if unhealthy_services:
        overall_health = "unhealthy"
    elif warning_services:
        overall_health = "warning"
    else:
        overall_health = "healthy"
    
    return HealthCheck(
        status="ok",
        timestamp=datetime.utcnow(),
        services=services,
        overall_health=overall_health
    )


@router.get("/config", response_model=SystemConfig)
async def get_system_config(
    current_user: User = Depends(get_current_admin_user)
):
    """获取系统配置"""
    from app.models import FileRecord
    
    return SystemConfig(
        app_name=settings.PROJECT_NAME,
        version="1.0.0",
        environment=settings.ENVIRONMENT,
        debug_mode=settings.DEBUG,
        max_file_size=settings.MAX_FILE_SIZE,
        max_batch_upload=settings.MAX_BATCH_UPLOAD,
        supported_formats=FileRecord.get_supported_extensions()
    )


@router.get("/logs")
async def get_system_logs(
    level: Optional[str] = Query(None, description="日志级别过滤"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量限制"),
    current_user: User = Depends(get_current_admin_user)
):
    """获取系统日志"""
    # 这里应该实现真实的日志读取逻辑
    # 为了演示，我们返回模拟的日志数据
    
    sample_logs = [
        LogEntry(
            timestamp=datetime.utcnow() - timedelta(minutes=5),
            level="INFO",
            message="系统启动完成",
            source="system",
            details={"startup_time": "2.3s"}
        ),
        LogEntry(
            timestamp=datetime.utcnow() - timedelta(minutes=10),
            level="INFO",
            message="数据库连接成功",
            source="database",
            details={"connection_pool": "active"}
        ),
        LogEntry(
            timestamp=datetime.utcnow() - timedelta(minutes=15),
            level="WARNING",
            message="内存使用率较高",
            source="monitor",
            details={"memory_usage": "78%"}
        )
    ]
    
    # 级别过滤
    if level:
        sample_logs = [log for log in sample_logs if log.level.lower() == level.lower()]
    
    # 限制数量
    sample_logs = sample_logs[:limit]
    
    return {
        "logs": [log.dict() for log in sample_logs],
        "total": len(sample_logs),
        "filtered_by_level": level
    }


@router.post("/maintenance/cleanup")
async def cleanup_system(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """系统清理"""
    cleanup_results = {
        "deleted_files": 0,
        "cleaned_tasks": 0,
        "freed_space_mb": 0,
        "errors": []
    }
    
    try:
        # 清理过期的失败任务
        expired_date = datetime.utcnow() - timedelta(days=7)
        expired_tasks = db.query(DetectionTask).filter(
            DetectionTask.status == TaskStatus.FAILED,
            DetectionTask.created_at < expired_date
        ).all()
        
        for task in expired_tasks:
            # 删除相关文件
            if task.output_file_path and os.path.exists(task.output_file_path):
                file_size = os.path.getsize(task.output_file_path)
                os.remove(task.output_file_path)
                cleanup_results["freed_space_mb"] += file_size / (1024**2)
                cleanup_results["deleted_files"] += 1
            
            if task.visualization_path and os.path.exists(task.visualization_path):
                file_size = os.path.getsize(task.visualization_path)
                os.remove(task.visualization_path)
                cleanup_results["freed_space_mb"] += file_size / (1024**2)
                cleanup_results["deleted_files"] += 1
            
            # 删除任务记录
            db.delete(task)
            cleanup_results["cleaned_tasks"] += 1
        
        db.commit()
        cleanup_results["freed_space_mb"] = round(cleanup_results["freed_space_mb"], 2)
        
    except Exception as e:
        cleanup_results["errors"].append(str(e))
        db.rollback()
    
    return {
        "message": "系统清理完成",
        "results": cleanup_results
    }


@router.post("/maintenance/backup")
async def backup_system(
    current_user: User = Depends(get_current_admin_user)
):
    """系统备份"""
    # 这里应该实现真实的备份逻辑
    # 为了演示，我们只返回备份信息
    
    backup_info = {
        "backup_id": f"backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
        "timestamp": datetime.utcnow(),
        "status": "completed",
        "size_mb": 125.6,
        "includes": ["database", "uploaded_files", "configuration"]
    }
    
    return {
        "message": "系统备份完成",
        "backup_info": backup_info
    }


@router.get("/monitoring/metrics")
async def get_monitoring_metrics(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """获取监控指标"""
    # 获取最近24小时的任务统计
    last_24h = datetime.utcnow() - timedelta(hours=24)
    
    recent_tasks = db.query(DetectionTask).filter(
        DetectionTask.created_at >= last_24h
    ).count()
    
    recent_completed = db.query(DetectionTask).filter(
        DetectionTask.created_at >= last_24h,
        DetectionTask.status == TaskStatus.COMPLETED
    ).count()
    
    # 系统资源使用情况
    cpu_usage = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # 计算平均处理时间
    avg_processing_time = db.query(db.func.avg(DetectionTask.processing_time)).filter(
        DetectionTask.status == TaskStatus.COMPLETED,
        DetectionTask.processing_time.isnot(None)
    ).scalar()
    
    return {
        "timestamp": datetime.utcnow(),
        "tasks": {
            "recent_24h": recent_tasks,
            "completed_24h": recent_completed,
            "success_rate_24h": round((recent_completed / recent_tasks * 100), 2) if recent_tasks > 0 else 0
        },
        "performance": {
            "cpu_usage_percent": cpu_usage,
            "memory_usage_percent": memory.percent,
            "disk_usage_percent": round((disk.used / disk.total) * 100, 2),
            "average_processing_time_seconds": round(float(avg_processing_time), 2) if avg_processing_time else 0
        },
        "resources": {
            "available_memory_gb": round(memory.available / (1024**3), 2),
            "free_disk_gb": round(disk.free / (1024**3), 2)
        }
    }