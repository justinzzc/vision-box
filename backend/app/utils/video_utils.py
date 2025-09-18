#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频工具模块
"""

import os
import cv2
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Generator
from pathlib import Path
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class VideoUtils:
    """视频工具类"""
    
    # 支持的视频格式
    SUPPORTED_FORMATS = {
        '.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v', '.3gp'
    }
    
    @staticmethod
    def is_video_file(file_path: str) -> bool:
        """检查是否为视频文件"""
        ext = Path(file_path).suffix.lower()
        return ext in VideoUtils.SUPPORTED_FORMATS
    
    @staticmethod
    def get_video_info(video_path: str) -> Dict[str, Any]:
        """获取视频基本信息"""
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return {}
            
            # 获取视频属性
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps if fps > 0 else 0
            
            # 获取编解码器信息
            fourcc = cap.get(cv2.CAP_PROP_FOURCC)
            codec = "".join([chr((int(fourcc) >> 8 * i) & 0xFF) for i in range(4)])
            
            cap.release()
            
            info = {
                "width": width,
                "height": height,
                "fps": round(fps, 2),
                "frame_count": frame_count,
                "duration": round(duration, 2),
                "duration_formatted": VideoUtils.format_duration(duration),
                "codec": codec.strip(),
                "aspect_ratio": round(width / height, 2) if height > 0 else 0,
                "resolution": f"{width}x{height}",
                "file_size": os.path.getsize(video_path)
            }
            
            return info
            
        except Exception as e:
            logger.error(f"获取视频信息失败: {str(e)}")
            return {}
    
    @staticmethod
    def format_duration(seconds: float) -> str:
        """格式化时长"""
        try:
            td = timedelta(seconds=seconds)
            hours, remainder = divmod(td.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            if hours > 0:
                return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            else:
                return f"{minutes:02d}:{seconds:02d}"
        except Exception:
            return "00:00"
    
    @staticmethod
    def extract_frame(
        video_path: str,
        frame_number: int,
        output_path: Optional[str] = None
    ) -> Optional[np.ndarray]:
        """提取指定帧"""
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return None
            
            # 跳转到指定帧
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            ret, frame = cap.read()
            
            cap.release()
            
            if ret:
                if output_path:
                    cv2.imwrite(output_path, frame)
                return frame
            
            return None
            
        except Exception as e:
            logger.error(f"提取帧失败: {str(e)}")
            return None
    
    @staticmethod
    def extract_frame_at_time(
        video_path: str,
        timestamp: float,
        output_path: Optional[str] = None
    ) -> Optional[np.ndarray]:
        """提取指定时间点的帧"""
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return None
            
            # 跳转到指定时间
            cap.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)
            ret, frame = cap.read()
            
            cap.release()
            
            if ret:
                if output_path:
                    cv2.imwrite(output_path, frame)
                return frame
            
            return None
            
        except Exception as e:
            logger.error(f"提取时间点帧失败: {str(e)}")
            return None
    
    @staticmethod
    def create_thumbnail(
        video_path: str,
        output_path: str,
        timestamp: float = 1.0,
        size: Tuple[int, int] = (300, 200)
    ) -> bool:
        """创建视频缩略图"""
        try:
            # 提取帧
            frame = VideoUtils.extract_frame_at_time(video_path, timestamp)
            if frame is None:
                return False
            
            # 调整大小
            height, width = frame.shape[:2]
            aspect_ratio = width / height
            
            if aspect_ratio > (size[0] / size[1]):
                # 宽图，以宽度为准
                new_width = size[0]
                new_height = int(new_width / aspect_ratio)
            else:
                # 高图，以高度为准
                new_height = size[1]
                new_width = int(new_height * aspect_ratio)
            
            resized_frame = cv2.resize(frame, (new_width, new_height))
            
            # 保存缩略图
            cv2.imwrite(output_path, resized_frame)
            return True
            
        except Exception as e:
            logger.error(f"创建视频缩略图失败: {str(e)}")
            return False
    
    @staticmethod
    def extract_frames(
        video_path: str,
        output_dir: str,
        frame_interval: int = 30,
        max_frames: int = 100
    ) -> List[str]:
        """批量提取帧"""
        try:
            # 确保输出目录存在
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return []
            
            frame_paths = []
            frame_count = 0
            extracted_count = 0
            
            while True:
                ret, frame = cap.read()
                if not ret or extracted_count >= max_frames:
                    break
                
                # 按间隔提取帧
                if frame_count % frame_interval == 0:
                    frame_filename = f"frame_{extracted_count:06d}.jpg"
                    frame_path = os.path.join(output_dir, frame_filename)
                    
                    cv2.imwrite(frame_path, frame)
                    frame_paths.append(frame_path)
                    extracted_count += 1
                
                frame_count += 1
            
            cap.release()
            return frame_paths
            
        except Exception as e:
            logger.error(f"批量提取帧失败: {str(e)}")
            return []
    
    @staticmethod
    def get_video_frames(
        video_path: str,
        start_frame: int = 0,
        end_frame: Optional[int] = None
    ) -> Generator[Tuple[int, np.ndarray], None, None]:
        """逐帧读取视频（生成器）"""
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return
            
            # 跳转到起始帧
            if start_frame > 0:
                cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
            
            frame_number = start_frame
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                if end_frame is not None and frame_number >= end_frame:
                    break
                
                yield frame_number, frame
                frame_number += 1
            
            cap.release()
            
        except Exception as e:
            logger.error(f"读取视频帧失败: {str(e)}")
            return
    
    @staticmethod
    def resize_video(
        input_path: str,
        output_path: str,
        size: Tuple[int, int],
        quality: int = 23
    ) -> bool:
        """调整视频大小"""
        try:
            cap = cv2.VideoCapture(input_path)
            if not cap.isOpened():
                return False
            
            # 获取原始视频属性
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            # 创建视频写入器
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, size)
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # 调整帧大小
                resized_frame = cv2.resize(frame, size)
                out.write(resized_frame)
            
            cap.release()
            out.release()
            
            return True
            
        except Exception as e:
            logger.error(f"调整视频大小失败: {str(e)}")
            return False
    
    @staticmethod
    def trim_video(
        input_path: str,
        output_path: str,
        start_time: float,
        end_time: float
    ) -> bool:
        """裁剪视频"""
        try:
            cap = cv2.VideoCapture(input_path)
            if not cap.isOpened():
                return False
            
            # 获取视频属性
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # 计算起始和结束帧
            start_frame = int(start_time * fps)
            end_frame = int(end_time * fps)
            
            # 跳转到起始帧
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
            
            # 创建视频写入器
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
            current_frame = start_frame
            
            while current_frame < end_frame:
                ret, frame = cap.read()
                if not ret:
                    break
                
                out.write(frame)
                current_frame += 1
            
            cap.release()
            out.release()
            
            return True
            
        except Exception as e:
            logger.error(f"裁剪视频失败: {str(e)}")
            return False
    
    @staticmethod
    def get_video_statistics(video_path: str) -> Dict[str, Any]:
        """获取视频统计信息"""
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return {}
            
            # 基本信息
            info = VideoUtils.get_video_info(video_path)
            
            # 采样一些帧来计算统计信息
            frame_count = info.get('frame_count', 0)
            sample_frames = min(10, frame_count)  # 最多采样10帧
            
            if sample_frames > 0:
                frame_interval = max(1, frame_count // sample_frames)
                
                brightness_values = []
                contrast_values = []
                
                for i in range(0, frame_count, frame_interval):
                    cap.set(cv2.CAP_PROP_POS_FRAMES, i)
                    ret, frame = cap.read()
                    
                    if ret:
                        # 转换为灰度
                        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                        
                        # 计算亮度（平均像素值）
                        brightness = np.mean(gray)
                        brightness_values.append(brightness)
                        
                        # 计算对比度（标准差）
                        contrast = np.std(gray)
                        contrast_values.append(contrast)
                    
                    if len(brightness_values) >= sample_frames:
                        break
                
                if brightness_values:
                    info.update({
                        'average_brightness': round(np.mean(brightness_values), 2),
                        'average_contrast': round(np.mean(contrast_values), 2),
                        'brightness_std': round(np.std(brightness_values), 2),
                        'contrast_std': round(np.std(contrast_values), 2)
                    })
            
            cap.release()
            return info
            
        except Exception as e:
            logger.error(f"获取视频统计信息失败: {str(e)}")
            return {}
    
    @staticmethod
    def validate_video(video_path: str) -> Tuple[bool, str]:
        """验证视频文件"""
        try:
            # 检查文件是否存在
            if not os.path.exists(video_path):
                return False, "文件不存在"
            
            # 检查文件扩展名
            if not VideoUtils.is_video_file(video_path):
                return False, "不支持的视频格式"
            
            # 尝试打开视频
            cap = cv2.VideoCapture(video_path)
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
            
            return True, "视频验证通过"
            
        except Exception as e:
            return False, f"视频验证失败: {str(e)}"
    
    @staticmethod
    def get_video_metadata(video_path: str) -> Dict[str, Any]:
        """获取视频元数据"""
        try:
            metadata = {
                "filename": Path(video_path).name,
                "file_size": os.path.getsize(video_path),
                "file_extension": Path(video_path).suffix.lower()
            }
            
            # 获取文件时间信息
            file_stat = os.stat(video_path)
            metadata.update({
                "created": datetime.fromtimestamp(file_stat.st_ctime),
                "modified": datetime.fromtimestamp(file_stat.st_mtime),
                "accessed": datetime.fromtimestamp(file_stat.st_atime)
            })
            
            # 获取视频信息
            video_info = VideoUtils.get_video_info(video_path)
            metadata.update(video_info)
            
            return metadata
            
        except Exception as e:
            logger.error(f"获取视频元数据失败: {str(e)}")
            return {}
    
    @staticmethod
    def calculate_video_quality_score(video_path: str) -> float:
        """计算视频质量评分（0-100）"""
        try:
            info = VideoUtils.get_video_info(video_path)
            if not info:
                return 0.0
            
            score = 0.0
            
            # 分辨率评分（40%）
            width = info.get('width', 0)
            height = info.get('height', 0)
            pixels = width * height
            
            if pixels >= 1920 * 1080:  # 1080p+
                score += 40
            elif pixels >= 1280 * 720:  # 720p
                score += 30
            elif pixels >= 854 * 480:   # 480p
                score += 20
            else:
                score += 10
            
            # 帧率评分（30%）
            fps = info.get('fps', 0)
            if fps >= 60:
                score += 30
            elif fps >= 30:
                score += 25
            elif fps >= 24:
                score += 20
            else:
                score += 10
            
            # 时长评分（20%）
            duration = info.get('duration', 0)
            if 10 <= duration <= 3600:  # 10秒到1小时
                score += 20
            elif duration > 0:
                score += 10
            
            # 文件大小合理性评分（10%）
            file_size = info.get('file_size', 0)
            if file_size > 0 and duration > 0:
                bitrate = (file_size * 8) / duration / 1000  # kbps
                if 1000 <= bitrate <= 10000:  # 合理的比特率范围
                    score += 10
                elif bitrate > 0:
                    score += 5
            
            return min(100.0, score)
            
        except Exception as e:
            logger.error(f"计算视频质量评分失败: {str(e)}")
            return 0.0
    
    @staticmethod
    def detect_scene_changes(
        video_path: str,
        threshold: float = 30.0,
        max_scenes: int = 50
    ) -> List[Dict[str, Any]]:
        """检测场景变化"""
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return []
            
            fps = cap.get(cv2.CAP_PROP_FPS)
            scenes = []
            
            ret, prev_frame = cap.read()
            if not ret:
                cap.release()
                return []
            
            prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
            frame_number = 1
            
            while len(scenes) < max_scenes:
                ret, curr_frame = cap.read()
                if not ret:
                    break
                
                curr_gray = cv2.cvtColor(curr_frame, cv2.COLOR_BGR2GRAY)
                
                # 计算帧差
                diff = cv2.absdiff(prev_gray, curr_gray)
                mean_diff = np.mean(diff)
                
                # 如果差异超过阈值，认为是场景变化
                if mean_diff > threshold:
                    timestamp = frame_number / fps
                    scenes.append({
                        'frame_number': frame_number,
                        'timestamp': round(timestamp, 2),
                        'timestamp_formatted': VideoUtils.format_duration(timestamp),
                        'difference_score': round(mean_diff, 2)
                    })
                
                prev_gray = curr_gray
                frame_number += 1
            
            cap.release()
            return scenes
            
        except Exception as e:
            logger.error(f"检测场景变化失败: {str(e)}")
            return []
    
    @staticmethod
    def create_video_preview(
        video_path: str,
        output_path: str,
        preview_duration: float = 10.0,
        start_offset: float = 5.0
    ) -> bool:
        """创建视频预览片段"""
        try:
            info = VideoUtils.get_video_info(video_path)
            if not info:
                return False
            
            total_duration = info.get('duration', 0)
            if total_duration <= preview_duration + start_offset:
                # 如果视频太短，直接复制
                import shutil
                shutil.copy2(video_path, output_path)
                return True
            
            # 裁剪预览片段
            end_time = start_offset + preview_duration
            return VideoUtils.trim_video(video_path, output_path, start_offset, end_time)
            
        except Exception as e:
            logger.error(f"创建视频预览失败: {str(e)}")
            return False