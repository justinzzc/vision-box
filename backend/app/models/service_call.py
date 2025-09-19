#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
服务调用记录模型
"""

from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid
import json


class ServiceCall(Base):
    """服务调用记录模型"""
    
    __tablename__ = "service_calls"
    
    # 主键
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    
    # 外键关系
    service_id = Column(String(36), ForeignKey("published_services.id"), nullable=False, comment="服务ID")
    token_id = Column(String(36), ForeignKey("service_tokens.id"), nullable=True, comment="令牌ID")
    
    # 请求信息
    request_id = Column(String(100), nullable=False, comment="请求ID")
    client_ip = Column(String(45), nullable=True, comment="客户端IP")
    user_agent = Column(Text, nullable=True, comment="用户代理")
    referer = Column(String(500), nullable=True, comment="来源页面")
    
    # 请求参数
    http_method = Column(String(10), default="POST", comment="HTTP方法")
    request_path = Column(String(500), nullable=False, comment="请求路径")
    request_headers = Column(Text, nullable=True, comment="请求头(JSON)")
    request_params = Column(Text, nullable=True, comment="请求参数(JSON)")
    
    # 文件信息
    file_name = Column(String(255), nullable=True, comment="上传文件名")
    file_size = Column(Integer, nullable=True, comment="文件大小(字节)")
    file_type = Column(String(50), nullable=True, comment="文件类型")
    file_hash = Column(String(64), nullable=True, comment="文件哈希")
    
    # 响应信息
    status_code = Column(Integer, nullable=False, comment="HTTP状态码")
    response_size = Column(Integer, nullable=True, comment="响应大小(字节)")
    response_headers = Column(Text, nullable=True, comment="响应头(JSON)")
    
    # 处理信息
    processing_time = Column(Float, nullable=True, comment="处理时间(秒)")
    detection_count = Column(Integer, nullable=True, comment="检测到的对象数量")
    model_used = Column(String(100), nullable=True, comment="使用的模型")
    confidence_threshold = Column(Float, nullable=True, comment="置信度阈值")
    
    # 结果信息
    success = Column(Boolean, default=False, comment="是否成功")
    error_code = Column(String(50), nullable=True, comment="错误代码")
    error_message = Column(Text, nullable=True, comment="错误信息")
    
    # 统计信息
    memory_usage = Column(Float, nullable=True, comment="内存使用(MB)")
    cpu_usage = Column(Float, nullable=True, comment="CPU使用率")
    gpu_usage = Column(Float, nullable=True, comment="GPU使用率")
    
    # 回调信息
    callback_url = Column(String(500), nullable=True, comment="回调URL")
    callback_status = Column(String(20), nullable=True, comment="回调状态")
    callback_attempts = Column(Integer, default=0, comment="回调尝试次数")
    
    # 逻辑删除标记
    is_delete = Column(Boolean, default=False, comment="是否已删除")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    completed_at = Column(DateTime, nullable=True, comment="完成时间")
    deleted_at = Column(DateTime, nullable=True, comment="删除时间")
    
    # 关系
    service = relationship("PublishedService", back_populates="service_calls")
    token = relationship("ServiceToken")
    
    def __repr__(self):
        return f"<ServiceCall(id={self.id}, service_id={self.service_id}, status={self.status_code})>"
    
    def to_dict(self, include_sensitive=False):
        """转换为字典"""
        data = {
            "id": self.id,
            "service_id": self.service_id,
            "token_id": self.token_id,
            "request_id": self.request_id,
            "client_ip": self.client_ip,
            "http_method": self.http_method,
            "request_path": self.request_path,
            "file_name": self.file_name,
            "file_size": self.file_size,
            "file_type": self.file_type,
            "status_code": self.status_code,
            "response_size": self.response_size,
            "processing_time": self.processing_time,
            "detection_count": self.detection_count,
            "model_used": self.model_used,
            "confidence_threshold": self.confidence_threshold,
            "success": self.success,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "memory_usage": self.memory_usage,
            "cpu_usage": self.cpu_usage,
            "gpu_usage": self.gpu_usage,
            "callback_url": self.callback_url,
            "callback_status": self.callback_status,
            "callback_attempts": self.callback_attempts,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }
        
        if include_sensitive:
            data.update({
                "user_agent": self.user_agent,
                "referer": self.referer,
                "request_headers": self.get_request_headers(),
                "request_params": self.get_request_params(),
                "response_headers": self.get_response_headers(),
                "file_hash": self.file_hash,
                "is_delete": self.is_delete,
                "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None
            })
        
        return data
    
    # JSON字段的getter和setter方法
    def get_request_headers(self) -> dict:
        """获取请求头"""
        return json.loads(self.request_headers) if self.request_headers else {}
    
    def set_request_headers(self, headers: dict):
        """设置请求头"""
        self.request_headers = json.dumps(headers, ensure_ascii=False)
    
    def get_request_params(self) -> dict:
        """获取请求参数"""
        return json.loads(self.request_params) if self.request_params else {}
    
    def set_request_params(self, params: dict):
        """设置请求参数"""
        self.request_params = json.dumps(params, ensure_ascii=False)
    
    def get_response_headers(self) -> dict:
        """获取响应头"""
        return json.loads(self.response_headers) if self.response_headers else {}
    
    def set_response_headers(self, headers: dict):
        """设置响应头"""
        self.response_headers = json.dumps(headers, ensure_ascii=False)
    
    def complete_call(self, status_code: int, success: bool = True, 
                     detection_count: int = None, processing_time: float = None):
        """完成调用记录"""
        self.status_code = status_code
        self.success = success
        self.completed_at = datetime.utcnow()
        
        if detection_count is not None:
            self.detection_count = detection_count
        
        if processing_time is not None:
            self.processing_time = processing_time
    
    def set_error(self, error_code: str, error_message: str, status_code: int = 500):
        """设置错误信息"""
        self.success = False
        self.status_code = status_code
        self.error_code = error_code
        self.error_message = error_message
        self.completed_at = datetime.utcnow()
    
    def update_callback_status(self, status: str, increment_attempts: bool = True):
        """更新回调状态"""
        self.callback_status = status
        if increment_attempts:
            self.callback_attempts += 1
    
    def soft_delete(self):
        """逻辑删除调用记录"""
        self.is_delete = True
        self.deleted_at = datetime.utcnow()
    
    @property
    def duration_ms(self) -> float:
        """处理时长(毫秒)"""
        return self.processing_time * 1000 if self.processing_time else 0
    
    @property
    def is_successful(self) -> bool:
        """是否成功"""
        return self.success and 200 <= self.status_code < 300
    
    @property
    def response_time_category(self) -> str:
        """响应时间分类"""
        if not self.processing_time:
            return "unknown"
        
        if self.processing_time < 1.0:
            return "fast"  # < 1秒
        elif self.processing_time < 5.0:
            return "normal"  # 1-5秒
        elif self.processing_time < 10.0:
            return "slow"  # 5-10秒
        else:
            return "very_slow"  # > 10秒