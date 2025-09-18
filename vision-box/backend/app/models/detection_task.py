#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检测任务模型
"""

from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, Enum, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid
import enum
import json


class TaskStatus(str, enum.Enum):
    """任务状态枚举"""
    PENDING = "pending"      # 等待中
    PROCESSING = "processing" # 处理中
    COMPLETED = "completed"   # 已完成
    FAILED = "failed"        # 失败
    CANCELLED = "cancelled"   # 已取消


class DetectionType(str, enum.Enum):
    """检测类型枚举"""
    OBJECT_DETECTION = "object_detection"        # 目标检测
    INSTANCE_SEGMENTATION = "instance_segmentation" # 实例分割
    CLASSIFICATION = "classification"            # 分类
    POSE_ESTIMATION = "pose_estimation"          # 姿态估计
    FACE_DETECTION = "face_detection"            # 人脸检测
    CUSTOM = "custom"                           # 自定义


class DetectionTask(Base):
    """检测任务模型"""
    
    __tablename__ = "detection_tasks"
    
    # 主键
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    
    # 外键关系
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, comment="用户ID")
    file_record_id = Column(String(36), ForeignKey("file_records.id"), nullable=False, comment="文件记录ID")
    
    # 任务基本信息
    task_name = Column(String(200), nullable=False, comment="任务名称")
    description = Column(Text, nullable=True, comment="任务描述")
    detection_type = Column(Enum(DetectionType), nullable=False, comment="检测类型")
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING, comment="任务状态")
    
    # 检测配置
    model_name = Column(String(100), nullable=False, comment="使用的模型名称")
    model_version = Column(String(50), nullable=True, comment="模型版本")
    confidence_threshold = Column(Float, default=0.5, comment="置信度阈值")
    iou_threshold = Column(Float, default=0.5, comment="IoU阈值")
    max_detections = Column(Integer, default=100, comment="最大检测数量")
    
    # 检测参数（JSON格式存储）
    detection_params = Column(Text, nullable=True, comment="检测参数(JSON)")
    preprocessing_params = Column(Text, nullable=True, comment="预处理参数(JSON)")
    postprocessing_params = Column(Text, nullable=True, comment="后处理参数(JSON)")
    
    # 执行信息
    priority = Column(Integer, default=0, comment="任务优先级")
    retry_count = Column(Integer, default=0, comment="重试次数")
    max_retries = Column(Integer, default=3, comment="最大重试次数")
    
    # 进度信息
    progress = Column(Float, default=0.0, comment="任务进度(0-100)")
    current_step = Column(String(100), nullable=True, comment="当前步骤")
    total_frames = Column(Integer, nullable=True, comment="总帧数(视频)")
    processed_frames = Column(Integer, default=0, comment="已处理帧数")
    
    # 结果信息
    result_data = Column(Text, nullable=True, comment="检测结果(JSON)")
    result_summary = Column(Text, nullable=True, comment="结果摘要(JSON)")
    output_file_path = Column(String(500), nullable=True, comment="输出文件路径")
    visualization_path = Column(String(500), nullable=True, comment="可视化结果路径")
    
    # 性能统计
    processing_time = Column(Float, nullable=True, comment="处理时间(秒)")
    memory_usage = Column(Float, nullable=True, comment="内存使用(MB)")
    gpu_usage = Column(Float, nullable=True, comment="GPU使用率")
    
    # 错误信息
    error_message = Column(Text, nullable=True, comment="错误信息")
    error_traceback = Column(Text, nullable=True, comment="错误堆栈")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    started_at = Column(DateTime, nullable=True, comment="开始时间")
    completed_at = Column(DateTime, nullable=True, comment="完成时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    # 关系
    user = relationship("User", back_populates="detection_tasks")
    file_record = relationship("FileRecord", back_populates="detection_tasks")
    
    def __repr__(self):
        return f"<DetectionTask(id={self.id}, name={self.task_name}, status={self.status})>"
    
    def to_dict(self, include_sensitive=False):
        """转换为字典"""
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "file_record_id": self.file_record_id,
            "task_name": self.task_name,
            "description": self.description,
            "detection_type": self.detection_type.value,
            "status": self.status.value,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "confidence_threshold": self.confidence_threshold,
            "iou_threshold": self.iou_threshold,
            "max_detections": self.max_detections,
            "priority": self.priority,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "progress": self.progress,
            "current_step": self.current_step,
            "total_frames": self.total_frames,
            "processed_frames": self.processed_frames,
            "processing_time": self.processing_time,
            "memory_usage": self.memory_usage,
            "gpu_usage": self.gpu_usage,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_sensitive:
            data.update({
                "detection_params": self.get_detection_params(),
                "preprocessing_params": self.get_preprocessing_params(),
                "postprocessing_params": self.get_postprocessing_params(),
                "result_data": self.get_result_data(),
                "result_summary": self.get_result_summary(),
                "output_file_path": self.output_file_path,
                "visualization_path": self.visualization_path,
                "error_message": self.error_message,
                "error_traceback": self.error_traceback
            })
        
        return data
    
    # JSON字段的getter和setter方法
    def get_detection_params(self) -> dict:
        """获取检测参数"""
        return json.loads(self.detection_params) if self.detection_params else {}
    
    def set_detection_params(self, params: dict):
        """设置检测参数"""
        self.detection_params = json.dumps(params, ensure_ascii=False)
    
    def get_preprocessing_params(self) -> dict:
        """获取预处理参数"""
        return json.loads(self.preprocessing_params) if self.preprocessing_params else {}
    
    def set_preprocessing_params(self, params: dict):
        """设置预处理参数"""
        self.preprocessing_params = json.dumps(params, ensure_ascii=False)
    
    def get_postprocessing_params(self) -> dict:
        """获取后处理参数"""
        return json.loads(self.postprocessing_params) if self.postprocessing_params else {}
    
    def set_postprocessing_params(self, params: dict):
        """设置后处理参数"""
        self.postprocessing_params = json.dumps(params, ensure_ascii=False)
    
    def get_result_data(self) -> dict:
        """获取结果数据"""
        return json.loads(self.result_data) if self.result_data else {}
    
    def set_result_data(self, data: dict):
        """设置结果数据"""
        self.result_data = json.dumps(data, ensure_ascii=False)
    
    def get_result_summary(self) -> dict:
        """获取结果摘要"""
        return json.loads(self.result_summary) if self.result_summary else {}
    
    def set_result_summary(self, summary: dict):
        """设置结果摘要"""
        self.result_summary = json.dumps(summary, ensure_ascii=False)
    
    # 状态管理方法
    def start_processing(self):
        """开始处理"""
        self.status = TaskStatus.PROCESSING
        self.started_at = datetime.utcnow()
        self.current_step = "初始化"
        self.progress = 0.0
    
    def complete_task(self, result_data: dict = None, summary: dict = None):
        """完成任务"""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.progress = 100.0
        self.current_step = "已完成"
        
        if result_data:
            self.set_result_data(result_data)
        if summary:
            self.set_result_summary(summary)
        
        # 计算处理时间
        if self.started_at:
            self.processing_time = (self.completed_at - self.started_at).total_seconds()
    
    def fail_task(self, error_message: str, error_traceback: str = None):
        """任务失败"""
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.error_message = error_message
        self.error_traceback = error_traceback
        self.current_step = "失败"
        
        # 计算处理时间
        if self.started_at:
            self.processing_time = (self.completed_at - self.started_at).total_seconds()
    
    def cancel_task(self):
        """取消任务"""
        self.status = TaskStatus.CANCELLED
        self.completed_at = datetime.utcnow()
        self.current_step = "已取消"
    
    def update_progress(self, progress: float, current_step: str = None):
        """更新进度"""
        self.progress = max(0.0, min(100.0, progress))
        if current_step:
            self.current_step = current_step
        self.updated_at = datetime.utcnow()
    
    def can_retry(self) -> bool:
        """是否可以重试"""
        return self.status == TaskStatus.FAILED and self.retry_count < self.max_retries
    
    def retry_task(self):
        """重试任务"""
        if self.can_retry():
            self.retry_count += 1
            self.status = TaskStatus.PENDING
            self.progress = 0.0
            self.current_step = None
            self.error_message = None
            self.error_traceback = None
            self.started_at = None
            self.completed_at = None
    
    @property
    def is_finished(self) -> bool:
        """是否已结束"""
        return self.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
    
    @property
    def is_running(self) -> bool:
        """是否正在运行"""
        return self.status == TaskStatus.PROCESSING
    
    @property
    def duration(self) -> float:
        """任务持续时间(秒)"""
        if self.started_at:
            end_time = self.completed_at or datetime.utcnow()
            return (end_time - self.started_at).total_seconds()
        return 0.0
    
    @property
    def estimated_remaining_time(self) -> float:
        """预估剩余时间(秒)"""
        if self.progress > 0 and self.started_at and not self.is_finished:
            elapsed = (datetime.utcnow() - self.started_at).total_seconds()
            total_estimated = elapsed * (100.0 / self.progress)
            return max(0.0, total_estimated - elapsed)
        return 0.0