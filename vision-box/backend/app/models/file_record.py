#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件记录模型
"""

from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text, Enum
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid
import enum


class FileType(str, enum.Enum):
    """文件类型枚举"""
    IMAGE = "image"
    VIDEO = "video"


class FileRecord(Base):
    """文件记录模型"""
    
    __tablename__ = "file_records"
    
    # 主键
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    
    # 文件信息
    filename = Column(String(255), nullable=False, comment="原始文件名")
    stored_filename = Column(String(255), nullable=False, comment="存储文件名")
    file_path = Column(String(500), nullable=False, comment="文件路径")
    file_type = Column(Enum(FileType), nullable=False, comment="文件类型")
    file_size = Column(Integer, nullable=False, comment="文件大小(字节)")
    mime_type = Column(String(100), nullable=False, comment="MIME类型")
    
    # 文件哈希和校验
    file_hash = Column(String(64), nullable=True, comment="文件SHA256哈希")
    checksum = Column(String(32), nullable=True, comment="文件MD5校验和")
    
    # 媒体信息（图片/视频）
    width = Column(Integer, nullable=True, comment="宽度")
    height = Column(Integer, nullable=True, comment="高度")
    duration = Column(Integer, nullable=True, comment="视频时长(秒)")
    fps = Column(Integer, nullable=True, comment="视频帧率")
    format_info = Column(Text, nullable=True, comment="格式详细信息(JSON)")
    
    # 访问控制
    is_public = Column(String(10), default="false", comment="是否公开")
    access_token = Column(String(255), nullable=True, comment="访问令牌")
    
    # 时间戳
    uploaded_at = Column(DateTime, default=datetime.utcnow, comment="上传时间")
    accessed_at = Column(DateTime, nullable=True, comment="最后访问时间")
    expires_at = Column(DateTime, nullable=True, comment="过期时间")
    
    # 关系
    detection_tasks = relationship("DetectionTask", back_populates="file_record", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<FileRecord(id={self.id}, filename={self.filename}, type={self.file_type})>"
    
    def to_dict(self, include_sensitive=False):
        """转换为字典"""
        data = {
            "id": self.id,
            "filename": self.filename,
            "file_type": self.file_type.value,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "width": self.width,
            "height": self.height,
            "duration": self.duration,
            "fps": self.fps,
            "is_public": self.is_public == "true",
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None,
            "accessed_at": self.accessed_at.isoformat() if self.accessed_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None
        }
        
        if include_sensitive:
            data.update({
                "stored_filename": self.stored_filename,
                "file_path": self.file_path,
                "file_hash": self.file_hash,
                "checksum": self.checksum,
                "format_info": self.format_info,
                "access_token": self.access_token
            })
        
        return data
    
    @property
    def is_image(self) -> bool:
        """是否为图片"""
        return self.file_type == FileType.IMAGE
    
    @property
    def is_video(self) -> bool:
        """是否为视频"""
        return self.file_type == FileType.VIDEO
    
    @property
    def file_extension(self) -> str:
        """获取文件扩展名"""
        return self.filename.split('.')[-1].lower() if '.' in self.filename else ''
    
    @property
    def file_size_mb(self) -> float:
        """获取文件大小(MB)"""
        return round(self.file_size / (1024 * 1024), 2)
    
    @property
    def aspect_ratio(self) -> float:
        """获取宽高比"""
        if self.width and self.height:
            return round(self.width / self.height, 2)
        return 0.0
    
    def update_access_time(self):
        """更新访问时间"""
        self.accessed_at = datetime.utcnow()
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.expires_at:
            return datetime.utcnow() > self.expires_at
        return False
    
    def set_expiry(self, hours: int = 24):
        """设置过期时间"""
        from datetime import timedelta
        self.expires_at = datetime.utcnow() + timedelta(hours=hours)
    
    def generate_access_url(self, base_url: str = "") -> str:
        """生成访问URL"""
        if self.is_public == "true":
            return f"{base_url}/uploads/{self.stored_filename}"
        elif self.access_token:
            return f"{base_url}/files/{self.id}?token={self.access_token}"
        else:
            return f"{base_url}/files/{self.id}"
    
    def get_thumbnail_path(self) -> str:
        """获取缩略图路径"""
        if self.is_image:
            name, ext = self.stored_filename.rsplit('.', 1)
            return f"{name}_thumb.{ext}"
        elif self.is_video:
            name, _ = self.stored_filename.rsplit('.', 1)
            return f"{name}_thumb.jpg"
        return ""
    
    def validate_file_integrity(self, current_hash: str) -> bool:
        """验证文件完整性"""
        return self.file_hash == current_hash if self.file_hash else True
    
    @classmethod
    def get_supported_extensions(cls) -> dict:
        """获取支持的文件扩展名"""
        return {
            "image": ["jpg", "jpeg", "png", "bmp", "gif", "webp"],
            "video": ["mp4", "avi", "mov", "mkv", "wmv", "flv", "webm"]
        }
    
    @classmethod
    def is_supported_format(cls, filename: str) -> bool:
        """检查是否为支持的格式"""
        ext = filename.split('.')[-1].lower() if '.' in filename else ''
        supported = cls.get_supported_extensions()
        return ext in supported["image"] or ext in supported["video"]
    
    @classmethod
    def get_file_type_from_extension(cls, filename: str) -> FileType:
        """根据扩展名获取文件类型"""
        ext = filename.split('.')[-1].lower() if '.' in filename else ''
        supported = cls.get_supported_extensions()
        
        if ext in supported["image"]:
            return FileType.IMAGE
        elif ext in supported["video"]:
            return FileType.VIDEO
        else:
            raise ValueError(f"不支持的文件格式: {ext}")