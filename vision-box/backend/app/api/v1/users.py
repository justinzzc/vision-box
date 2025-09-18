#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户管理API接口
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Form, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from app.core.database import get_db
from app.core.security import get_password_hash, verify_password
from app.models import User, DetectionTask, FileRecord
from app.api.v1.auth import get_current_active_user, get_current_admin_user

router = APIRouter()


# Pydantic模型
class UserProfile(BaseModel):
    """用户资料模型"""
    id: str
    username: str
    email: str
    full_name: Optional[str]
    avatar_url: Optional[str]
    bio: Optional[str]
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login_at: Optional[datetime]


class UserUpdate(BaseModel):
    """用户更新模型"""
    full_name: Optional[str] = None
    bio: Optional[str] = None
    email: Optional[EmailStr] = None


class UserListResponse(BaseModel):
    """用户列表响应模型"""
    users: List[UserProfile]
    total: int
    page: int
    page_size: int
    total_pages: int


class UserStats(BaseModel):
    """用户统计模型"""
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    total_files: int
    total_storage_mb: float
    last_activity: Optional[datetime]
    registration_date: datetime


class UserActivity(BaseModel):
    """用户活动模型"""
    activity_type: str
    description: str
    timestamp: datetime
    details: Optional[dict]


class PasswordUpdate(BaseModel):
    """密码更新模型"""
    current_password: str
    new_password: str
    confirm_password: str


class UserPreferences(BaseModel):
    """用户偏好设置模型"""
    theme: str = "light"
    language: str = "zh-CN"
    notifications: dict = {
        "email_notifications": True,
        "task_completion": True,
        "task_failure": True,
        "system_updates": False
    }
    detection_defaults: dict = {
        "default_model": "yolov8n",
        "default_confidence": 0.5,
        "default_iou": 0.5,
        "auto_start_detection": False
    }


# API端点
@router.get("/profile", response_model=UserProfile)
async def get_user_profile(
    current_user: User = Depends(get_current_active_user)
):
    """获取用户资料"""
    return UserProfile(**current_user.to_dict())


@router.put("/profile", response_model=UserProfile)
async def update_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新用户资料"""
    # 检查邮箱是否已被其他用户使用
    if user_update.email and user_update.email != current_user.email:
        existing_user = db.query(User).filter(
            User.email == user_update.email,
            User.id != current_user.id
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被其他用户使用"
            )
        current_user.email = user_update.email
        current_user.is_verified = False  # 邮箱变更后需要重新验证
    
    # 更新其他字段
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name
    if user_update.bio is not None:
        current_user.bio = user_update.bio
    
    current_user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(current_user)
    
    return UserProfile(**current_user.to_dict())


@router.post("/upload-avatar")
async def upload_avatar(
    avatar: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """上传头像"""
    # 验证文件类型
    if not avatar.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只支持图片文件"
        )
    
    # 验证文件大小（2MB限制）
    max_size = 2 * 1024 * 1024
    avatar_content = await avatar.read()
    if len(avatar_content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="头像文件大小不能超过2MB"
        )
    
    # 这里应该实现文件保存逻辑
    # 为了简化，我们只是模拟保存并返回URL
    import uuid
    avatar_filename = f"avatar_{current_user.id}_{uuid.uuid4().hex[:8]}.jpg"
    avatar_url = f"/uploads/avatars/{avatar_filename}"
    
    # 更新用户头像URL
    current_user.avatar_url = avatar_url
    current_user.updated_at = datetime.utcnow()
    db.commit()
    
    return {
        "message": "头像上传成功",
        "avatar_url": avatar_url
    }


@router.put("/password")
async def update_password(
    password_update: PasswordUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新密码"""
    # 验证当前密码
    if not verify_password(password_update.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="当前密码错误"
        )
    
    # 验证新密码确认
    if password_update.new_password != password_update.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="新密码与确认密码不匹配"
        )
    
    # 验证新密码强度
    if len(password_update.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="密码长度至少6位"
        )
    
    # 更新密码
    current_user.password_hash = get_password_hash(password_update.new_password)
    current_user.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": "密码更新成功"}


@router.get("/preferences", response_model=UserPreferences)
async def get_user_preferences(
    current_user: User = Depends(get_current_active_user)
):
    """获取用户偏好设置"""
    import json
    
    if current_user.preferences:
        try:
            preferences_data = json.loads(current_user.preferences)
            return UserPreferences(**preferences_data)
        except (json.JSONDecodeError, TypeError):
            pass
    
    # 返回默认偏好设置
    return UserPreferences()


@router.put("/preferences", response_model=UserPreferences)
async def update_user_preferences(
    preferences: UserPreferences,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新用户偏好设置"""
    import json
    
    # 保存偏好设置
    current_user.preferences = json.dumps(preferences.dict(), ensure_ascii=False)
    current_user.updated_at = datetime.utcnow()
    db.commit()
    
    return preferences


@router.get("/stats", response_model=UserStats)
async def get_user_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取用户统计信息"""
    # 任务统计
    total_tasks = db.query(DetectionTask).filter(DetectionTask.user_id == current_user.id).count()
    completed_tasks = db.query(DetectionTask).filter(
        DetectionTask.user_id == current_user.id,
        DetectionTask.status == "completed"
    ).count()
    failed_tasks = db.query(DetectionTask).filter(
        DetectionTask.user_id == current_user.id,
        DetectionTask.status == "failed"
    ).count()
    
    # 文件统计
    # 注意：这里假设文件与用户有关联，实际可能需要调整
    total_files = db.query(FileRecord).count()  # 简化处理
    
    # 存储统计
    total_storage_result = db.query(db.func.sum(FileRecord.file_size)).scalar()
    total_storage_bytes = total_storage_result or 0
    total_storage_mb = round(total_storage_bytes / (1024 * 1024), 2)
    
    # 最后活动时间
    last_activity = current_user.last_login_at or current_user.updated_at
    
    return UserStats(
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        failed_tasks=failed_tasks,
        total_files=total_files,
        total_storage_mb=total_storage_mb,
        last_activity=last_activity,
        registration_date=current_user.created_at
    )


@router.get("/activity")
async def get_user_activity(
    limit: int = Query(20, ge=1, le=100, description="返回数量限制"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取用户活动记录"""
    # 获取最近的检测任务作为活动记录
    recent_tasks = db.query(DetectionTask).filter(
        DetectionTask.user_id == current_user.id
    ).order_by(DetectionTask.created_at.desc()).limit(limit).all()
    
    activities = []
    for task in recent_tasks:
        activity = UserActivity(
            activity_type="detection_task",
            description=f"{'完成' if task.status == 'completed' else '创建'}了检测任务: {task.task_name}",
            timestamp=task.completed_at or task.created_at,
            details={
                "task_id": task.id,
                "task_name": task.task_name,
                "status": task.status,
                "detection_type": task.detection_type
            }
        )
        activities.append(activity)
    
    return {
        "activities": [activity.dict() for activity in activities],
        "total": len(activities)
    }


@router.delete("/account")
async def delete_user_account(
    password: str = Form(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """删除用户账户"""
    # 验证密码
    if not verify_password(password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="密码错误"
        )
    
    # 删除用户相关数据
    # 注意：这里应该实现级联删除或数据清理逻辑
    # 为了简化，我们只是停用账户
    current_user.is_active = False
    current_user.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": "账户已停用"}


# 管理员专用端点
@router.get("/admin/list", response_model=UserListResponse)
async def list_all_users(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    is_active: Optional[bool] = Query(None, description="活跃状态过滤"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """获取所有用户列表（管理员）"""
    query = db.query(User)
    
    # 搜索过滤
    if search:
        query = query.filter(
            db.or_(
                User.username.contains(search),
                User.email.contains(search),
                User.full_name.contains(search)
            )
        )
    
    # 活跃状态过滤
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    # 按创建时间倒序
    query = query.order_by(User.created_at.desc())
    
    # 计算总数
    total = query.count()
    
    # 分页
    offset = (page - 1) * page_size
    users = query.offset(offset).limit(page_size).all()
    
    # 转换为响应格式
    user_list = [UserProfile(**user.to_dict()) for user in users]
    
    total_pages = (total + page_size - 1) // page_size
    
    return UserListResponse(
        users=user_list,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.put("/admin/{user_id}/status")
async def update_user_status(
    user_id: str,
    is_active: bool = Form(...),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """更新用户状态（管理员）"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 不能停用自己
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能修改自己的状态"
        )
    
    user.is_active = is_active
    user.updated_at = datetime.utcnow()
    db.commit()
    
    return {
        "message": f"用户状态已更新为 {'激活' if is_active else '停用'}",
        "user_id": user_id,
        "is_active": is_active
    }


@router.get("/admin/{user_id}/stats", response_model=UserStats)
async def get_user_stats_admin(
    user_id: str,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """获取指定用户统计信息（管理员）"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 复用用户统计逻辑
    # 这里可以调用上面的get_user_stats函数，但需要传入指定用户
    total_tasks = db.query(DetectionTask).filter(DetectionTask.user_id == user_id).count()
    completed_tasks = db.query(DetectionTask).filter(
        DetectionTask.user_id == user_id,
        DetectionTask.status == "completed"
    ).count()
    failed_tasks = db.query(DetectionTask).filter(
        DetectionTask.user_id == user_id,
        DetectionTask.status == "failed"
    ).count()
    
    total_files = db.query(FileRecord).count()  # 简化处理
    total_storage_result = db.query(db.func.sum(FileRecord.file_size)).scalar()
    total_storage_bytes = total_storage_result or 0
    total_storage_mb = round(total_storage_bytes / (1024 * 1024), 2)
    
    last_activity = user.last_login_at or user.updated_at
    
    return UserStats(
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        failed_tasks=failed_tasks,
        total_files=total_files,
        total_storage_mb=total_storage_mb,
        last_activity=last_activity,
        registration_date=user.created_at
    )