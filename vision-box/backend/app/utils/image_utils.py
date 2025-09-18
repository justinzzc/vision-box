#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图像工具模块
"""

import os
import cv2
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import logging
from PIL import Image, ImageOps, ImageEnhance, ImageFilter

logger = logging.getLogger(__name__)


class ImageUtils:
    """图像工具类"""
    
    # 支持的图像格式
    SUPPORTED_FORMATS = {
        '.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp', '.tiff', '.tif'
    }
    
    @staticmethod
    def is_image_file(file_path: str) -> bool:
        """检查是否为图像文件"""
        ext = Path(file_path).suffix.lower()
        return ext in ImageUtils.SUPPORTED_FORMATS
    
    @staticmethod
    def get_image_info(image_path: str) -> Dict[str, Any]:
        """获取图像基本信息"""
        try:
            with Image.open(image_path) as img:
                info = {
                    "width": img.width,
                    "height": img.height,
                    "format": img.format,
                    "mode": img.mode,
                    "channels": len(img.getbands()),
                    "has_transparency": img.mode in ('RGBA', 'LA') or 'transparency' in img.info,
                    "file_size": os.path.getsize(image_path)
                }
                
                # 获取EXIF信息
                exif_data = {}
                if hasattr(img, '_getexif') and img._getexif() is not None:
                    exif = img._getexif()
                    for tag_id, value in exif.items():
                        tag = Image.ExifTags.TAGS.get(tag_id, tag_id)
                        exif_data[tag] = value
                
                info["exif"] = exif_data
                return info
                
        except Exception as e:
            logger.error(f"获取图像信息失败: {str(e)}")
            return {}
    
    @staticmethod
    def get_image_dimensions(image_path: str) -> Tuple[int, int]:
        """获取图像尺寸"""
        try:
            with Image.open(image_path) as img:
                return img.width, img.height
        except Exception as e:
            logger.error(f"获取图像尺寸失败: {str(e)}")
            return 0, 0
    
    @staticmethod
    def resize_image(
        input_path: str,
        output_path: str,
        size: Tuple[int, int],
        maintain_aspect_ratio: bool = True,
        quality: int = 85
    ) -> bool:
        """调整图像大小"""
        try:
            with Image.open(input_path) as img:
                if maintain_aspect_ratio:
                    img.thumbnail(size, Image.Resampling.LANCZOS)
                else:
                    img = img.resize(size, Image.Resampling.LANCZOS)
                
                # 保存图像
                save_kwargs = {}
                if img.format == 'JPEG' or output_path.lower().endswith(('.jpg', '.jpeg')):
                    save_kwargs['quality'] = quality
                    save_kwargs['optimize'] = True
                
                img.save(output_path, **save_kwargs)
                return True
                
        except Exception as e:
            logger.error(f"调整图像大小失败: {str(e)}")
            return False
    
    @staticmethod
    def create_thumbnail(
        input_path: str,
        output_path: str,
        size: Tuple[int, int] = (300, 300),
        quality: int = 85
    ) -> bool:
        """创建缩略图"""
        try:
            with Image.open(input_path) as img:
                # 自动旋转（基于EXIF）
                img = ImageOps.exif_transpose(img)
                
                # 转换为RGB（处理RGBA等格式）
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # 创建缩略图
                img.thumbnail(size, Image.Resampling.LANCZOS)
                
                # 保存缩略图
                img.save(output_path, 'JPEG', quality=quality, optimize=True)
                return True
                
        except Exception as e:
            logger.error(f"创建缩略图失败: {str(e)}")
            return False
    
    @staticmethod
    def crop_image(
        input_path: str,
        output_path: str,
        bbox: Tuple[int, int, int, int],
        quality: int = 85
    ) -> bool:
        """裁剪图像"""
        try:
            with Image.open(input_path) as img:
                cropped = img.crop(bbox)
                
                save_kwargs = {}
                if cropped.format == 'JPEG' or output_path.lower().endswith(('.jpg', '.jpeg')):
                    save_kwargs['quality'] = quality
                    save_kwargs['optimize'] = True
                
                cropped.save(output_path, **save_kwargs)
                return True
                
        except Exception as e:
            logger.error(f"裁剪图像失败: {str(e)}")
            return False
    
    @staticmethod
    def rotate_image(
        input_path: str,
        output_path: str,
        angle: float,
        expand: bool = True,
        quality: int = 85
    ) -> bool:
        """旋转图像"""
        try:
            with Image.open(input_path) as img:
                rotated = img.rotate(angle, expand=expand)
                
                save_kwargs = {}
                if rotated.format == 'JPEG' or output_path.lower().endswith(('.jpg', '.jpeg')):
                    save_kwargs['quality'] = quality
                    save_kwargs['optimize'] = True
                
                rotated.save(output_path, **save_kwargs)
                return True
                
        except Exception as e:
            logger.error(f"旋转图像失败: {str(e)}")
            return False
    
    @staticmethod
    def flip_image(
        input_path: str,
        output_path: str,
        direction: str = 'horizontal',
        quality: int = 85
    ) -> bool:
        """翻转图像"""
        try:
            with Image.open(input_path) as img:
                if direction.lower() == 'horizontal':
                    flipped = img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
                elif direction.lower() == 'vertical':
                    flipped = img.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
                else:
                    raise ValueError("方向必须是 'horizontal' 或 'vertical'")
                
                save_kwargs = {}
                if flipped.format == 'JPEG' or output_path.lower().endswith(('.jpg', '.jpeg')):
                    save_kwargs['quality'] = quality
                    save_kwargs['optimize'] = True
                
                flipped.save(output_path, **save_kwargs)
                return True
                
        except Exception as e:
            logger.error(f"翻转图像失败: {str(e)}")
            return False
    
    @staticmethod
    def adjust_brightness(
        input_path: str,
        output_path: str,
        factor: float,
        quality: int = 85
    ) -> bool:
        """调整图像亮度"""
        try:
            with Image.open(input_path) as img:
                enhancer = ImageEnhance.Brightness(img)
                enhanced = enhancer.enhance(factor)
                
                save_kwargs = {}
                if enhanced.format == 'JPEG' or output_path.lower().endswith(('.jpg', '.jpeg')):
                    save_kwargs['quality'] = quality
                    save_kwargs['optimize'] = True
                
                enhanced.save(output_path, **save_kwargs)
                return True
                
        except Exception as e:
            logger.error(f"调整亮度失败: {str(e)}")
            return False
    
    @staticmethod
    def adjust_contrast(
        input_path: str,
        output_path: str,
        factor: float,
        quality: int = 85
    ) -> bool:
        """调整图像对比度"""
        try:
            with Image.open(input_path) as img:
                enhancer = ImageEnhance.Contrast(img)
                enhanced = enhancer.enhance(factor)
                
                save_kwargs = {}
                if enhanced.format == 'JPEG' or output_path.lower().endswith(('.jpg', '.jpeg')):
                    save_kwargs['quality'] = quality
                    save_kwargs['optimize'] = True
                
                enhanced.save(output_path, **save_kwargs)
                return True
                
        except Exception as e:
            logger.error(f"调整对比度失败: {str(e)}")
            return False
    
    @staticmethod
    def apply_blur(
        input_path: str,
        output_path: str,
        radius: float = 2.0,
        quality: int = 85
    ) -> bool:
        """应用模糊效果"""
        try:
            with Image.open(input_path) as img:
                blurred = img.filter(ImageFilter.GaussianBlur(radius=radius))
                
                save_kwargs = {}
                if blurred.format == 'JPEG' or output_path.lower().endswith(('.jpg', '.jpeg')):
                    save_kwargs['quality'] = quality
                    save_kwargs['optimize'] = True
                
                blurred.save(output_path, **save_kwargs)
                return True
                
        except Exception as e:
            logger.error(f"应用模糊效果失败: {str(e)}")
            return False
    
    @staticmethod
    def convert_format(
        input_path: str,
        output_path: str,
        quality: int = 85
    ) -> bool:
        """转换图像格式"""
        try:
            with Image.open(input_path) as img:
                # 根据输出文件扩展名确定格式
                output_ext = Path(output_path).suffix.lower()
                
                # 处理透明度
                if output_ext in ['.jpg', '.jpeg'] and img.mode in ('RGBA', 'LA'):
                    # JPEG不支持透明度，转换为RGB
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                
                save_kwargs = {}
                if output_ext in ['.jpg', '.jpeg']:
                    save_kwargs['quality'] = quality
                    save_kwargs['optimize'] = True
                elif output_ext == '.png':
                    save_kwargs['optimize'] = True
                
                img.save(output_path, **save_kwargs)
                return True
                
        except Exception as e:
            logger.error(f"转换图像格式失败: {str(e)}")
            return False
    
    @staticmethod
    def get_dominant_colors(image_path: str, num_colors: int = 5) -> List[Tuple[int, int, int]]:
        """获取图像主要颜色"""
        try:
            with Image.open(image_path) as img:
                # 转换为RGB
                img = img.convert('RGB')
                
                # 缩小图像以提高性能
                img.thumbnail((150, 150))
                
                # 获取颜色
                colors = img.getcolors(maxcolors=256*256*256)
                if colors:
                    # 按出现频率排序
                    colors.sort(key=lambda x: x[0], reverse=True)
                    return [color[1] for color in colors[:num_colors]]
                
        except Exception as e:
            logger.error(f"获取主要颜色失败: {str(e)}")
        
        return []
    
    @staticmethod
    def calculate_image_hash(image_path: str, hash_size: int = 8) -> str:
        """计算图像感知哈希"""
        try:
            with Image.open(image_path) as img:
                # 转换为灰度
                img = img.convert('L')
                
                # 调整大小
                img = img.resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)
                
                # 计算差异哈希
                pixels = list(img.getdata())
                difference = []
                
                for row in range(hash_size):
                    for col in range(hash_size):
                        pixel_left = pixels[row * (hash_size + 1) + col]
                        pixel_right = pixels[row * (hash_size + 1) + col + 1]
                        difference.append(pixel_left > pixel_right)
                
                # 转换为十六进制字符串
                decimal_value = 0
                hex_string = []
                
                for index, value in enumerate(difference):
                    if value:
                        decimal_value += 2**(index % 4)
                    if (index % 4) == 3:
                        hex_string.append(hex(decimal_value)[2:])
                        decimal_value = 0
                
                return ''.join(hex_string)
                
        except Exception as e:
            logger.error(f"计算图像哈希失败: {str(e)}")
            return ""
    
    @staticmethod
    def compare_images(image1_path: str, image2_path: str) -> float:
        """比较两个图像的相似度（0-1，1表示完全相同）"""
        try:
            hash1 = ImageUtils.calculate_image_hash(image1_path)
            hash2 = ImageUtils.calculate_image_hash(image2_path)
            
            if not hash1 or not hash2:
                return 0.0
            
            # 计算汉明距离
            hamming_distance = sum(c1 != c2 for c1, c2 in zip(hash1, hash2))
            
            # 转换为相似度
            similarity = 1.0 - (hamming_distance / len(hash1))
            return similarity
            
        except Exception as e:
            logger.error(f"比较图像失败: {str(e)}")
            return 0.0
    
    @staticmethod
    def extract_image_metadata(image_path: str) -> Dict[str, Any]:
        """提取图像元数据"""
        try:
            metadata = {}
            
            with Image.open(image_path) as img:
                # 基本信息
                metadata.update({
                    "filename": Path(image_path).name,
                    "format": img.format,
                    "mode": img.mode,
                    "size": img.size,
                    "width": img.width,
                    "height": img.height
                })
                
                # EXIF数据
                if hasattr(img, '_getexif') and img._getexif():
                    exif_dict = {}
                    exif = img._getexif()
                    
                    for tag_id, value in exif.items():
                        tag = Image.ExifTags.TAGS.get(tag_id, tag_id)
                        exif_dict[tag] = value
                    
                    metadata["exif"] = exif_dict
                
                # 文件信息
                file_stat = os.stat(image_path)
                metadata.update({
                    "file_size": file_stat.st_size,
                    "created": file_stat.st_ctime,
                    "modified": file_stat.st_mtime
                })
            
            return metadata
            
        except Exception as e:
            logger.error(f"提取图像元数据失败: {str(e)}")
            return {}
    
    @staticmethod
    def validate_image(image_path: str) -> Tuple[bool, str]:
        """验证图像文件"""
        try:
            # 检查文件是否存在
            if not os.path.exists(image_path):
                return False, "文件不存在"
            
            # 检查文件扩展名
            if not ImageUtils.is_image_file(image_path):
                return False, "不支持的图像格式"
            
            # 尝试打开图像
            with Image.open(image_path) as img:
                # 验证图像完整性
                img.verify()
            
            # 重新打开以获取更多信息（verify会关闭文件）
            with Image.open(image_path) as img:
                # 检查图像尺寸
                if img.width <= 0 or img.height <= 0:
                    return False, "无效的图像尺寸"
                
                # 检查图像模式
                if img.mode not in ['RGB', 'RGBA', 'L', 'P']:
                    return False, f"不支持的图像模式: {img.mode}"
            
            return True, "图像验证通过"
            
        except Exception as e:
            return False, f"图像验证失败: {str(e)}"
    
    @staticmethod
    def get_image_statistics(image_path: str) -> Dict[str, Any]:
        """获取图像统计信息"""
        try:
            with Image.open(image_path) as img:
                # 转换为numpy数组
                img_array = np.array(img)
                
                stats = {
                    "shape": img_array.shape,
                    "dtype": str(img_array.dtype),
                    "min_value": int(img_array.min()),
                    "max_value": int(img_array.max()),
                    "mean_value": float(img_array.mean()),
                    "std_value": float(img_array.std())
                }
                
                # 如果是彩色图像，计算每个通道的统计信息
                if len(img_array.shape) == 3:
                    channel_stats = {}
                    channel_names = ['Red', 'Green', 'Blue'] if img_array.shape[2] == 3 else [f'Channel_{i}' for i in range(img_array.shape[2])]
                    
                    for i, name in enumerate(channel_names[:img_array.shape[2]]):
                        channel_data = img_array[:, :, i]
                        channel_stats[name] = {
                            "min": int(channel_data.min()),
                            "max": int(channel_data.max()),
                            "mean": float(channel_data.mean()),
                            "std": float(channel_data.std())
                        }
                    
                    stats["channels"] = channel_stats
                
                return stats
                
        except Exception as e:
            logger.error(f"获取图像统计信息失败: {str(e)}")
            return {}