#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视觉检测应用后端服务
基于FastAPI + Supervision的目标检测API服务
"""

import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from loguru import logger
from dotenv import load_dotenv

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 加载环境变量
load_dotenv()

# 导入应用模块
from app.core.config import get_settings
from app.core.database import init_db
from app.api import api_router
from app.core.exceptions import setup_exception_handlers

settings = get_settings()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("启动 Vision Box 应用...")
    
    # 确保必要的目录存在
    directories = [
        settings.UPLOAD_DIR,
        os.path.join(settings.UPLOAD_DIR, "thumbnails"),
        os.path.join(settings.UPLOAD_DIR, "temp"),
        os.path.join(settings.UPLOAD_DIR, "outputs"),
        os.path.join(settings.UPLOAD_DIR, "visualizations")
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        logger.info(f"确保目录存在: {directory}")
    
    # 初始化数据库
    try:
        from app.core.database import init_db
        await init_db()
        logger.info("数据库初始化完成")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
    
    # 检查supervision库可用性
    try:
        from app.services import DetectionService
        detection_service = DetectionService()
        if detection_service.is_supervision_available():
            logger.info("Supervision库可用，支持真实检测")
        else:
            logger.warning("Supervision库不可用，将使用模拟检测")
    except Exception as e:
        logger.warning(f"检查supervision库时出错: {e}")
    
    yield
    
    # 关闭时执行
    logger.info("关闭 Vision Box 应用...")


# 创建FastAPI应用
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="基于supervision库的视觉检测应用",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# 设置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 设置异常处理
setup_exception_handlers(app)

# 注册API路由
app.include_router(api_router, prefix=settings.API_V1_STR)

# 静态文件服务
if os.path.exists(settings.UPLOAD_DIR):
    app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")
    logger.info(f"静态文件服务已启用: /uploads -> {settings.UPLOAD_DIR}")


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "Welcome to Vision Box API",
        "version": "1.0.0",
        "docs": "/docs",
        "api": settings.API_V1_STR,
        "features": {
            "file_upload": True,
            "image_detection": True,
            "video_detection": True,
            "result_visualization": True,
            "result_export": True
        }
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    from datetime import datetime
    
    # 检查数据库连接
    db_status = "healthy"
    try:
        from app.core.database import SessionLocal
        from sqlalchemy import text
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    # 检查上传目录
    upload_status = "healthy" if os.path.exists(settings.UPLOAD_DIR) else "unhealthy: upload directory not found"
    
    # 检查supervision库
    supervision_status = "unknown"
    try:
        from app.services import DetectionService
        detection_service = DetectionService()
        supervision_status = "available" if detection_service.is_supervision_available() else "unavailable"
    except Exception:
        supervision_status = "error"
    
    return {
        "status": "healthy" if db_status == "healthy" and upload_status == "healthy" else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "components": {
            "database": db_status,
            "upload_directory": upload_status,
            "supervision_library": supervision_status
        }
    }


@app.get("/info")
async def app_info():
    """应用信息"""
    return {
        "name": settings.PROJECT_NAME,
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
        "api_version": settings.API_V1_STR,
        "upload_limits": {
            "max_file_size_mb": settings.MAX_FILE_SIZE,
            "max_batch_upload": settings.MAX_BATCH_UPLOAD
        },
        "supported_formats": {
            "images": [".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp"],
            "videos": [".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm"]
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )