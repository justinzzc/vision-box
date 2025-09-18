#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件工具模块
"""

import os
import shutil
import hashlib
import mimetypes
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class FileUtils:
    """文件工具类"""
    
    @staticmethod
    def calculate_file_hash(file_path: str, algorithm: str = "sha256") -> str:
        """计算文件哈希值"""
        try:
            hash_func = getattr(hashlib, algorithm)()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_func.update(chunk)
            return hash_func.hexdigest()
        except Exception as e:
            logger.error(f"计算文件哈希失败: {str(e)}")
            return ""
    
    @staticmethod
    def get_file_size(file_path: str) -> int:
        """获取文件大小（字节）"""
        try:
            return os.path.getsize(file_path)
        except Exception as e:
            logger.error(f"获取文件大小失败: {str(e)}")
            return 0
    
    @staticmethod
    def get_file_size_formatted(file_path: str) -> str:
        """获取格式化的文件大小"""
        size = FileUtils.get_file_size(file_path)
        return FileUtils.format_file_size(size)
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """格式化文件大小"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"
    
    @staticmethod
    def get_mime_type(file_path: str) -> str:
        """获取文件MIME类型"""
        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type or "application/octet-stream"
    
    @staticmethod
    def get_file_extension(file_path: str) -> str:
        """获取文件扩展名"""
        return Path(file_path).suffix.lower()
    
    @staticmethod
    def get_file_name_without_extension(file_path: str) -> str:
        """获取不带扩展名的文件名"""
        return Path(file_path).stem
    
    @staticmethod
    def is_file_exists(file_path: str) -> bool:
        """检查文件是否存在"""
        return os.path.isfile(file_path)
    
    @staticmethod
    def is_directory_exists(dir_path: str) -> bool:
        """检查目录是否存在"""
        return os.path.isdir(dir_path)
    
    @staticmethod
    def create_directory(dir_path: str, exist_ok: bool = True) -> bool:
        """创建目录"""
        try:
            Path(dir_path).mkdir(parents=True, exist_ok=exist_ok)
            return True
        except Exception as e:
            logger.error(f"创建目录失败: {str(e)}")
            return False
    
    @staticmethod
    def delete_file(file_path: str) -> bool:
        """删除文件"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            logger.error(f"删除文件失败: {str(e)}")
            return False
    
    @staticmethod
    def delete_directory(dir_path: str) -> bool:
        """删除目录及其内容"""
        try:
            if os.path.exists(dir_path):
                shutil.rmtree(dir_path)
                return True
            return False
        except Exception as e:
            logger.error(f"删除目录失败: {str(e)}")
            return False
    
    @staticmethod
    def copy_file(source: str, destination: str) -> bool:
        """复制文件"""
        try:
            # 确保目标目录存在
            dest_dir = Path(destination).parent
            dest_dir.mkdir(parents=True, exist_ok=True)
            
            shutil.copy2(source, destination)
            return True
        except Exception as e:
            logger.error(f"复制文件失败: {str(e)}")
            return False
    
    @staticmethod
    def move_file(source: str, destination: str) -> bool:
        """移动文件"""
        try:
            # 确保目标目录存在
            dest_dir = Path(destination).parent
            dest_dir.mkdir(parents=True, exist_ok=True)
            
            shutil.move(source, destination)
            return True
        except Exception as e:
            logger.error(f"移动文件失败: {str(e)}")
            return False
    
    @staticmethod
    def get_file_modification_time(file_path: str) -> Optional[datetime]:
        """获取文件修改时间"""
        try:
            timestamp = os.path.getmtime(file_path)
            return datetime.fromtimestamp(timestamp)
        except Exception as e:
            logger.error(f"获取文件修改时间失败: {str(e)}")
            return None
    
    @staticmethod
    def get_file_creation_time(file_path: str) -> Optional[datetime]:
        """获取文件创建时间"""
        try:
            timestamp = os.path.getctime(file_path)
            return datetime.fromtimestamp(timestamp)
        except Exception as e:
            logger.error(f"获取文件创建时间失败: {str(e)}")
            return None
    
    @staticmethod
    def list_files_in_directory(
        dir_path: str,
        extensions: Optional[List[str]] = None,
        recursive: bool = False
    ) -> List[str]:
        """列出目录中的文件"""
        try:
            files = []
            path = Path(dir_path)
            
            if recursive:
                pattern = "**/*"
            else:
                pattern = "*"
            
            for file_path in path.glob(pattern):
                if file_path.is_file():
                    if extensions is None or file_path.suffix.lower() in extensions:
                        files.append(str(file_path))
            
            return sorted(files)
        except Exception as e:
            logger.error(f"列出目录文件失败: {str(e)}")
            return []
    
    @staticmethod
    def get_directory_size(dir_path: str) -> int:
        """获取目录大小（字节）"""
        try:
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(dir_path):
                for filename in filenames:
                    file_path = os.path.join(dirpath, filename)
                    if os.path.exists(file_path):
                        total_size += os.path.getsize(file_path)
            return total_size
        except Exception as e:
            logger.error(f"获取目录大小失败: {str(e)}")
            return 0
    
    @staticmethod
    def get_directory_stats(dir_path: str) -> Dict[str, Any]:
        """获取目录统计信息"""
        try:
            stats = {
                "total_files": 0,
                "total_directories": 0,
                "total_size": 0,
                "file_types": {},
                "largest_file": {"path": "", "size": 0},
                "oldest_file": {"path": "", "date": None},
                "newest_file": {"path": "", "date": None}
            }
            
            for root, dirs, files in os.walk(dir_path):
                stats["total_directories"] += len(dirs)
                
                for file in files:
                    file_path = os.path.join(root, file)
                    if os.path.exists(file_path):
                        stats["total_files"] += 1
                        
                        # 文件大小
                        file_size = os.path.getsize(file_path)
                        stats["total_size"] += file_size
                        
                        # 最大文件
                        if file_size > stats["largest_file"]["size"]:
                            stats["largest_file"] = {"path": file_path, "size": file_size}
                        
                        # 文件类型统计
                        ext = Path(file).suffix.lower()
                        if ext in stats["file_types"]:
                            stats["file_types"][ext]["count"] += 1
                            stats["file_types"][ext]["size"] += file_size
                        else:
                            stats["file_types"][ext] = {"count": 1, "size": file_size}
                        
                        # 文件时间
                        mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                        if stats["oldest_file"]["date"] is None or mod_time < stats["oldest_file"]["date"]:
                            stats["oldest_file"] = {"path": file_path, "date": mod_time}
                        if stats["newest_file"]["date"] is None or mod_time > stats["newest_file"]["date"]:
                            stats["newest_file"] = {"path": file_path, "date": mod_time}
            
            return stats
        except Exception as e:
            logger.error(f"获取目录统计失败: {str(e)}")
            return {}
    
    @staticmethod
    def clean_filename(filename: str) -> str:
        """清理文件名，移除不安全字符"""
        # 定义不安全字符
        unsafe_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
        
        # 替换不安全字符
        clean_name = filename
        for char in unsafe_chars:
            clean_name = clean_name.replace(char, '_')
        
        # 移除连续的下划线
        while '__' in clean_name:
            clean_name = clean_name.replace('__', '_')
        
        # 移除开头和结尾的下划线和空格
        clean_name = clean_name.strip('_ ')
        
        # 确保文件名不为空
        if not clean_name:
            clean_name = 'unnamed'
        
        return clean_name
    
    @staticmethod
    def is_safe_path(file_path: str, base_path: str) -> bool:
        """检查路径是否安全（防止路径遍历攻击）"""
        try:
            # 规范化路径
            abs_base = os.path.abspath(base_path)
            abs_path = os.path.abspath(os.path.join(base_path, file_path))
            
            # 检查路径是否在基础路径内
            return abs_path.startswith(abs_base)
        except Exception:
            return False
    
    @staticmethod
    def get_unique_filename(directory: str, filename: str) -> str:
        """获取唯一文件名（如果文件已存在，则添加数字后缀）"""
        base_path = Path(directory)
        file_path = base_path / filename
        
        if not file_path.exists():
            return filename
        
        # 分离文件名和扩展名
        name = file_path.stem
        ext = file_path.suffix
        
        # 查找可用的文件名
        counter = 1
        while True:
            new_filename = f"{name}_{counter}{ext}"
            new_path = base_path / new_filename
            if not new_path.exists():
                return new_filename
            counter += 1
    
    @staticmethod
    def read_file_chunks(file_path: str, chunk_size: int = 8192):
        """分块读取文件"""
        try:
            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    yield chunk
        except Exception as e:
            logger.error(f"读取文件失败: {str(e)}")
            return
    
    @staticmethod
    def compare_files(file1: str, file2: str) -> bool:
        """比较两个文件是否相同"""
        try:
            # 首先比较文件大小
            if os.path.getsize(file1) != os.path.getsize(file2):
                return False
            
            # 比较文件内容
            with open(file1, 'rb') as f1, open(file2, 'rb') as f2:
                while True:
                    chunk1 = f1.read(8192)
                    chunk2 = f2.read(8192)
                    
                    if chunk1 != chunk2:
                        return False
                    
                    if not chunk1:  # 到达文件末尾
                        break
            
            return True
        except Exception as e:
            logger.error(f"比较文件失败: {str(e)}")
            return False
    
    @staticmethod
    def get_file_info(file_path: str) -> Dict[str, Any]:
        """获取文件详细信息"""
        try:
            stat = os.stat(file_path)
            path_obj = Path(file_path)
            
            return {
                "name": path_obj.name,
                "stem": path_obj.stem,
                "suffix": path_obj.suffix,
                "size": stat.st_size,
                "size_formatted": FileUtils.format_file_size(stat.st_size),
                "created": datetime.fromtimestamp(stat.st_ctime),
                "modified": datetime.fromtimestamp(stat.st_mtime),
                "accessed": datetime.fromtimestamp(stat.st_atime),
                "mime_type": FileUtils.get_mime_type(file_path),
                "is_file": path_obj.is_file(),
                "is_directory": path_obj.is_dir(),
                "absolute_path": str(path_obj.absolute()),
                "parent": str(path_obj.parent)
            }
        except Exception as e:
            logger.error(f"获取文件信息失败: {str(e)}")
            return {}