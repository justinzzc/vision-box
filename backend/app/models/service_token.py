#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
服务令牌模型
"""

from datetime import datetime, timedelta
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid
import secrets
import hashlib


class ServiceToken(Base):
    """服务令牌模型"""
    
    __tablename__ = "service_tokens"
    
    # 主键
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    
    # 外键关系
    service_id = Column(String(36), ForeignKey("published_services.id"), nullable=False, comment="服务ID")
    
    # 令牌信息
    token_name = Column(String(200), nullable=False, comment="令牌名称")
    token_hash = Column(String(255), nullable=False, unique=True, comment="令牌哈希值")
    token_prefix = Column(String(20), nullable=False, comment="令牌前缀(用于显示)")
    
    # 权限和限制
    permissions = Column(Text, nullable=True, comment="权限列表(JSON)")
    rate_limit_override = Column(String(50), nullable=True, comment="覆盖的频率限制")
    ip_whitelist = Column(Text, nullable=True, comment="IP白名单(JSON)")
    
    # 状态信息
    is_active = Column(Boolean, default=True, comment="是否激活")
    is_revoked = Column(Boolean, default=False, comment="是否已撤销")
    
    # 使用统计
    usage_count = Column(String(50), default="0", comment="使用次数")
    last_used_at = Column(DateTime, nullable=True, comment="最后使用时间")
    last_used_ip = Column(String(45), nullable=True, comment="最后使用IP")
    
    # 过期时间
    expires_at = Column(DateTime, nullable=True, comment="过期时间")
    
    # 逻辑删除标记
    is_delete = Column(Boolean, default=False, comment="是否已删除")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    deleted_at = Column(DateTime, nullable=True, comment="删除时间")
    
    # 关系
    service = relationship("PublishedService", back_populates="service_tokens")
    
    def __repr__(self):
        return f"<ServiceToken(id={self.id}, name={self.token_name}, service_id={self.service_id})>"
    
    def to_dict(self, include_sensitive=False):
        """转换为字典"""
        data = {
            "id": self.id,
            "service_id": self.service_id,
            "token_name": self.token_name,
            "token_prefix": self.token_prefix,
            "is_active": self.is_active,
            "is_revoked": self.is_revoked,
            "usage_count": self.usage_count,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "last_used_ip": self.last_used_ip,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_sensitive:
            data.update({
                "token_hash": self.token_hash,
                "permissions": self.permissions,
                "rate_limit_override": self.rate_limit_override,
                "ip_whitelist": self.ip_whitelist,
                "is_delete": self.is_delete,
                "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None
            })
        
        return data
    
    @classmethod
    def generate_token(cls, service_id: str, token_name: str, expires_hours: int = None) -> tuple:
        """生成新的令牌"""
        # 生成随机令牌
        token = f"st_{secrets.token_urlsafe(32)}"
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        token_prefix = token[:12] + "..."
        
        # 计算过期时间
        expires_at = None
        if expires_hours:
            expires_at = datetime.utcnow() + timedelta(hours=expires_hours)
        
        # 创建令牌实例
        service_token = cls(
            service_id=service_id,
            token_name=token_name,
            token_hash=token_hash,
            token_prefix=token_prefix,
            expires_at=expires_at
        )
        
        return service_token, token
    
    def verify_token(self, token: str) -> bool:
        """验证令牌"""
        if self.is_revoked or self.is_delete or not self.is_active:
            return False
        
        # 检查是否过期
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False
        
        # 验证令牌哈希
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        return token_hash == self.token_hash
    
    def revoke(self):
        """撤销令牌"""
        self.is_revoked = True
        self.is_active = False
        self.updated_at = datetime.utcnow()
    
    def activate(self):
        """激活令牌"""
        if not self.is_revoked and not self.is_delete:
            self.is_active = True
            self.updated_at = datetime.utcnow()
    
    def deactivate(self):
        """停用令牌"""
        self.is_active = False
        self.updated_at = datetime.utcnow()
    
    def soft_delete(self):
        """逻辑删除令牌"""
        self.is_delete = True
        self.is_active = False
        self.deleted_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def update_usage(self, ip_address: str = None):
        """更新使用统计"""
        try:
            current_count = int(self.usage_count)
            self.usage_count = str(current_count + 1)
        except (ValueError, TypeError):
            self.usage_count = "1"
        
        self.last_used_at = datetime.utcnow()
        if ip_address:
            self.last_used_ip = ip_address
        self.updated_at = datetime.utcnow()
    
    @property
    def is_expired(self) -> bool:
        """是否已过期"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_valid(self) -> bool:
        """是否有效"""
        return (
            self.is_active and 
            not self.is_revoked and 
            not self.is_delete and 
            not self.is_expired
        )
    
    @property
    def days_until_expiry(self) -> int:
        """距离过期的天数"""
        if not self.expires_at:
            return -1  # 永不过期
        
        delta = self.expires_at - datetime.utcnow()
        return max(0, delta.days)