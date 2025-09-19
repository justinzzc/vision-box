#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
服务统计模型
"""

from datetime import datetime, date
from sqlalchemy import Column, String, Integer, Float, DateTime, Date, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid
import json


class ServiceStats(Base):
    """服务统计模型"""
    
    __tablename__ = "service_stats"
    
    # 主键
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    
    # 外键关系
    service_id = Column(String(36), ForeignKey("published_services.id"), nullable=False, comment="服务ID")
    
    # 统计维度
    stats_date = Column(Date, nullable=False, comment="统计日期")
    stats_hour = Column(Integer, nullable=True, comment="统计小时(0-23)")
    stats_type = Column(String(20), default="daily", comment="统计类型(hourly/daily/monthly)")
    
    # 调用统计
    total_calls = Column(Integer, default=0, comment="总调用次数")
    successful_calls = Column(Integer, default=0, comment="成功调用次数")
    failed_calls = Column(Integer, default=0, comment="失败调用次数")
    
    # 响应时间统计
    avg_response_time = Column(Float, default=0.0, comment="平均响应时间(秒)")
    min_response_time = Column(Float, nullable=True, comment="最小响应时间(秒)")
    max_response_time = Column(Float, nullable=True, comment="最大响应时间(秒)")
    
    # 文件统计
    total_files_processed = Column(Integer, default=0, comment="处理文件总数")
    total_file_size = Column(String(20), default="0", comment="文件总大小(字节)")
    avg_file_size = Column(Float, default=0.0, comment="平均文件大小(字节)")
    
    # 检测结果统计
    total_detections = Column(Integer, default=0, comment="检测到的对象总数")
    avg_detections_per_call = Column(Float, default=0.0, comment="平均每次调用检测数量")
    
    # 资源使用统计
    avg_memory_usage = Column(Float, default=0.0, comment="平均内存使用(MB)")
    max_memory_usage = Column(Float, default=0.0, comment="最大内存使用(MB)")
    avg_cpu_usage = Column(Float, default=0.0, comment="平均CPU使用率")
    avg_gpu_usage = Column(Float, default=0.0, comment="平均GPU使用率")
    
    # 错误统计
    error_breakdown = Column(Text, nullable=True, comment="错误分类统计(JSON)")
    status_code_breakdown = Column(Text, nullable=True, comment="状态码分布(JSON)")
    
    # 客户端统计
    unique_ips = Column(Integer, default=0, comment="唯一IP数量")
    unique_tokens = Column(Integer, default=0, comment="使用的令牌数量")
    top_user_agents = Column(Text, nullable=True, comment="主要用户代理(JSON)")
    
    # 文件类型统计
    file_type_breakdown = Column(Text, nullable=True, comment="文件类型分布(JSON)")
    model_usage_breakdown = Column(Text, nullable=True, comment="模型使用分布(JSON)")
    
    # 逻辑删除标记
    is_delete = Column(Boolean, default=False, comment="是否已删除")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    deleted_at = Column(DateTime, nullable=True, comment="删除时间")
    
    # 关系
    service = relationship("PublishedService", back_populates="service_stats")
    
    def __repr__(self):
        return f"<ServiceStats(id={self.id}, service_id={self.service_id}, date={self.stats_date})>"
    
    def to_dict(self, include_sensitive=False):
        """转换为字典"""
        data = {
            "id": self.id,
            "service_id": self.service_id,
            "stats_date": self.stats_date.isoformat() if self.stats_date else None,
            "stats_hour": self.stats_hour,
            "stats_type": self.stats_type,
            "total_calls": self.total_calls,
            "successful_calls": self.successful_calls,
            "failed_calls": self.failed_calls,
            "success_rate": self.success_rate,
            "avg_response_time": self.avg_response_time,
            "min_response_time": self.min_response_time,
            "max_response_time": self.max_response_time,
            "total_files_processed": self.total_files_processed,
            "total_file_size": self.total_file_size,
            "avg_file_size": self.avg_file_size,
            "total_detections": self.total_detections,
            "avg_detections_per_call": self.avg_detections_per_call,
            "avg_memory_usage": self.avg_memory_usage,
            "max_memory_usage": self.max_memory_usage,
            "avg_cpu_usage": self.avg_cpu_usage,
            "avg_gpu_usage": self.avg_gpu_usage,
            "unique_ips": self.unique_ips,
            "unique_tokens": self.unique_tokens,
            "error_breakdown": self.get_error_breakdown(),
            "status_code_breakdown": self.get_status_code_breakdown(),
            "file_type_breakdown": self.get_file_type_breakdown(),
            "model_usage_breakdown": self.get_model_usage_breakdown(),
            "top_user_agents": self.get_top_user_agents(),
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
    def get_error_breakdown(self) -> dict:
        """获取错误分类统计"""
        return json.loads(self.error_breakdown) if self.error_breakdown else {}
    
    def set_error_breakdown(self, breakdown: dict):
        """设置错误分类统计"""
        self.error_breakdown = json.dumps(breakdown, ensure_ascii=False)
    
    def get_status_code_breakdown(self) -> dict:
        """获取状态码分布"""
        return json.loads(self.status_code_breakdown) if self.status_code_breakdown else {}
    
    def set_status_code_breakdown(self, breakdown: dict):
        """设置状态码分布"""
        self.status_code_breakdown = json.dumps(breakdown, ensure_ascii=False)
    
    def get_file_type_breakdown(self) -> dict:
        """获取文件类型分布"""
        return json.loads(self.file_type_breakdown) if self.file_type_breakdown else {}
    
    def set_file_type_breakdown(self, breakdown: dict):
        """设置文件类型分布"""
        self.file_type_breakdown = json.dumps(breakdown, ensure_ascii=False)
    
    def get_model_usage_breakdown(self) -> dict:
        """获取模型使用分布"""
        return json.loads(self.model_usage_breakdown) if self.model_usage_breakdown else {}
    
    def set_model_usage_breakdown(self, breakdown: dict):
        """设置模型使用分布"""
        self.model_usage_breakdown = json.dumps(breakdown, ensure_ascii=False)
    
    def get_top_user_agents(self) -> list:
        """获取主要用户代理"""
        return json.loads(self.top_user_agents) if self.top_user_agents else []
    
    def set_top_user_agents(self, agents: list):
        """设置主要用户代理"""
        self.top_user_agents = json.dumps(agents, ensure_ascii=False)
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_calls == 0:
            return 0.0
        return (self.successful_calls / self.total_calls) * 100
    
    @property
    def failure_rate(self) -> float:
        """失败率"""
        if self.total_calls == 0:
            return 0.0
        return (self.failed_calls / self.total_calls) * 100
    
    def update_stats(self, call_data: dict):
        """更新统计数据"""
        # 更新调用统计
        self.total_calls += 1
        if call_data.get('success', False):
            self.successful_calls += 1
        else:
            self.failed_calls += 1
        
        # 更新响应时间统计
        response_time = call_data.get('processing_time', 0)
        if response_time > 0:
            if self.min_response_time is None or response_time < self.min_response_time:
                self.min_response_time = response_time
            if self.max_response_time is None or response_time > self.max_response_time:
                self.max_response_time = response_time
            
            # 计算平均响应时间
            total_time = self.avg_response_time * (self.total_calls - 1) + response_time
            self.avg_response_time = total_time / self.total_calls
        
        # 更新文件统计
        file_size = call_data.get('file_size', 0)
        if file_size > 0:
            self.total_files_processed += 1
            try:
                current_total_size = int(self.total_file_size)
                self.total_file_size = str(current_total_size + file_size)
                self.avg_file_size = (current_total_size + file_size) / self.total_files_processed
            except (ValueError, TypeError):
                self.total_file_size = str(file_size)
                self.avg_file_size = file_size
        
        # 更新检测统计
        detection_count = call_data.get('detection_count', 0)
        if detection_count > 0:
            self.total_detections += detection_count
            self.avg_detections_per_call = self.total_detections / self.total_calls
        
        # 更新资源使用统计
        memory_usage = call_data.get('memory_usage', 0)
        if memory_usage > 0:
            total_memory = self.avg_memory_usage * (self.total_calls - 1) + memory_usage
            self.avg_memory_usage = total_memory / self.total_calls
            if memory_usage > self.max_memory_usage:
                self.max_memory_usage = memory_usage
        
        cpu_usage = call_data.get('cpu_usage', 0)
        if cpu_usage > 0:
            total_cpu = self.avg_cpu_usage * (self.total_calls - 1) + cpu_usage
            self.avg_cpu_usage = total_cpu / self.total_calls
        
        gpu_usage = call_data.get('gpu_usage', 0)
        if gpu_usage > 0:
            total_gpu = self.avg_gpu_usage * (self.total_calls - 1) + gpu_usage
            self.avg_gpu_usage = total_gpu / self.total_calls
        
        self.updated_at = datetime.utcnow()
    
    def soft_delete(self):
        """逻辑删除统计记录"""
        self.is_delete = True
        self.deleted_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    @classmethod
    def create_daily_stats(cls, service_id: str, stats_date: date):
        """创建日统计记录"""
        return cls(
            service_id=service_id,
            stats_date=stats_date,
            stats_type="daily"
        )
    
    @classmethod
    def create_hourly_stats(cls, service_id: str, stats_date: date, hour: int):
        """创建小时统计记录"""
        return cls(
            service_id=service_id,
            stats_date=stats_date,
            stats_hour=hour,
            stats_type="hourly"
        )