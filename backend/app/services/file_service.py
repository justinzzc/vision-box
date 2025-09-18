#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件服务模块
处理文件上传、存储、管理等功能
"""

import os
import shutil
import hashlib
import mimetypes
from typing import Dict, List, Any, Optional, Tuple, BinaryIO
from pathlib import Path
import logging
from datetime import datetime, timedelta
from PIL import Image, ImageOps
import cv2

from app.core.config import get_settings
from app.models import FileRecord, FileType

settings = get_settings()
logger = logging.getLogger(__name__)


class FileService:
    """文件服务类"""
    
    def __init__(self):
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.thumbnail_dir = self.upload_dir / "thumbnails"
        self.temp_dir = self.upload_dir / "temp"
        
        # 确保目录存在
        self._ensure_directories()
        
        # 支持的文件格式
        self.supported_image_formats = {
            '.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp', '.tiff', '.tif'
        }
        self.supported_video_formats = {
            '.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v'
        }
        
        # 最大文件大小（字节）
        self.max_file_size = settings.MAX_FILE_SIZE * 1024 * 1024
        
        # 缩略图设置
        self.thumbnail_size = (300, 300)
        self.thumbnail_quality = 85
    
    def _ensure_directories(self):
        """确保必要的目录存在"""
        directories = [self.upload_dir, self.thumbnail_dir, self.temp_dir]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"确保目录存在: {directory}")
    
    def validate_file(self, filename: str, file_size: int) -> Tuple[bool, str, Optional[FileType]]:
        """验证文件"""
        # 检查文件名
        if not filename or len(filename) > 255:
            return False, "文件名无效或过长", None
        
        # 获取文件扩展名
        file_ext = Path(filename).suffix.lower()
        if not file_ext:
            return False, "文件必须有扩展名", None
        
        # 检查文件类型
        file_type = None
        if file_ext in self.supported_image_formats:
            file_type = FileType.IMAGE
        elif file_ext in self.supported_video_formats:
            file_type = FileType.VIDEO
        else:
            supported_formats = list(self.supported_image_formats | self.supported_video_formats)
            return False, f"不支持的文件格式。支持的格式: {', '.join(supported_formats)}", None
        
        # 检查文件大小
        if file_size > self.max_file_size:
            max_size_mb = self.max_file_size / (1024 * 1024)
            return False, f"文件大小超过限制 ({max_size_mb}MB)", None
        
        return True, "文件验证通过", file_type
    
    def generate_unique_filename(self, original_filename: str) -> str:
        """生成唯一文件名"""
        name = Path(original_filename).stem
        ext = Path(original_filename).suffix
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        
        # 清理文件名中的特殊字符
        safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_name = safe_name[:50]  # 限制长度
        
        return f"{safe_name}_{timestamp}_{unique_id}{ext}"
    
    def calculate_file_hash(self, file_content: bytes) -> Tuple[str, str]:
        """计算文件哈希值"""
        sha256_hash = hashlib.sha256(file_content).hexdigest()
        md5_hash = hashlib.md5(file_content).hexdigest()
        return sha256_hash, md5_hash
    
    def save_file(self, file_content: bytes, filename: str) -> Tuple[str, str]:
        """保存文件"""
        try:
            # 生成唯一文件名
            unique_filename = self.generate_unique_filename(filename)
            file_path = self.upload_dir / unique_filename
            
            # 保存文件
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            logger.info(f"文件保存成功: {file_path}")
            return str(file_path), unique_filename
            
        except Exception as e:
            logger.error(f"保存文件失败: {str(e)}")
            raise Exception(f"保存文件失败: {str(e)}")
    
    def get_image_info(self, file_path: str) -> Dict[str, Any]:
        """获取图片信息"""
        try:
            with Image.open(file_path) as img:
                # 获取EXIF信息
                exif_data = {}
                if hasattr(img, '_getexif') and img._getexif() is not None:
                    exif = img._getexif()
                    for tag_id, value in exif.items():
                        tag = Image.ExifTags.TAGS.get(tag_id, tag_id)
                        exif_data[tag] = value
                
                return {
                    "width": img.width,
                    "height": img.height,
                    "format": img.format,
                    "mode": img.mode,
                    "has_transparency": img.mode in ('RGBA', 'LA') or 'transparency' in img.info,
                    "exif": exif_data
                }
        except Exception as e:
            logger.error(f"获取图片信息失败: {str(e)}")
            return {}
    
    def get_video_info(self, file_path: str) -> Dict[str, Any]:
        """获取视频信息"""
        try:
            cap = cv2.VideoCapture(file_path)
            if not cap.isOpened():
                return {}
            
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps if fps > 0 else 0
            
            # 获取编解码器信息
            fourcc = cap.get(cv2.CAP_PROP_FOURCC)
            codec = "".join([chr((int(fourcc) >> 8 * i) & 0xFF) for i in range(4)])
            
            cap.release()
            
            return {
                "width": width,
                "height": height,
                "fps": round(fps, 2),
                "frame_count": frame_count,
                "duration": round(duration, 2),
                "codec": codec.strip(),
                "bitrate": None  # OpenCV无法直接获取比特率
            }
        except Exception as e:
            logger.error(f"获取视频信息失败: {str(e)}")
            return {}
    
    def create_thumbnail(self, file_path: str, file_type: FileType) -> Optional[str]:
        """创建缩略图"""
        try:
            filename = Path(file_path).stem
            thumbnail_path = self.thumbnail_dir / f"{filename}_thumb.jpg"
            
            if file_type == FileType.IMAGE:
                # 图片缩略图
                with Image.open(file_path) as img:
                    # 自动旋转（基于EXIF）
                    img = ImageOps.exif_transpose(img)
                    
                    # 转换为RGB（处理RGBA等格式）
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    
                    # 创建缩略图
                    img.thumbnail(self.thumbnail_size, Image.Resampling.LANCZOS)
                    img.save(thumbnail_path, 'JPEG', quality=self.thumbnail_quality, optimize=True)
            
            elif file_type == FileType.VIDEO:
                # 视频缩略图（提取第一帧）
                cap = cv2.VideoCapture(file_path)
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret:
                        # 调整大小
                        height, width = frame.shape[:2]
                        aspect_ratio = width / height
                        
                        if aspect_ratio > 1:  # 宽图
                            new_width = self.thumbnail_size[0]
                            new_height = int(new_width / aspect_ratio)
                        else:  # 高图
                            new_height = self.thumbnail_size[1]
                            new_width = int(new_height * aspect_ratio)
                        
                        resized_frame = cv2.resize(frame, (new_width, new_height))
                        cv2.imwrite(str(thumbnail_path), resized_frame)
                    cap.release()
            
            if thumbnail_path.exists():
                logger.info(f"缩略图创建成功: {thumbnail_path}")
                return str(thumbnail_path)
            
        except Exception as e:
            logger.error(f"创建缩略图失败: {str(e)}")
        
        return None
    
    def delete_file(self, file_path: str, thumbnail_path: Optional[str] = None) -> bool:
        """删除文件"""
        try:
            deleted_files = []
            
            # 删除主文件
            if os.path.exists(file_path):
                os.remove(file_path)
                deleted_files.append(file_path)
            
            # 删除缩略图
            if thumbnail_path and os.path.exists(thumbnail_path):
                os.remove(thumbnail_path)
                deleted_files.append(thumbnail_path)
            
            logger.info(f"文件删除成功: {deleted_files}")
            return True
            
        except Exception as e:
            logger.error(f"删除文件失败: {str(e)}")
            return False
    
    def move_file(self, source_path: str, destination_path: str) -> bool:
        """移动文件"""
        try:
            # 确保目标目录存在
            Path(destination_path).parent.mkdir(parents=True, exist_ok=True)
            
            shutil.move(source_path, destination_path)
            logger.info(f"文件移动成功: {source_path} -> {destination_path}")
            return True
            
        except Exception as e:
            logger.error(f"移动文件失败: {str(e)}")
            return False
    
    def copy_file(self, source_path: str, destination_path: str) -> bool:
        """复制文件"""
        try:
            # 确保目标目录存在
            Path(destination_path).parent.mkdir(parents=True, exist_ok=True)
            
            shutil.copy2(source_path, destination_path)
            logger.info(f"文件复制成功: {source_path} -> {destination_path}")
            return True
            
        except Exception as e:
            logger.error(f"复制文件失败: {str(e)}")
            return False
    
    def get_file_stats(self) -> Dict[str, Any]:
        """获取文件统计信息"""
        try:
            stats = {
                "total_files": 0,
                "total_size_bytes": 0,
                "file_types": {},
                "upload_dir_size": 0,
                "thumbnail_dir_size": 0
            }
            
            # 统计上传目录
            for file_path in self.upload_dir.rglob('*'):
                if file_path.is_file() and not file_path.name.startswith('.'):
                    file_size = file_path.stat().st_size
                    file_ext = file_path.suffix.lower()
                    
                    stats["total_files"] += 1
                    stats["total_size_bytes"] += file_size
                    stats["upload_dir_size"] += file_size
                    
                    if file_ext in stats["file_types"]:
                        stats["file_types"][file_ext]["count"] += 1
                        stats["file_types"][file_ext]["size"] += file_size
                    else:
                        stats["file_types"][file_ext] = {"count": 1, "size": file_size}
            
            # 统计缩略图目录
            for file_path in self.thumbnail_dir.rglob('*'):
                if file_path.is_file():
                    stats["thumbnail_dir_size"] += file_path.stat().st_size
            
            # 转换为更友好的单位
            stats["total_size_mb"] = round(stats["total_size_bytes"] / (1024 * 1024), 2)
            stats["upload_dir_size_mb"] = round(stats["upload_dir_size"] / (1024 * 1024), 2)
            stats["thumbnail_dir_size_mb"] = round(stats["thumbnail_dir_size"] / (1024 * 1024), 2)
            
            return stats
            
        except Exception as e:
            logger.error(f"获取文件统计失败: {str(e)}")
            return {}
    
    def cleanup_temp_files(self, max_age_hours: int = 24) -> Dict[str, Any]:
        """清理临时文件"""
        try:
            cleanup_stats = {
                "deleted_files": 0,
                "freed_space_bytes": 0,
                "errors": []
            }
            
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            
            for file_path in self.temp_dir.rglob('*'):
                if file_path.is_file():
                    try:
                        file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                        if file_mtime < cutoff_time:
                            file_size = file_path.stat().st_size
                            file_path.unlink()
                            cleanup_stats["deleted_files"] += 1
                            cleanup_stats["freed_space_bytes"] += file_size
                    except Exception as e:
                        cleanup_stats["errors"].append(f"删除文件 {file_path} 失败: {str(e)}")
            
            cleanup_stats["freed_space_mb"] = round(cleanup_stats["freed_space_bytes"] / (1024 * 1024), 2)
            
            logger.info(f"临时文件清理完成: {cleanup_stats}")
            return cleanup_stats
            
        except Exception as e:
            logger.error(f"清理临时文件失败: {str(e)}")
            return {"error": str(e)}
    
    def verify_file_integrity(self, file_path: str, expected_hash: str) -> bool:
        """验证文件完整性"""
        try:
            with open(file_path, 'rb') as f:
                file_content = f.read()
                actual_hash = hashlib.sha256(file_content).hexdigest()
                return actual_hash == expected_hash
        except Exception as e:
            logger.error(f"验证文件完整性失败: {str(e)}")
            return False
    
    def get_mime_type(self, filename: str) -> str:
        """获取MIME类型"""
        mime_type, _ = mimetypes.guess_type(filename)
        return mime_type or "application/octet-stream"
    
    def is_safe_filename(self, filename: str) -> bool:
        """检查文件名是否安全"""
        # 检查危险字符
        dangerous_chars = ['..', '/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in dangerous_chars:
            if char in filename:
                return False
        
        # 检查保留名称（Windows）
        reserved_names = [
            'CON', 'PRN', 'AUX', 'NUL',
            'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
            'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
        ]
        
        name_without_ext = Path(filename).stem.upper()
        if name_without_ext in reserved_names:
            return False
        
        return True
    
    def process_uploaded_file(
        self,
        file_content: bytes,
        filename: str,
        create_thumbnail: bool = True
    ) -> Dict[str, Any]:
        """处理上传的文件"""
        try:
            # 验证文件
            is_valid, message, file_type = self.validate_file(filename, len(file_content))
            if not is_valid:
                raise Exception(message)
            
            # 检查文件名安全性
            if not self.is_safe_filename(filename):
                raise Exception("文件名包含不安全字符")
            
            # 计算文件哈希
            file_hash, checksum = self.calculate_file_hash(file_content)
            
            # 保存文件
            file_path, stored_filename = self.save_file(file_content, filename)
            
            # 获取媒体信息
            media_info = {}
            if file_type == FileType.IMAGE:
                media_info = self.get_image_info(file_path)
            elif file_type == FileType.VIDEO:
                media_info = self.get_video_info(file_path)
            
            # 创建缩略图
            thumbnail_path = None
            if create_thumbnail:
                thumbnail_path = self.create_thumbnail(file_path, file_type)
            
            # 获取MIME类型
            mime_type = self.get_mime_type(filename)
            
            result = {
                "filename": filename,
                "stored_filename": stored_filename,
                "file_path": file_path,
                "file_type": file_type,
                "file_size": len(file_content),
                "mime_type": mime_type,
                "file_hash": file_hash,
                "checksum": checksum,
                "thumbnail_path": thumbnail_path,
                "media_info": media_info,
                "uploaded_at": datetime.utcnow()
            }
            
            logger.info(f"文件处理完成: {filename} -> {stored_filename}")
            return result
            
        except Exception as e:
            logger.error(f"处理上传文件失败: {str(e)}")
            raise e