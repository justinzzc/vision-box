#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
可视化服务模块
处理检测结果的可视化展示和导出功能
"""

import os
import cv2
import json
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import logging
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

try:
    import supervision as sv
    SUPERVISION_AVAILABLE = True
except ImportError:
    SUPERVISION_AVAILABLE = False
    logging.warning("Supervision库未安装，将使用基础可视化功能")

from app.core.config import get_settings
from app.models import DetectionTask, FileRecord

settings = get_settings()
logger = logging.getLogger(__name__)


class VisualizationService:
    """可视化服务类"""
    
    def __init__(self):
        self.output_dir = Path(settings.UPLOAD_DIR) / "outputs"
        self.visualization_dir = Path(settings.UPLOAD_DIR) / "visualizations"
        
        # 确保目录存在
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.visualization_dir.mkdir(parents=True, exist_ok=True)
        
        # 可视化配置
        self.colors = [
            (255, 0, 0),    # 红色
            (0, 255, 0),    # 绿色
            (0, 0, 255),    # 蓝色
            (255, 255, 0),  # 黄色
            (255, 0, 255),  # 洋红
            (0, 255, 255),  # 青色
            (255, 128, 0),  # 橙色
            (128, 0, 255),  # 紫色
            (255, 192, 203), # 粉色
            (0, 128, 128),  # 深青色
        ]
        
        self.font_scale = 0.6
        self.font_thickness = 2
        self.box_thickness = 2
        
        # 尝试加载字体
        self.font = None
        try:
            # 在Windows上尝试加载中文字体
            font_paths = [
                "C:/Windows/Fonts/msyh.ttc",  # 微软雅黑
                "C:/Windows/Fonts/simhei.ttf", # 黑体
                "C:/Windows/Fonts/simsun.ttc", # 宋体
            ]
            for font_path in font_paths:
                if os.path.exists(font_path):
                    self.font = ImageFont.truetype(font_path, 20)
                    break
        except Exception:
            pass
    
    def get_class_color(self, class_id: int) -> Tuple[int, int, int]:
        """根据类别ID获取颜色"""
        return self.colors[class_id % len(self.colors)]
    
    def draw_detection_box(
        self,
        image: np.ndarray,
        bbox: List[int],
        class_name: str,
        confidence: float,
        class_id: int = 0
    ) -> np.ndarray:
        """在图像上绘制检测框"""
        x1, y1, x2, y2 = bbox
        color = self.get_class_color(class_id)
        
        # 绘制边界框
        cv2.rectangle(image, (x1, y1), (x2, y2), color, self.box_thickness)
        
        # 准备标签文本
        label = f"{class_name}: {confidence:.2f}"
        
        # 计算文本大小
        (text_width, text_height), baseline = cv2.getTextSize(
            label, cv2.FONT_HERSHEY_SIMPLEX, self.font_scale, self.font_thickness
        )
        
        # 绘制标签背景
        label_y = y1 - 10 if y1 - 10 > text_height else y1 + text_height + 10
        cv2.rectangle(
            image,
            (x1, label_y - text_height - 5),
            (x1 + text_width + 5, label_y + 5),
            color,
            -1
        )
        
        # 绘制标签文本
        cv2.putText(
            image,
            label,
            (x1 + 2, label_y - 2),
            cv2.FONT_HERSHEY_SIMPLEX,
            self.font_scale,
            (255, 255, 255),
            self.font_thickness
        )
        
        return image
    
    def visualize_image_detections(
        self,
        image_path: str,
        detections: List[Dict[str, Any]],
        output_path: Optional[str] = None
    ) -> str:
        """可视化图像检测结果"""
        try:
            # 读取图像
            image = cv2.imread(image_path)
            if image is None:
                raise Exception(f"无法读取图像: {image_path}")
            
            # 绘制检测结果
            for detection in detections:
                bbox = detection.get("bbox", [])
                class_name = detection.get("class_name", "unknown")
                confidence = detection.get("confidence", 0.0)
                class_id = detection.get("class_id", 0)
                
                if len(bbox) == 4:
                    image = self.draw_detection_box(
                        image, bbox, class_name, confidence, class_id
                    )
            
            # 添加统计信息
            stats_text = f"Detections: {len(detections)}"
            cv2.putText(
                image,
                stats_text,
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2
            )
            
            # 保存结果
            if output_path is None:
                filename = Path(image_path).stem + "_detected.jpg"
                output_path = str(self.visualization_dir / filename)
            
            cv2.imwrite(output_path, image)
            logger.info(f"图像可视化结果保存至: {output_path}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"图像可视化失败: {str(e)}")
            raise Exception(f"图像可视化失败: {str(e)}")
    
    def visualize_video_detections(
        self,
        video_path: str,
        frame_detections: List[Dict[str, Any]],
        output_path: Optional[str] = None,
        progress_callback: Optional[callable] = None
    ) -> str:
        """可视化视频检测结果"""
        try:
            # 打开输入视频
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise Exception(f"无法打开视频: {video_path}")
            
            # 获取视频属性
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # 设置输出路径
            if output_path is None:
                filename = Path(video_path).stem + "_detected.mp4"
                output_path = str(self.visualization_dir / filename)
            
            # 创建视频写入器
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
            # 创建检测结果索引
            detection_index = {}
            for frame_data in frame_detections:
                frame_id = frame_data.get("frame_id", 0)
                detection_index[frame_id] = frame_data.get("detections", [])
            
            frame_count = 0
            processed_frames = 0
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # 获取当前帧的检测结果
                current_detections = detection_index.get(processed_frames, [])
                
                # 绘制检测结果
                for detection in current_detections:
                    bbox = detection.get("bbox", [])
                    class_name = detection.get("class_name", "unknown")
                    confidence = detection.get("confidence", 0.0)
                    class_id = detection.get("class_id", 0)
                    
                    if len(bbox) == 4:
                        frame = self.draw_detection_box(
                            frame, bbox, class_name, confidence, class_id
                        )
                
                # 添加帧信息
                frame_info = f"Frame: {processed_frames}, Detections: {len(current_detections)}"
                cv2.putText(
                    frame,
                    frame_info,
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    2
                )
                
                # 写入帧
                out.write(frame)
                
                processed_frames += 1
                frame_count += 1
                
                # 进度回调
                if progress_callback and frame_count % 10 == 0:
                    progress = (frame_count / total_frames) * 100
                    progress_callback(progress, f"处理第 {frame_count} 帧")
            
            # 释放资源
            cap.release()
            out.release()
            
            logger.info(f"视频可视化结果保存至: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"视频可视化失败: {str(e)}")
            raise Exception(f"视频可视化失败: {str(e)}")
    
    def create_detection_summary_image(
        self,
        detections: List[Dict[str, Any]],
        image_info: Dict[str, Any],
        output_path: Optional[str] = None
    ) -> str:
        """创建检测结果摘要图像"""
        try:
            # 创建画布
            canvas_width = 800
            canvas_height = 600
            canvas = Image.new('RGB', (canvas_width, canvas_height), 'white')
            draw = ImageDraw.Draw(canvas)
            
            # 使用字体
            title_font = self.font if self.font else ImageFont.load_default()
            text_font = self.font if self.font else ImageFont.load_default()
            
            # 绘制标题
            title = "检测结果摘要"
            draw.text((20, 20), title, fill='black', font=title_font)
            
            # 绘制基本信息
            y_offset = 80
            info_lines = [
                f"总检测数量: {len(detections)}",
                f"图像尺寸: {image_info.get('width', 'N/A')} x {image_info.get('height', 'N/A')}",
                f"处理时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            ]
            
            for line in info_lines:
                draw.text((20, y_offset), line, fill='black', font=text_font)
                y_offset += 30
            
            # 统计类别
            class_counts = {}
            for detection in detections:
                class_name = detection.get("class_name", "unknown")
                class_counts[class_name] = class_counts.get(class_name, 0) + 1
            
            # 绘制类别统计
            y_offset += 20
            draw.text((20, y_offset), "检测类别统计:", fill='black', font=text_font)
            y_offset += 30
            
            for class_name, count in class_counts.items():
                line = f"  {class_name}: {count}"
                draw.text((40, y_offset), line, fill='blue', font=text_font)
                y_offset += 25
            
            # 绘制置信度分布
            if detections:
                confidences = [d.get("confidence", 0) for d in detections]
                avg_confidence = sum(confidences) / len(confidences)
                max_confidence = max(confidences)
                min_confidence = min(confidences)
                
                y_offset += 20
                confidence_lines = [
                    "置信度统计:",
                    f"  平均置信度: {avg_confidence:.3f}",
                    f"  最高置信度: {max_confidence:.3f}",
                    f"  最低置信度: {min_confidence:.3f}"
                ]
                
                for line in confidence_lines:
                    color = 'black' if line.startswith('置信度') else 'green'
                    draw.text((20, y_offset), line, fill=color, font=text_font)
                    y_offset += 25
            
            # 保存图像
            if output_path is None:
                filename = f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                output_path = str(self.visualization_dir / filename)
            
            canvas.save(output_path)
            logger.info(f"检测摘要图像保存至: {output_path}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"创建摘要图像失败: {str(e)}")
            raise Exception(f"创建摘要图像失败: {str(e)}")
    
    def export_detection_results(
        self,
        task: DetectionTask,
        file_record: FileRecord,
        result_data: Dict[str, Any],
        format: str = "json"
    ) -> str:
        """导出检测结果"""
        try:
            # 准备导出数据
            export_data = {
                "task_info": {
                    "task_id": task.id,
                    "task_name": task.task_name,
                    "detection_type": task.detection_type.value,
                    "model_name": task.model_name,
                    "confidence_threshold": task.confidence_threshold,
                    "iou_threshold": task.iou_threshold,
                    "created_at": task.created_at.isoformat(),
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                    "processing_time": task.processing_time
                },
                "file_info": {
                    "filename": file_record.filename,
                    "file_type": file_record.file_type.value,
                    "file_size": file_record.file_size,
                    "width": file_record.width,
                    "height": file_record.height,
                    "duration": file_record.duration,
                    "uploaded_at": file_record.uploaded_at.isoformat()
                },
                "detection_results": result_data,
                "export_info": {
                    "format": format,
                    "exported_at": datetime.utcnow().isoformat(),
                    "version": "1.0"
                }
            }
            
            # 生成输出文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = f"{task.task_name}_{timestamp}"
            
            if format.lower() == "json":
                output_path = str(self.output_dir / f"{base_filename}.json")
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            elif format.lower() == "csv":
                import csv
                output_path = str(self.output_dir / f"{base_filename}.csv")
                
                # 导出检测结果为CSV
                detections = result_data.get("detections", [])
                if file_record.is_video:
                    # 视频检测结果
                    frame_detections = result_data.get("frame_detections", [])
                    with open(output_path, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerow([
                            'frame_id', 'timestamp', 'class_id', 'class_name',
                            'confidence', 'x1', 'y1', 'x2', 'y2'
                        ])
                        
                        for frame_data in frame_detections:
                            frame_id = frame_data.get("frame_id", 0)
                            timestamp = frame_data.get("timestamp", 0)
                            for detection in frame_data.get("detections", []):
                                bbox = detection.get("bbox", [0, 0, 0, 0])
                                writer.writerow([
                                    frame_id, timestamp,
                                    detection.get("class_id", 0),
                                    detection.get("class_name", ""),
                                    detection.get("confidence", 0),
                                    bbox[0], bbox[1], bbox[2], bbox[3]
                                ])
                else:
                    # 图像检测结果
                    with open(output_path, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerow([
                            'detection_id', 'class_id', 'class_name',
                            'confidence', 'x1', 'y1', 'x2', 'y2', 'area'
                        ])
                        
                        for detection in detections:
                            bbox = detection.get("bbox", [0, 0, 0, 0])
                            writer.writerow([
                                detection.get("id", 0),
                                detection.get("class_id", 0),
                                detection.get("class_name", ""),
                                detection.get("confidence", 0),
                                bbox[0], bbox[1], bbox[2], bbox[3],
                                detection.get("area", 0)
                            ])
            
            elif format.lower() == "xml":
                import xml.etree.ElementTree as ET
                output_path = str(self.output_dir / f"{base_filename}.xml")
                
                # 创建XML结构
                root = ET.Element("detection_results")
                
                # 任务信息
                task_elem = ET.SubElement(root, "task_info")
                for key, value in export_data["task_info"].items():
                    elem = ET.SubElement(task_elem, key)
                    elem.text = str(value) if value is not None else ""
                
                # 文件信息
                file_elem = ET.SubElement(root, "file_info")
                for key, value in export_data["file_info"].items():
                    elem = ET.SubElement(file_elem, key)
                    elem.text = str(value) if value is not None else ""
                
                # 检测结果
                results_elem = ET.SubElement(root, "detections")
                detections = result_data.get("detections", [])
                for detection in detections:
                    det_elem = ET.SubElement(results_elem, "detection")
                    for key, value in detection.items():
                        elem = ET.SubElement(det_elem, key)
                        elem.text = str(value) if value is not None else ""
                
                # 保存XML
                tree = ET.ElementTree(root)
                tree.write(output_path, encoding='utf-8', xml_declaration=True)
            
            else:
                raise Exception(f"不支持的导出格式: {format}")
            
            logger.info(f"检测结果导出至: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"导出检测结果失败: {str(e)}")
            raise Exception(f"导出检测结果失败: {str(e)}")
    
    def create_visualization_for_task(
        self,
        task: DetectionTask,
        file_record: FileRecord,
        result_data: Dict[str, Any],
        progress_callback: Optional[callable] = None
    ) -> Dict[str, str]:
        """为检测任务创建可视化结果"""
        try:
            visualization_paths = {}
            
            if progress_callback:
                progress_callback(10, "开始创建可视化")
            
            if file_record.is_image:
                # 图像可视化
                detections = result_data.get("detections", [])
                if detections:
                    viz_path = self.visualize_image_detections(
                        file_record.file_path,
                        detections
                    )
                    visualization_paths["main"] = viz_path
                
                if progress_callback:
                    progress_callback(60, "图像可视化完成")
                
                # 创建摘要图像
                summary_path = self.create_detection_summary_image(
                    detections,
                    result_data.get("image_info", {})
                )
                visualization_paths["summary"] = summary_path
                
            elif file_record.is_video:
                # 视频可视化
                frame_detections = result_data.get("frame_detections", [])
                if frame_detections:
                    def video_progress(progress, step):
                        if progress_callback:
                            mapped_progress = 10 + (progress * 0.7)
                            progress_callback(mapped_progress, step)
                    
                    viz_path = self.visualize_video_detections(
                        file_record.file_path,
                        frame_detections,
                        progress_callback=video_progress
                    )
                    visualization_paths["main"] = viz_path
            
            if progress_callback:
                progress_callback(90, "导出检测结果")
            
            # 导出JSON结果
            json_path = self.export_detection_results(
                task, file_record, result_data, "json"
            )
            visualization_paths["json"] = json_path
            
            # 导出CSV结果
            csv_path = self.export_detection_results(
                task, file_record, result_data, "csv"
            )
            visualization_paths["csv"] = csv_path
            
            if progress_callback:
                progress_callback(100, "可视化创建完成")
            
            logger.info(f"任务 {task.id} 可视化创建完成: {visualization_paths}")
            return visualization_paths
            
        except Exception as e:
            logger.error(f"创建任务可视化失败: {str(e)}")
            raise e
    
    def cleanup_old_visualizations(self, max_age_days: int = 7) -> Dict[str, Any]:
        """清理旧的可视化文件"""
        try:
            from datetime import timedelta
            
            cleanup_stats = {
                "deleted_files": 0,
                "freed_space_bytes": 0,
                "errors": []
            }
            
            cutoff_time = datetime.now() - timedelta(days=max_age_days)
            
            # 清理可视化目录
            for file_path in self.visualization_dir.rglob('*'):
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
            
            # 清理输出目录
            for file_path in self.output_dir.rglob('*'):
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
            
            logger.info(f"可视化文件清理完成: {cleanup_stats}")
            return cleanup_stats
            
        except Exception as e:
            logger.error(f"清理可视化文件失败: {str(e)}")
            return {"error": str(e)}