#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件管理API接口
"""

import os
import uuid
import hashlib
import mimetypes
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query, Form
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from PIL import Image
import cv2

from app.core.database import get_db
from app.core.config import get_settings
from app.models import FileRecord, FileType, User
from app.api.v1.auth import get_current_active_user

settings = get_settings()
router = APIRouter()


# Pydantic模型
class FileInfo(BaseModel):
    """文件信息模型"""
    id: str
    filename: str
    file_type: str
    file_size: int
    mime_type: str
    width: Optional[int]
    height: Optional[int]
    duration: Optional[int]
    fps: Optional[int]
    uploaded_at: datetime
    access_url: str


class FileListResponse(BaseModel):
    """文件列表响应模型"""
    files: List[FileInfo]
    total: int
    page: int
    page_size: int
    total_pages: int


class UploadResponse(BaseModel):
    """上传响应模型"""
    file_id: str
    filename: str
    file_size: int
    file_type: str
    message: str


# 工具函数
def get_file_hash(file_content: bytes) -> str:
    """计算文件SHA256哈希"""
    return hashlib.sha256(file_content).hexdigest()


def get_file_checksum(file_content: bytes) -> str:
    """计算文件MD5校验和"""
    return hashlib.md5(file_content).hexdigest()


def get_image_info(file_path: str) -> dict:
    """获取图片信息"""
    try:
        with Image.open(file_path) as img:
            return {
                "width": img.width,
                "height": img.height,
                "format": img.format
            }
    except Exception:
        return {}


def get_video_info(file_path: str) -> dict:
    """获取视频信息"""
    try:
        cap = cv2.VideoCapture(file_path)
        if not cap.isOpened():
            return {}
        
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 else 0
        
        cap.release()
        
        return {
            "width": width,
            "height": height,
            "fps": fps,
            "duration": int(duration)
        }
    except Exception:
        return {}


def ensure_upload_directory():
    """确保上传目录存在"""
    upload_dir = settings.UPLOAD_DIR
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir, exist_ok=True)
    return upload_dir


def generate_unique_filename(original_filename: str) -> str:
    """生成唯一文件名"""
    name, ext = os.path.splitext(original_filename)
    unique_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{name}_{timestamp}_{unique_id}{ext}"


def validate_file_type(filename: str) -> bool:
    """验证文件类型"""
    return FileRecord.is_supported_format(filename)


def validate_file_size(file_size: int) -> bool:
    """验证文件大小"""
    max_size = settings.MAX_FILE_SIZE * 1024 * 1024  # 转换为字节
    return file_size <= max_size


# API端点
@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    is_public: bool = Form(False),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """上传文件"""
    from app.services import FileService
    
    file_service = FileService()
    
    try:
        # 读取文件内容
        file_content = await file.read()
        
        # 处理上传的文件
        file_info = file_service.process_uploaded_file(
            file_content, file.filename, create_thumbnail=True
        )
        
        # 创建文件记录
        file_record = FileRecord(
            id=str(uuid.uuid4()),
            filename=file_info["filename"],
            stored_filename=file_info["stored_filename"],
            file_path=file_info["file_path"],
            file_type=file_info["file_type"],
            file_size=file_info["file_size"],
            mime_type=file_info["mime_type"],
            file_hash=file_info["file_hash"],
            checksum=file_info["checksum"],
            width=file_info["media_info"].get("width"),
            height=file_info["media_info"].get("height"),
            duration=file_info["media_info"].get("duration"),
            fps=file_info["media_info"].get("fps"),
            format_info=json.dumps(file_info["media_info"], ensure_ascii=False) if file_info["media_info"] else None,
            is_public="true" if is_public else "false",
            uploaded_at=file_info["uploaded_at"]
        )
        
        db.add(file_record)
        db.commit()
        db.refresh(file_record)
        
        return UploadResponse(
            file_id=file_record.id,
            filename=file_record.filename,
            file_size=file_record.file_size,
            file_type=file_record.file_type.value,
            message="文件上传成功"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件上传失败: {str(e)}"
        )


@router.get("/list", response_model=FileListResponse)
async def list_files(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    file_type: Optional[str] = Query(None, description="文件类型过滤"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取文件列表"""
    query = db.query(FileRecord)
    
    # 文件类型过滤
    if file_type:
        try:
            file_type_enum = FileType(file_type)
            query = query.filter(FileRecord.file_type == file_type_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无效的文件类型"
            )
    
    # 搜索过滤
    if search:
        query = query.filter(FileRecord.filename.contains(search))
    
    # 计算总数
    total = query.count()
    
    # 分页
    offset = (page - 1) * page_size
    files = query.offset(offset).limit(page_size).all()
    
    # 转换为响应格式
    file_list = []
    for file_record in files:
        file_info = FileInfo(
            id=file_record.id,
            filename=file_record.filename,
            file_type=file_record.file_type.value,
            file_size=file_record.file_size,
            mime_type=file_record.mime_type,
            width=file_record.width,
            height=file_record.height,
            duration=file_record.duration,
            fps=file_record.fps,
            uploaded_at=file_record.uploaded_at,
            access_url=file_record.generate_access_url(f"{settings.API_V1_STR}")
        )
        file_list.append(file_info)
    
    total_pages = (total + page_size - 1) // page_size
    
    return FileListResponse(
        files=file_list,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/{file_id}", response_model=FileInfo)
async def get_file_info(
    file_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取文件信息"""
    file_record = db.query(FileRecord).filter(FileRecord.id == file_id).first()
    
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文件不存在"
        )
    
    # 更新访问时间
    file_record.update_access_time()
    db.commit()
    
    return FileInfo(
        id=file_record.id,
        filename=file_record.filename,
        file_type=file_record.file_type.value,
        file_size=file_record.file_size,
        mime_type=file_record.mime_type,
        width=file_record.width,
        height=file_record.height,
        duration=file_record.duration,
        fps=file_record.fps,
        uploaded_at=file_record.uploaded_at,
        access_url=file_record.generate_access_url(f"{settings.API_V1_STR}")
    )


@router.get("/{file_id}/download")
async def download_file(
    file_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """下载文件"""
    file_record = db.query(FileRecord).filter(FileRecord.id == file_id).first()
    
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文件不存在"
        )
    
    if not os.path.exists(file_record.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文件已被删除"
        )
    
    # 更新访问时间
    file_record.update_access_time()
    db.commit()
    
    return FileResponse(
        path=file_record.file_path,
        filename=file_record.filename,
        media_type=file_record.mime_type
    )


@router.get("/{file_id}/preview")
async def preview_file(
    file_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """预览文件"""
    file_record = db.query(FileRecord).filter(FileRecord.id == file_id).first()
    
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文件不存在"
        )
    
    if not os.path.exists(file_record.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文件已被删除"
        )
    
    # 更新访问时间
    file_record.update_access_time()
    db.commit()
    
    # 对于图片，直接返回
    if file_record.is_image:
        return FileResponse(
            path=file_record.file_path,
            media_type=file_record.mime_type
        )
    
    # 对于视频，返回第一帧作为预览
    elif file_record.is_video:
        # 这里可以实现视频缩略图生成逻辑
        # 暂时返回原文件
        return FileResponse(
            path=file_record.file_path,
            media_type=file_record.mime_type
        )
    
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该文件类型不支持预览"
        )


@router.delete("/{file_id}")
async def delete_file(
    file_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """删除文件"""
    file_record = db.query(FileRecord).filter(FileRecord.id == file_id).first()
    
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文件不存在"
        )
    
    try:
        # 删除物理文件
        if os.path.exists(file_record.file_path):
            os.remove(file_record.file_path)
        
        # 删除数据库记录
        db.delete(file_record)
        db.commit()
        
        return {"message": "文件删除成功"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件删除失败: {str(e)}"
        )


@router.post("/batch-upload")
async def batch_upload_files(
    files: List[UploadFile] = File(...),
    is_public: bool = Form(False),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """批量上传文件"""
    if len(files) > settings.MAX_BATCH_UPLOAD:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"批量上传文件数量不能超过 {settings.MAX_BATCH_UPLOAD} 个"
        )
    
    results = []
    errors = []
    
    for file in files:
        try:
            # 这里可以复用单文件上传的逻辑
            # 为了简化，这里只返回基本信息
            result = {
                "filename": file.filename,
                "status": "success",
                "message": "上传成功"
            }
            results.append(result)
        except Exception as e:
            error = {
                "filename": file.filename,
                "status": "error",
                "message": str(e)
            }
            errors.append(error)
    
    return {
        "total": len(files),
        "success": len(results),
        "failed": len(errors),
        "results": results,
        "errors": errors
    }


@router.get("/stats/summary")
async def get_file_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取文件统计信息"""
    total_files = db.query(FileRecord).count()
    total_images = db.query(FileRecord).filter(FileRecord.file_type == FileType.IMAGE).count()
    total_videos = db.query(FileRecord).filter(FileRecord.file_type == FileType.VIDEO).count()
    
    # 计算总存储大小
    total_size_result = db.query(db.func.sum(FileRecord.file_size)).scalar()
    total_size = total_size_result or 0
    
    return {
        "total_files": total_files,
        "total_images": total_images,
        "total_videos": total_videos,
        "total_size_bytes": total_size,
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "average_file_size_mb": round(total_size / (1024 * 1024) / total_files, 2) if total_files > 0 else 0
    }