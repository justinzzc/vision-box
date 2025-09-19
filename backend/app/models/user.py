#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户模型
"""

from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid


class User(Base):
    """用户模型"""
    
    __tablename__ = "users"
    
    # 主键
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    
    # 基本信息
    username = Column(String(50), unique=True, index=True, nullable=False, comment="用户名")
    email = Column(String(100), unique=True, index=True, nullable=False, comment="邮箱")
    password_hash = Column(String(255), nullable=False, comment="密码哈希")
    
    # 用户状态
    is_active = Column(Boolean, default=True, comment="是否激活")
    is_superuser = Column(Boolean, default=False, comment="是否超级用户")
    is_verified = Column(Boolean, default=False, comment="是否已验证邮箱")
    
    # 个人信息
    full_name = Column(String(100), nullable=True, comment="全名")
    avatar_url = Column(String(500), nullable=True, comment="头像URL")
    bio = Column(Text, nullable=True, comment="个人简介")
    
    # 设置信息
    preferences = Column(Text, nullable=True, comment="用户偏好设置(JSON)")
    api_key_hash = Column(String(255), nullable=True, comment="API密钥哈希")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    last_login_at = Column(DateTime, nullable=True, comment="最后登录时间")
    
    # 关系
    detection_tasks = relationship("DetectionTask", back_populates="user", cascade="all, delete-orphan")
    published_services = relationship("PublishedService", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"
    
    def to_dict(self, include_sensitive=False):
        """转换为字典"""
        data = {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "is_active": self.is_active,
            "is_superuser": self.is_superuser,
            "is_verified": self.is_verified,
            "full_name": self.full_name,
            "avatar_url": self.avatar_url,
            "bio": self.bio,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None
        }
        
        if include_sensitive:
            data.update({
                "preferences": self.preferences,
                "api_key_hash": self.api_key_hash
            })
        
        return data
    
    @property
    def is_admin(self):
        """是否为管理员"""
        return self.is_superuser
    
    def check_permission(self, permission: str) -> bool:
        """检查权限"""
        # 超级用户拥有所有权限
        if self.is_superuser:
            return True
        
        # 这里可以扩展更复杂的权限系统
        basic_permissions = [
            "upload_file",
            "create_detection_task",
            "view_own_tasks",
            "download_results"
        ]
        
        return permission in basic_permissions
    
    def update_last_login(self):
        """更新最后登录时间"""
        self.last_login_at = datetime.utcnow()
    
    def deactivate(self):
        """停用用户"""
        self.is_active = False
        self.updated_at = datetime.utcnow()
    
    def activate(self):
        """激活用户"""
        self.is_active = True
        self.updated_at = datetime.utcnow()