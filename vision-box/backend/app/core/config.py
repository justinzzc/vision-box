#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用配置模块
管理所有配置参数和环境变量
"""

import os
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import validator


class Settings(BaseSettings):
    """应用设置类"""
    
    # 基本配置
    PROJECT_NAME: str = "视觉检测应用"
    APP_NAME: str = "视觉检测应用"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # API配置
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_PREFIX: str = "/api"
    API_V1_STR: str = "/api/v1"
    
    # 数据库配置
    DATABASE_URL: str = "sqlite:///./data/vision_app.db"
    
    # 文件存储配置
    UPLOAD_DIR: str = "./data/uploads"
    RESULT_DIR: str = "./data/results"
    MODEL_DIR: str = "./data/models"
    
    # 文件上传限制
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
    SUPPORTED_IMAGE_FORMATS: List[str] = ["jpg", "jpeg", "png", "bmp", "gif"]
    SUPPORTED_VIDEO_FORMATS: List[str] = ["mp4", "avi", "mov", "mkv", "wmv"]
    
    # 检测配置
    DEFAULT_CONFIDENCE: float = 0.5
    DEFAULT_MODEL: str = "yolov8s"
    MAX_DETECTION_TIME: int = 300  # 5分钟
    
    # CORS配置
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080"
    ]
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080"
    ]
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: Optional[str] = None
    
    # 安全配置
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    EMAIL_RESET_TOKEN_EXPIRE_HOURS: int = 48
    
    @validator("CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v):
        """解析CORS源列表"""
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    @validator("DATABASE_URL", pre=True)
    def assemble_db_connection(cls, v):
        """确保数据库URL正确"""
        if v.startswith("sqlite"):
            # 确保SQLite数据库目录存在
            db_path = v.replace("sqlite:///", "")
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        return v
    
    @property
    def all_supported_formats(self) -> List[str]:
        """获取所有支持的文件格式"""
        return self.SUPPORTED_IMAGE_FORMATS + self.SUPPORTED_VIDEO_FORMATS
    
    @property
    def upload_path(self) -> Path:
        """上传目录路径"""
        path = Path(self.UPLOAD_DIR)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @property
    def result_path(self) -> Path:
        """结果目录路径"""
        path = Path(self.RESULT_DIR)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @property
    def model_path(self) -> Path:
        """模型目录路径"""
        path = Path(self.MODEL_DIR)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def is_image_format(self, filename: str) -> bool:
        """检查是否为图片格式"""
        ext = filename.lower().split('.')[-1]
        return ext in self.SUPPORTED_IMAGE_FORMATS
    
    def is_video_format(self, filename: str) -> bool:
        """检查是否为视频格式"""
        ext = filename.lower().split('.')[-1]
        return ext in self.SUPPORTED_VIDEO_FORMATS
    
    def is_supported_format(self, filename: str) -> bool:
        """检查是否为支持的格式"""
        return self.is_image_format(filename) or self.is_video_format(filename)
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 创建全局设置实例
settings = Settings()


# 开发环境配置
class DevelopmentSettings(Settings):
    """开发环境配置"""
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    CORS_ORIGINS: List[str] = ["*"]  # 开发环境允许所有源


# 生产环境配置
class ProductionSettings(Settings):
    """生产环境配置"""
    DEBUG: bool = False
    LOG_LEVEL: str = "WARNING"
    # 生产环境应该设置具体的CORS源


# 测试环境配置
class TestSettings(Settings):
    """测试环境配置"""
    DEBUG: bool = True
    DATABASE_URL: str = "sqlite:///./test.db"
    UPLOAD_DIR: str = "./test_uploads"
    RESULT_DIR: str = "./test_results"
    MODEL_DIR: str = "./test_models"


def get_settings() -> Settings:
    """根据环境变量获取相应的配置"""
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    if env == "production":
        return ProductionSettings()
    elif env == "test":
        return TestSettings()
    else:
        return DevelopmentSettings()


# 根据环境更新设置
if os.getenv("ENVIRONMENT"):
    settings = get_settings()