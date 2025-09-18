#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视觉检测API接口
"""

import os
import json
import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.config import get_settings
from app.models import DetectionTask, TaskStatus, DetectionType, FileRecord, User
from app.api.v1.auth import get_current_active_user
from loguru import logger

settings = get_settings()
router = APIRouter()


# Pydantic模型
class DetectionTaskCreate(BaseModel):
    """检测任务创建模型"""
    file_record_id: str
    task_name: str
    description: Optional[str] = None
    detection_type: DetectionType
    model_name: str = "yolov8n"
    confidence_threshold: float = Field(0.5, ge=0.0, le=1.0)
    iou_threshold: float = Field(0.5, ge=0.0, le=1.0)
    max_detections: int = Field(100, ge=1, le=1000)
    detection_params: Optional[Dict[str, Any]] = None
    preprocessing_params: Optional[Dict[str, Any]] = None
    postprocessing_params: Optional[Dict[str, Any]] = None


class DetectionTaskResponse(BaseModel):
    """检测任务响应模型"""
    id: str
    task_name: str
    description: Optional[str]
    detection_type: str
    status: str
    model_name: str
    confidence_threshold: float
    iou_threshold: float
    max_detections: int
    progress: float
    current_step: Optional[str]
    total_frames: Optional[int]
    processed_frames: int
    processing_time: Optional[float]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    file_info: Dict[str, Any]
    result_summary: Optional[Dict[str, Any]]


class DetectionResult(BaseModel):
    """检测结果模型"""
    task_id: str
    status: str
    progress: float
    current_step: Optional[str]
    result_data: Optional[Dict[str, Any]]
    result_summary: Optional[Dict[str, Any]]
    visualization_path: Optional[str]
    annotated_url: Optional[str]
    output_file_path: Optional[str]
    processing_time: Optional[float]
    error_message: Optional[str]
    # 文件信息
    file_info: Optional[Dict[str, Any]]
    original_url: Optional[str]


class TaskListResponse(BaseModel):
    """任务列表响应模型"""
    tasks: List[DetectionTaskResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ModelInfo(BaseModel):
    """模型信息模型"""
    name: str
    display_name: str
    description: str
    supported_types: List[str]
    default_confidence: float
    default_iou: float
    input_size: List[int]
    is_available: bool


# 可用模型配置
AVAILABLE_MODELS = {
    "yolov8n": {
        "display_name": "YOLOv8 Nano",
        "description": "轻量级目标检测模型，速度快",
        "supported_types": ["object_detection"],
        "default_confidence": 0.5,
        "default_iou": 0.5,
        "input_size": [640, 640],
        "is_available": True
    },
    "yolov8s": {
        "display_name": "YOLOv8 Small",
        "description": "小型目标检测模型，平衡速度和精度",
        "supported_types": ["object_detection"],
        "default_confidence": 0.5,
        "default_iou": 0.5,
        "input_size": [640, 640],
        "is_available": True
    },
    "yolov8m": {
        "display_name": "YOLOv8 Medium",
        "description": "中型目标检测模型，精度较高",
        "supported_types": ["object_detection"],
        "default_confidence": 0.5,
        "default_iou": 0.5,
        "input_size": [640, 640],
        "is_available": True
    },
    "yolov8l": {
        "display_name": "YOLOv8 Large",
        "description": "大型目标检测模型，精度高但速度较慢",
        "supported_types": ["object_detection"],
        "default_confidence": 0.5,
        "default_iou": 0.5,
        "input_size": [640, 640],
        "is_available": True
    },
    "yolov8x": {
        "display_name": "YOLOv8 Extra Large",
        "description": "超大型目标检测模型，最高精度",
        "supported_types": ["object_detection"],
        "default_confidence": 0.5,
        "default_iou": 0.5,
        "input_size": [640, 640],
        "is_available": True
    }
}


# 工具函数
def validate_model_for_detection_type(model_name: str, detection_type: DetectionType) -> bool:
    """验证模型是否支持指定的检测类型"""
    if model_name not in AVAILABLE_MODELS:
        return False
    
    supported_types = AVAILABLE_MODELS[model_name]["supported_types"]
    return detection_type.value in supported_types


def convert_local_path_to_url(local_path: str) -> str:
    """将本地文件路径转换为HTTP可访问的URL"""
    if not local_path:
        return None
    
    from app.core.config import get_settings
    settings = get_settings()
    
    # 将Windows路径分隔符转换为URL路径分隔符
    normalized_path = local_path.replace('\\', '/')
    
    # 如果路径包含UPLOAD_DIR，提取相对路径
    upload_dir = settings.UPLOAD_DIR.replace('\\', '/')
    if upload_dir in normalized_path:
        relative_path = normalized_path.split(upload_dir)[-1]
        # 确保路径以/开头
        if not relative_path.startswith('/'):
            relative_path = '/' + relative_path
        return f"/uploads{relative_path}"
    
    # 如果路径以data/uploads开头，直接转换
    if normalized_path.startswith('data/uploads/'):
        relative_path = normalized_path.replace('data/uploads', '')
        return f"/uploads{relative_path}"
    
    return local_path


async def run_detection_task(task_id: str, db: AsyncSession):
    """运行检测任务（后台任务）"""
    from app.services import DetectionService, VisualizationService
    
    query = select(DetectionTask).where(DetectionTask.id == task_id)
    result = await db.execute(query)
    task = result.scalar_one_or_none()
    if not task:
        return
    
    detection_service = DetectionService()
    visualization_service = VisualizationService()
    
    try:
        # 开始处理
        task.start_processing()
        await db.commit()
        
        # 获取文件信息
        file_result = await db.execute(select(FileRecord).where(FileRecord.id == task.file_record_id))
        file_record = file_result.scalar_one_or_none()
        if not file_record or not os.path.exists(file_record.file_path):
            task.fail_task("文件不存在或已被删除")
            await db.commit()
            return
        
        # 进度回调函数
        async def progress_callback(progress: float, step: str):
            task.update_progress(progress, step)
            await db.commit()
        
        # 执行检测
        await progress_callback(10, "开始检测处理")
        
        detection_result = await detection_service.process_detection_task(
            task, file_record, progress_callback
        )
        
        result_data = detection_result["result_data"]
        result_summary = detection_result["result_summary"]
        
        await progress_callback(85, "创建可视化结果")
        
        # 创建可视化
        try:
            visualization_paths = await visualization_service.create_visualization_for_task(
                task, file_record, result_data, progress_callback
            )
            
            # 保存可视化路径
            if "main" in visualization_paths:
                task.visualization_path = visualization_paths["main"]
            if "json" in visualization_paths:
                task.output_file_path = visualization_paths["json"]
                
        except Exception as viz_error:
            logger.warning(f"创建可视化失败，但检测成功: {str(viz_error)}")
        
        # 完成任务
        task.complete_task(result_data, result_summary)
        await db.commit()
        
    except Exception as e:
        logger.error(f"检测任务失败: {str(e)}")
        task.fail_task(str(e))
        await db.commit()


# API端点
@router.post("/tasks", response_model=DetectionTaskResponse, status_code=status.HTTP_201_CREATED)
async def create_detection_task(
    task_data: DetectionTaskCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """创建检测任务"""
    from sqlalchemy import select
    
    # 验证文件是否存在
    logger.info(f"查找文件记录，file_record_id: {task_data.file_record_id}")
    result = await db.execute(select(FileRecord).where(FileRecord.id == task_data.file_record_id))
    file_record = result.scalar_one_or_none()
    
    if not file_record:
        # 查询所有文件记录用于调试
        all_files_result = await db.execute(select(FileRecord.id, FileRecord.filename).limit(10))
        all_files = all_files_result.fetchall()
        logger.error(f"文件记录不存在，查找的ID: {task_data.file_record_id}")
        logger.error(f"数据库中现有的文件记录: {all_files}")
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"文件不存在，ID: {task_data.file_record_id}"
        )
    
    logger.info(f"找到文件记录: {file_record.filename}")
    
    # 验证模型是否支持检测类型
    if not validate_model_for_detection_type(task_data.model_name, task_data.detection_type):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"模型 {task_data.model_name} 不支持 {task_data.detection_type.value} 检测类型"
        )
    
    # 创建检测任务
    import uuid
    detection_task = DetectionTask(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        file_record_id=task_data.file_record_id,
        task_name=task_data.task_name,
        description=task_data.description,
        detection_type=task_data.detection_type,
        model_name=task_data.model_name,
        confidence_threshold=task_data.confidence_threshold,
        iou_threshold=task_data.iou_threshold,
        max_detections=task_data.max_detections,
        created_at=datetime.utcnow()
    )
    
    # 设置参数
    if task_data.detection_params:
        detection_task.set_detection_params(task_data.detection_params)
    if task_data.preprocessing_params:
        detection_task.set_preprocessing_params(task_data.preprocessing_params)
    if task_data.postprocessing_params:
        detection_task.set_postprocessing_params(task_data.postprocessing_params)
    
    db.add(detection_task)
    await db.commit()
    await db.refresh(detection_task)
    
    # 添加后台任务
    background_tasks.add_task(run_detection_task, detection_task.id, db)
    
    # 返回任务信息
    return DetectionTaskResponse(
        id=detection_task.id,
        task_name=detection_task.task_name,
        description=detection_task.description,
        detection_type=detection_task.detection_type.value,
        status=detection_task.status.value,
        model_name=detection_task.model_name,
        confidence_threshold=detection_task.confidence_threshold,
        iou_threshold=detection_task.iou_threshold,
        max_detections=detection_task.max_detections,
        progress=detection_task.progress,
        current_step=detection_task.current_step,
        total_frames=detection_task.total_frames,
        processed_frames=detection_task.processed_frames,
        processing_time=detection_task.processing_time,
        created_at=detection_task.created_at,
        started_at=detection_task.started_at,
        completed_at=detection_task.completed_at,
        file_info=file_record.to_dict(),
        result_summary=detection_task.get_result_summary() if detection_task.result_summary else None
    )


@router.get("/tasks", response_model=TaskListResponse)
async def list_detection_tasks(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status_filter: Optional[TaskStatus] = Query(None, description="状态过滤"),
    detection_type_filter: Optional[DetectionType] = Query(None, description="检测类型过滤"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取检测任务列表"""
    from sqlalchemy import select, func
    
    # 构建基础查询
    query = select(DetectionTask).where(DetectionTask.user_id == current_user.id)
    
    # 状态过滤
    if status_filter:
        query = query.where(DetectionTask.status == status_filter)
    
    # 检测类型过滤
    if detection_type_filter:
        query = query.where(DetectionTask.detection_type == detection_type_filter)
    
    # 搜索过滤
    if search:
        query = query.where(DetectionTask.task_name.contains(search))
    
    # 按创建时间倒序
    query = query.order_by(DetectionTask.created_at.desc())
    
    # 计算总数
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 分页
    offset = (page - 1) * page_size
    paginated_query = query.offset(offset).limit(page_size)
    result = await db.execute(paginated_query)
    tasks = result.scalars().all()
    
    # 转换为响应格式
    task_list = []
    for task in tasks:
        file_result = await db.execute(select(FileRecord).where(FileRecord.id == task.file_record_id))
        file_record = file_result.scalar_one_or_none()
        
        task_response = DetectionTaskResponse(
            id=task.id,
            task_name=task.task_name,
            description=task.description,
            detection_type=task.detection_type.value,
            status=task.status.value,
            model_name=task.model_name,
            confidence_threshold=task.confidence_threshold,
            iou_threshold=task.iou_threshold,
            max_detections=task.max_detections,
            progress=task.progress,
            current_step=task.current_step,
            total_frames=task.total_frames,
            processed_frames=task.processed_frames,
            processing_time=task.processing_time,
            created_at=task.created_at,
            started_at=task.started_at,
            completed_at=task.completed_at,
            file_info=file_record.to_dict() if file_record else {},
            result_summary=task.get_result_summary() if task.result_summary else None
        )
        task_list.append(task_response)
    
    total_pages = (total + page_size - 1) // page_size
    
    return TaskListResponse(
        tasks=task_list,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/tasks/{task_id}", response_model=DetectionResult)
async def get_detection_result(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取检测结果"""
    from sqlalchemy import select
    
    result = await db.execute(select(DetectionTask).where(
        DetectionTask.id == task_id,
        DetectionTask.user_id == current_user.id
    ))
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    # 获取文件信息
    file_result = await db.execute(select(FileRecord).where(FileRecord.id == task.file_record_id))
    file_record = file_result.scalar_one_or_none()
    
    # 构建文件信息和原始文件URL
    file_info = file_record.to_dict() if file_record else None
    original_url = None
    if file_record:
        # 生成原始文件的访问URL
        if file_record.is_public == "true":
            original_url = f"/uploads/{file_record.stored_filename}"
        else:
            original_url = f"/uploads/{file_record.stored_filename}"
    
    return DetectionResult(
        task_id=task.id,
        status=task.status.value,
        progress=task.progress,
        current_step=task.current_step,
        result_data=task.get_result_data() if task.result_data else None,
        result_summary=task.get_result_summary() if task.result_summary else None,
        visualization_path=task.visualization_path,
        annotated_url=convert_local_path_to_url(task.visualization_path),
        output_file_path=task.output_file_path,
        processing_time=task.processing_time,
        error_message=task.error_message,
        file_info=file_info,
        original_url=original_url
    )


@router.post("/tasks/{task_id}/retry")
async def retry_detection_task(
    task_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """重试检测任务"""
    from sqlalchemy import select
    
    result = await db.execute(select(DetectionTask).where(
        DetectionTask.id == task_id,
        DetectionTask.user_id == current_user.id
    ))
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    if not task.can_retry():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="任务无法重试"
        )
    
    # 重试任务
    task.retry_task()
    await db.commit()
    
    # 添加后台任务
    background_tasks.add_task(run_detection_task, task.id, db)
    
    return {"message": "任务重试已启动"}


@router.delete("/tasks/{task_id}")
async def delete_detection_task(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """删除检测任务"""
    from sqlalchemy import select
    
    result = await db.execute(select(DetectionTask).where(
        DetectionTask.id == task_id,
        DetectionTask.user_id == current_user.id
    ))
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    # 如果任务正在运行，先取消
    if task.is_running:
        task.cancel_task()
    
    # 删除相关文件
    if task.output_file_path and os.path.exists(task.output_file_path):
        os.remove(task.output_file_path)
    if task.visualization_path and os.path.exists(task.visualization_path):
        os.remove(task.visualization_path)
    
    # 删除任务
    await db.delete(task)
    await db.commit()
    
    return {"message": "任务删除成功"}


@router.get("/models", response_model=List[ModelInfo])
async def list_available_models(
    detection_type: Optional[DetectionType] = Query(None, description="检测类型过滤")
):
    """获取可用模型列表"""
    models = []
    
    for model_name, model_config in AVAILABLE_MODELS.items():
        # 检测类型过滤
        if detection_type and detection_type.value not in model_config["supported_types"]:
            continue
        
        model_info = ModelInfo(
            name=model_name,
            display_name=model_config["display_name"],
            description=model_config["description"],
            supported_types=model_config["supported_types"],
            default_confidence=model_config["default_confidence"],
            default_iou=model_config["default_iou"],
            input_size=model_config["input_size"],
            is_available=model_config["is_available"]
        )
        models.append(model_info)
    
    return models


@router.get("/tasks/{task_id}/download/{file_type}")
async def download_detection_result(
    task_id: str,
    file_type: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """下载检测结果文件"""
    from fastapi.responses import FileResponse
    from sqlalchemy import select
    
    result = await db.execute(select(DetectionTask).where(
        DetectionTask.id == task_id,
        DetectionTask.user_id == current_user.id
    ))
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    file_path = None
    filename = None
    
    if file_type == "visualization" and task.visualization_path:
        file_path = task.visualization_path
        filename = f"{task.task_name}_visualization.jpg"
    elif file_type == "json" and task.output_file_path:
        file_path = task.output_file_path
        filename = f"{task.task_name}_results.json"
    elif file_type == "csv":
        # 动态生成CSV文件
        from app.services import VisualizationService
        visualization_service = VisualizationService()
        
        file_result = await db.execute(select(FileRecord).where(FileRecord.id == task.file_record_id))
        file_record = file_result.scalar_one_or_none()
        if file_record and task.result_data:
            try:
                csv_path = visualization_service.export_detection_results(
                    task, file_record, task.get_result_data(), "csv"
                )
                file_path = csv_path
                filename = f"{task.task_name}_results.csv"
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"生成CSV文件失败: {str(e)}"
                )
    
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="结果文件不存在"
        )
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='application/octet-stream'
    )


@router.post("/tasks/{task_id}/export")
async def export_detection_results(
    task_id: str,
    format: str = Form("json"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """导出检测结果"""
    from app.services import VisualizationService
    from sqlalchemy import select
    
    result = await db.execute(select(DetectionTask).where(
        DetectionTask.id == task_id,
        DetectionTask.user_id == current_user.id
    ))
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    if task.status != TaskStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只能导出已完成的任务结果"
        )
    
    file_result = await db.execute(select(FileRecord).where(FileRecord.id == task.file_record_id))
    file_record = file_result.scalar_one_or_none()
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="关联文件不存在"
        )
    
    try:
        visualization_service = VisualizationService()
        export_path = visualization_service.export_detection_results(
            task, file_record, task.get_result_data(), format.lower()
        )
        
        return {
            "message": "导出成功",
            "format": format,
            "export_path": export_path,
            "download_url": f"/api/v1/detection/tasks/{task_id}/download/{format}"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导出失败: {str(e)}"
        )


@router.get("/history", response_model=TaskListResponse)
async def get_detection_history(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    status_filter: Optional[TaskStatus] = Query(None, description="状态过滤"),
    detection_type_filter: Optional[DetectionType] = Query(None, description="检测类型过滤"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取检测历史记录"""
    return await list_detection_tasks(
        page=page,
        page_size=page_size,
        status_filter=status_filter,
        detection_type_filter=detection_type_filter,
        search=search,
        current_user=current_user,
        db=db
    )


@router.get("/stats/summary")
async def get_detection_stats(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取检测统计信息"""
    from sqlalchemy import select, func
    
    # 总任务数
    total_result = await db.execute(select(func.count(DetectionTask.id)).where(DetectionTask.user_id == current_user.id))
    total_tasks = total_result.scalar()
    
    # 完成任务数
    completed_result = await db.execute(select(func.count(DetectionTask.id)).where(
        DetectionTask.user_id == current_user.id,
        DetectionTask.status == TaskStatus.COMPLETED
    ))
    completed_tasks = completed_result.scalar()
    
    # 失败任务数
    failed_result = await db.execute(select(func.count(DetectionTask.id)).where(
        DetectionTask.user_id == current_user.id,
        DetectionTask.status == TaskStatus.FAILED
    ))
    failed_tasks = failed_result.scalar()
    
    # 运行中任务数
    running_result = await db.execute(select(func.count(DetectionTask.id)).where(
        DetectionTask.user_id == current_user.id,
        DetectionTask.status == TaskStatus.PROCESSING
    ))
    running_tasks = running_result.scalar()
    
    # 计算平均处理时间
    avg_result = await db.execute(select(func.avg(DetectionTask.processing_time)).where(
        DetectionTask.user_id == current_user.id,
        DetectionTask.status == TaskStatus.COMPLETED,
        DetectionTask.processing_time.isnot(None)
    ))
    avg_processing_time_result = avg_result.scalar()
    avg_processing_time = float(avg_processing_time_result) if avg_processing_time_result else 0.0
    
    return {
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "failed_tasks": failed_tasks,
        "running_tasks": running_tasks,
        "success_rate": round(completed_tasks / total_tasks * 100, 2) if total_tasks > 0 else 0,
        "average_processing_time": round(avg_processing_time, 2)
    }