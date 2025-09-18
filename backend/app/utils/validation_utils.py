#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证工具模块
"""

import re
import os
from typing import Dict, List, Any, Optional, Tuple, Union
from pathlib import Path
import logging
from datetime import datetime
import mimetypes

logger = logging.getLogger(__name__)


class ValidationUtils:
    """验证工具类"""
    
    # 支持的文件格式
    SUPPORTED_IMAGE_FORMATS = {
        '.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp', '.tiff', '.tif'
    }
    
    SUPPORTED_VIDEO_FORMATS = {
        '.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v', '.3gp'
    }
    
    # 危险文件扩展名
    DANGEROUS_EXTENSIONS = {
        '.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.js', '.jar',
        '.msi', '.dll', '.sys', '.ini', '.reg', '.ps1', '.sh', '.php', '.asp',
        '.jsp', '.py', '.rb', '.pl', '.sql'
    }
    
    # Windows保留文件名
    WINDOWS_RESERVED_NAMES = {
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    }
    
    @staticmethod
    def validate_email(email: str) -> Tuple[bool, str]:
        """验证邮箱格式"""
        if not email:
            return False, "邮箱不能为空"
        
        # 基本格式检查
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return False, "邮箱格式不正确"
        
        # 长度检查
        if len(email) > 254:
            return False, "邮箱长度不能超过254个字符"
        
        # 本地部分长度检查
        local_part = email.split('@')[0]
        if len(local_part) > 64:
            return False, "邮箱本地部分长度不能超过64个字符"
        
        return True, "邮箱格式正确"
    
    @staticmethod
    def validate_username(username: str) -> Tuple[bool, str]:
        """验证用户名"""
        if not username:
            return False, "用户名不能为空"
        
        # 长度检查
        if len(username) < 3:
            return False, "用户名长度不能少于3个字符"
        
        if len(username) > 50:
            return False, "用户名长度不能超过50个字符"
        
        # 字符检查
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            return False, "用户名只能包含字母、数字、下划线和连字符"
        
        # 不能以数字开头
        if username[0].isdigit():
            return False, "用户名不能以数字开头"
        
        return True, "用户名格式正确"
    
    @staticmethod
    def validate_password(password: str) -> Tuple[bool, str]:
        """验证密码强度"""
        if not password:
            return False, "密码不能为空"
        
        # 长度检查
        if len(password) < 6:
            return False, "密码长度不能少于6个字符"
        
        if len(password) > 128:
            return False, "密码长度不能超过128个字符"
        
        # 强度检查
        score = 0
        feedback = []
        
        # 检查是否包含小写字母
        if re.search(r'[a-z]', password):
            score += 1
        else:
            feedback.append("包含小写字母")
        
        # 检查是否包含大写字母
        if re.search(r'[A-Z]', password):
            score += 1
        else:
            feedback.append("包含大写字母")
        
        # 检查是否包含数字
        if re.search(r'\d', password):
            score += 1
        else:
            feedback.append("包含数字")
        
        # 检查是否包含特殊字符
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            score += 1
        else:
            feedback.append("包含特殊字符")
        
        # 根据评分判断强度
        if score < 2:
            return False, f"密码强度太弱，建议{', '.join(feedback)}"
        elif score < 3:
            return True, "密码强度中等"
        else:
            return True, "密码强度良好"
    
    @staticmethod
    def validate_filename(filename: str) -> Tuple[bool, str]:
        """验证文件名"""
        if not filename:
            return False, "文件名不能为空"
        
        # 长度检查
        if len(filename) > 255:
            return False, "文件名长度不能超过255个字符"
        
        # 危险字符检查
        dangerous_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
        for char in dangerous_chars:
            if char in filename:
                return False, f"文件名不能包含字符: {char}"
        
        # 控制字符检查
        if any(ord(char) < 32 for char in filename):
            return False, "文件名不能包含控制字符"
        
        # Windows保留名称检查
        name_without_ext = Path(filename).stem.upper()
        if name_without_ext in ValidationUtils.WINDOWS_RESERVED_NAMES:
            return False, f"文件名不能使用系统保留名称: {name_without_ext}"
        
        # 不能以点或空格开头/结尾
        if filename.startswith('.') or filename.startswith(' '):
            return False, "文件名不能以点或空格开头"
        
        if filename.endswith('.') or filename.endswith(' '):
            return False, "文件名不能以点或空格结尾"
        
        return True, "文件名格式正确"
    
    @staticmethod
    def validate_file_type(filename: str, allowed_types: Optional[List[str]] = None) -> Tuple[bool, str]:
        """验证文件类型"""
        if not filename:
            return False, "文件名不能为空"
        
        ext = Path(filename).suffix.lower()
        if not ext:
            return False, "文件必须有扩展名"
        
        # 检查是否为危险文件类型
        if ext in ValidationUtils.DANGEROUS_EXTENSIONS:
            return False, f"不允许上传 {ext} 类型的文件"
        
        # 检查是否在允许的类型列表中
        if allowed_types:
            if ext not in allowed_types:
                return False, f"不支持的文件类型: {ext}，支持的类型: {', '.join(allowed_types)}"
        else:
            # 默认只允许图像和视频文件
            all_supported = ValidationUtils.SUPPORTED_IMAGE_FORMATS | ValidationUtils.SUPPORTED_VIDEO_FORMATS
            if ext not in all_supported:
                return False, f"不支持的文件类型: {ext}"
        
        return True, "文件类型正确"
    
    @staticmethod
    def validate_file_size(file_size: int, max_size_mb: int = 100) -> Tuple[bool, str]:
        """验证文件大小"""
        if file_size <= 0:
            return False, "文件大小无效"
        
        max_size_bytes = max_size_mb * 1024 * 1024
        if file_size > max_size_bytes:
            return False, f"文件大小超过限制 ({max_size_mb}MB)"
        
        return True, "文件大小正确"
    
    @staticmethod
    def validate_image_file(file_path: str) -> Tuple[bool, str]:
        """验证图像文件"""
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                return False, "文件不存在"
            
            # 检查文件扩展名
            ext = Path(file_path).suffix.lower()
            if ext not in ValidationUtils.SUPPORTED_IMAGE_FORMATS:
                return False, f"不支持的图像格式: {ext}"
            
            # 尝试使用PIL打开图像
            from PIL import Image
            with Image.open(file_path) as img:
                # 验证图像完整性
                img.verify()
            
            # 重新打开以获取更多信息
            with Image.open(file_path) as img:
                # 检查图像尺寸
                if img.width <= 0 or img.height <= 0:
                    return False, "无效的图像尺寸"
                
                # 检查图像模式
                if img.mode not in ['RGB', 'RGBA', 'L', 'P', 'CMYK']:
                    return False, f"不支持的图像模式: {img.mode}"
            
            return True, "图像文件验证通过"
            
        except Exception as e:
            return False, f"图像文件验证失败: {str(e)}"
    
    @staticmethod
    def validate_video_file(file_path: str) -> Tuple[bool, str]:
        """验证视频文件"""
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                return False, "文件不存在"
            
            # 检查文件扩展名
            ext = Path(file_path).suffix.lower()
            if ext not in ValidationUtils.SUPPORTED_VIDEO_FORMATS:
                return False, f"不支持的视频格式: {ext}"
            
            # 尝试使用OpenCV打开视频
            import cv2
            cap = cv2.VideoCapture(file_path)
            if not cap.isOpened():
                return False, "无法打开视频文件"
            
            # 检查视频属性
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            cap.release()
            
            if width <= 0 or height <= 0:
                return False, "无效的视频尺寸"
            
            if fps <= 0:
                return False, "无效的帧率"
            
            if frame_count <= 0:
                return False, "视频没有帧"
            
            return True, "视频文件验证通过"
            
        except Exception as e:
            return False, f"视频文件验证失败: {str(e)}"
    
    @staticmethod
    def validate_path_safety(file_path: str, base_path: str) -> Tuple[bool, str]:
        """验证路径安全性（防止路径遍历攻击）"""
        try:
            # 规范化路径
            abs_base = os.path.abspath(base_path)
            abs_path = os.path.abspath(os.path.join(base_path, file_path))
            
            # 检查路径是否在基础路径内
            if not abs_path.startswith(abs_base):
                return False, "路径不安全，可能存在路径遍历攻击"
            
            return True, "路径安全"
            
        except Exception as e:
            return False, f"路径验证失败: {str(e)}"
    
    @staticmethod
    def validate_url(url: str) -> Tuple[bool, str]:
        """验证URL格式"""
        if not url:
            return False, "URL不能为空"
        
        # 基本URL格式检查
        url_pattern = r'^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/.*)?$'
        if not re.match(url_pattern, url):
            return False, "URL格式不正确"
        
        # 长度检查
        if len(url) > 2048:
            return False, "URL长度不能超过2048个字符"
        
        return True, "URL格式正确"
    
    @staticmethod
    def validate_json_data(data: Any, required_fields: Optional[List[str]] = None) -> Tuple[bool, str]:
        """验证JSON数据"""
        if not isinstance(data, dict):
            return False, "数据必须是JSON对象"
        
        # 检查必需字段
        if required_fields:
            missing_fields = []
            for field in required_fields:
                if field not in data:
                    missing_fields.append(field)
            
            if missing_fields:
                return False, f"缺少必需字段: {', '.join(missing_fields)}"
        
        return True, "JSON数据验证通过"
    
    @staticmethod
    def validate_numeric_range(
        value: Union[int, float],
        min_value: Optional[Union[int, float]] = None,
        max_value: Optional[Union[int, float]] = None
    ) -> Tuple[bool, str]:
        """验证数值范围"""
        if not isinstance(value, (int, float)):
            return False, "值必须是数字"
        
        if min_value is not None and value < min_value:
            return False, f"值不能小于 {min_value}"
        
        if max_value is not None and value > max_value:
            return False, f"值不能大于 {max_value}"
        
        return True, "数值范围正确"
    
    @staticmethod
    def validate_detection_params(params: Dict[str, Any]) -> Tuple[bool, str]:
        """验证检测参数"""
        try:
            # 验证置信度阈值
            if 'confidence_threshold' in params:
                conf = params['confidence_threshold']
                is_valid, msg = ValidationUtils.validate_numeric_range(conf, 0.0, 1.0)
                if not is_valid:
                    return False, f"置信度阈值错误: {msg}"
            
            # 验证IoU阈值
            if 'iou_threshold' in params:
                iou = params['iou_threshold']
                is_valid, msg = ValidationUtils.validate_numeric_range(iou, 0.0, 1.0)
                if not is_valid:
                    return False, f"IoU阈值错误: {msg}"
            
            # 验证最大检测数量
            if 'max_detections' in params:
                max_det = params['max_detections']
                is_valid, msg = ValidationUtils.validate_numeric_range(max_det, 1, 1000)
                if not is_valid:
                    return False, f"最大检测数量错误: {msg}"
            
            return True, "检测参数验证通过"
            
        except Exception as e:
            return False, f"检测参数验证失败: {str(e)}"
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """清理文件名"""
        if not filename:
            return "unnamed"
        
        # 移除危险字符
        dangerous_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
        clean_name = filename
        for char in dangerous_chars:
            clean_name = clean_name.replace(char, '_')
        
        # 移除控制字符
        clean_name = ''.join(char for char in clean_name if ord(char) >= 32)
        
        # 移除连续的下划线
        while '__' in clean_name:
            clean_name = clean_name.replace('__', '_')
        
        # 移除开头和结尾的下划线和空格
        clean_name = clean_name.strip('_ ')
        
        # 确保文件名不为空
        if not clean_name:
            clean_name = 'unnamed'
        
        # 限制长度
        if len(clean_name) > 200:
            name_part = Path(clean_name).stem[:150]
            ext_part = Path(clean_name).suffix
            clean_name = name_part + ext_part
        
        return clean_name
    
    @staticmethod
    def validate_batch_operation(
        items: List[Any],
        max_batch_size: int = 100
    ) -> Tuple[bool, str]:
        """验证批量操作"""
        if not items:
            return False, "批量操作项目不能为空"
        
        if len(items) > max_batch_size:
            return False, f"批量操作项目数量不能超过 {max_batch_size}"
        
        return True, "批量操作验证通过"
    
    @staticmethod
    def get_file_type_from_extension(filename: str) -> Optional[str]:
        """根据扩展名获取文件类型"""
        ext = Path(filename).suffix.lower()
        
        if ext in ValidationUtils.SUPPORTED_IMAGE_FORMATS:
            return "image"
        elif ext in ValidationUtils.SUPPORTED_VIDEO_FORMATS:
            return "video"
        else:
            return None
    
    @staticmethod
    def validate_mime_type(filename: str, file_content: bytes) -> Tuple[bool, str]:
        """验证MIME类型与文件扩展名是否匹配"""
        try:
            # 获取基于扩展名的MIME类型
            expected_mime, _ = mimetypes.guess_type(filename)
            if not expected_mime:
                return True, "无法确定预期MIME类型"  # 允许通过
            
            # 检查文件头部字节来确定实际类型
            actual_mime = None
            
            # 常见文件头部签名
            if file_content.startswith(b'\xff\xd8\xff'):
                actual_mime = 'image/jpeg'
            elif file_content.startswith(b'\x89PNG\r\n\x1a\n'):
                actual_mime = 'image/png'
            elif file_content.startswith(b'GIF87a') or file_content.startswith(b'GIF89a'):
                actual_mime = 'image/gif'
            elif file_content.startswith(b'RIFF') and b'WEBP' in file_content[:12]:
                actual_mime = 'image/webp'
            elif file_content.startswith(b'\x00\x00\x00\x20ftypmp4') or file_content.startswith(b'\x00\x00\x00\x18ftyp'):
                actual_mime = 'video/mp4'
            
            # 如果能检测到实际MIME类型，进行比较
            if actual_mime:
                if not expected_mime.startswith(actual_mime.split('/')[0]):
                    return False, f"文件内容与扩展名不匹配: 期望 {expected_mime}，实际 {actual_mime}"
            
            return True, "MIME类型验证通过"
            
        except Exception as e:
            logger.warning(f"MIME类型验证失败: {str(e)}")
            return True, "MIME类型验证跳过"  # 验证失败时允许通过
    
    @staticmethod
    def create_validation_report(validations: List[Tuple[str, bool, str]]) -> Dict[str, Any]:
        """创建验证报告"""
        report = {
            "total_validations": len(validations),
            "passed": 0,
            "failed": 0,
            "results": [],
            "errors": [],
            "overall_status": "passed"
        }
        
        for name, is_valid, message in validations:
            result = {
                "validation": name,
                "status": "passed" if is_valid else "failed",
                "message": message
            }
            
            report["results"].append(result)
            
            if is_valid:
                report["passed"] += 1
            else:
                report["failed"] += 1
                report["errors"].append(f"{name}: {message}")
        
        if report["failed"] > 0:
            report["overall_status"] = "failed"
        
        return report