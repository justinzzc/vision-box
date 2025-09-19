#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
发布服务模型
"""

from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid
import json
import enum


class ServiceStatus(str, enum.Enum):
    """服务状态枚举"""
    ACTIVE = "active"        # 活跃
    DISABLED = "disabled"    # 禁用
    SUSPENDED = "suspended"  # 暂停
    DELETED = "deleted"      # 已删除


class PublishedService(Base):
    """发布服务模型"""
    
    __tablename__ = "published_services"
    
    # 主键
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    
    # 外键关系
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, comment="创建用户ID")
    
    # 服务基本信息
    service_name = Column(String(200), nullable=False, comment="服务名称")
    description = Column(Text, nullable=True, comment="服务描述")
    status = Column(String(20), default="active", comment="服务状态")
    
    # 检测配置
    model_name = Column(String(100), nullable=False, comment="使用的模型名称")
    confidence_threshold = Column(Float, default=0.5, comment="置信度阈值")
    detection_classes = Column(Text, nullable=True, comment="检测类别列表(JSON)")
    
    # API配置
    api_endpoint = Column(String(500), nullable=False, comment="API调用端点")
    rate_limit = Column(Integer, default=100, comment="调用频率限制(次/分钟)")
    max_file_size = Column(Integer, default=10485760, comment="最大文件大小(字节)")
    allowed_formats = Column(Text, nullable=True, comment="允许的文件格式(JSON)")
    
    # 统计信息
    total_calls = Column(Integer, default=0, comment="总调用次数")
    successful_calls = Column(Integer, default=0, comment="成功调用次数")
    failed_calls = Column(Integer, default=0, comment="失败调用次数")
    last_called_at = Column(DateTime, nullable=True, comment="最后调用时间")
    
    # 逻辑删除标记
    is_delete = Column(Boolean, default=False, comment="是否已删除")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    deleted_at = Column(DateTime, nullable=True, comment="删除时间")
    
    # 关系
    user = relationship("User", back_populates="published_services")
    service_tokens = relationship("ServiceToken", back_populates="service", cascade="all, delete-orphan")
    service_calls = relationship("ServiceCall", back_populates="service", cascade="all, delete-orphan")
    service_stats = relationship("ServiceStats", back_populates="service", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<PublishedService(id={self.id}, name={self.service_name}, status={self.status})>"
    
    def to_dict(self, include_sensitive=False):
        """转换为字典"""
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "service_name": self.service_name,
            "description": self.description,
            "status": self.status,
            "model_name": self.model_name,
            "confidence_threshold": self.confidence_threshold,
            "detection_classes": self.get_detection_classes(),
            "api_endpoint": self.api_endpoint,
            "rate_limit": self.rate_limit,
            "max_file_size": self.max_file_size,
            "allowed_formats": self.get_allowed_formats(),
            "total_calls": self.total_calls,
            "successful_calls": self.successful_calls,
            "failed_calls": self.failed_calls,
            "last_called_at": self.last_called_at.isoformat() if self.last_called_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_sensitive:
            data.update({
                "is_delete": self.is_delete,
                "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None
            })
        
        return data
    
    # JSON字段的getter和setter方法
    def get_detection_classes(self) -> list:
        """获取检测类别列表"""
        return json.loads(self.detection_classes) if self.detection_classes else []
    
    def set_detection_classes(self, classes: list):
        """设置检测类别列表"""
        self.detection_classes = json.dumps(classes, ensure_ascii=False)
    
    def get_allowed_formats(self) -> list:
        """获取允许的文件格式"""
        return json.loads(self.allowed_formats) if self.allowed_formats else ["jpg", "jpeg", "png", "mp4", "avi"]
    
    def set_allowed_formats(self, formats: list):
        """设置允许的文件格式"""
        self.allowed_formats = json.dumps(formats, ensure_ascii=False)
    
    # 状态管理方法
    def disable(self):
        """禁用服务"""
        self.status = "disabled"
        self.updated_at = datetime.utcnow()
    
    def enable(self):
        """启用服务"""
        self.status = "active"
        self.updated_at = datetime.utcnow()
    
    def soft_delete(self):
        """逻辑删除服务"""
        self.is_delete = True
        self.status = "deleted"
        self.deleted_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def restore(self):
        """恢复已删除的服务"""
        self.is_delete = False
        self.status = "active"
        self.deleted_at = None
        self.updated_at = datetime.utcnow()
    
    def increment_call_count(self, success: bool = True):
        """增加调用计数"""
        self.total_calls += 1
        if success:
            self.successful_calls += 1
        else:
            self.failed_calls += 1
        self.last_called_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_calls == 0:
            return 0.0
        return (self.successful_calls / self.total_calls) * 100
    
    @property
    def is_active(self) -> bool:
        """是否活跃"""
        return self.status == "active" and not self.is_delete