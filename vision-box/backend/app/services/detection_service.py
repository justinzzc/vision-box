#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视觉检测服务模块
集成supervision库实现视觉检测功能
"""

import os
import cv2
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from pathlib import Path
import logging
from datetime import datetime

try:
    import supervision as sv
    from ultralytics import YOLO
    SUPERVISION_AVAILABLE = True
except ImportError:
    SUPERVISION_AVAILABLE = False
    logging.warning("Supervision或YOLO库未安装，将使用模拟检测")

from app.core.config import get_settings
from app.models import DetectionTask, FileRecord, DetectionType

settings = get_settings()
logger = logging.getLogger(__name__)


class DetectionService:
    """视觉检测服务类"""
    
    def __init__(self):
        self.models_cache = {}  # 模型缓存
        self.supported_models = {
            "yolov8n": "yolov8n.pt",
            "yolov8s": "yolov8s.pt",
            "yolov8m": "yolov8m.pt",
            "yolov8l": "yolov8l.pt",
            "yolov8x": "yolov8x.pt"
        }
        
        # COCO类别名称
        self.coco_classes = [
            "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck",
            "boat", "traffic light", "fire hydrant", "stop sign", "parking meter", "bench",
            "bird", "cat", "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra",
            "giraffe", "backpack", "umbrella", "handbag", "tie", "suitcase", "frisbee",
            "skis", "snowboard", "sports ball", "kite", "baseball bat", "baseball glove",
            "skateboard", "surfboard", "tennis racket", "bottle", "wine glass", "cup",
            "fork", "knife", "spoon", "bowl", "banana", "apple", "sandwich", "orange",
            "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair", "couch",
            "potted plant", "bed", "dining table", "toilet", "tv", "laptop", "mouse",
            "remote", "keyboard", "cell phone", "microwave", "oven", "toaster", "sink",
            "refrigerator", "book", "clock", "vase", "scissors", "teddy bear", "hair drier",
            "toothbrush"
        ]
    
    def load_model(self, model_name: str) -> Optional[Any]:
        """加载模型"""
        if not SUPERVISION_AVAILABLE:
            logger.warning(f"Supervision库不可用，无法加载模型 {model_name}")
            return None
        
        if model_name in self.models_cache:
            return self.models_cache[model_name]
        
        try:
            if model_name not in self.supported_models:
                raise ValueError(f"不支持的模型: {model_name}")
            
            model_file = self.supported_models[model_name]
            model = YOLO(model_file)
            
            # 缓存模型
            self.models_cache[model_name] = model
            logger.info(f"模型 {model_name} 加载成功")
            
            return model
            
        except Exception as e:
            logger.error(f"加载模型 {model_name} 失败: {str(e)}")
            return None
    
    def detect_objects(
        self,
        image_path: str,
        model_name: str = "yolov8n",
        confidence_threshold: float = 0.5,
        iou_threshold: float = 0.5,
        max_detections: int = 100
    ) -> Dict[str, Any]:
        """目标检测"""
        try:
            if not SUPERVISION_AVAILABLE:
                return self._simulate_detection(image_path, "object_detection")
            
            # 加载模型
            model = self.load_model(model_name)
            if model is None:
                raise Exception(f"无法加载模型 {model_name}")
            
            # 读取图像
            image = cv2.imread(image_path)
            if image is None:
                raise Exception(f"无法读取图像: {image_path}")
            
            # 执行检测
            results = model(image, conf=confidence_threshold, iou=iou_threshold, max_det=max_detections)
            
            # 解析结果
            detections = []
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for i, box in enumerate(boxes):
                        # 获取边界框坐标
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        confidence = float(box.conf[0].cpu().numpy())
                        class_id = int(box.cls[0].cpu().numpy())
                        
                        # 获取类别名称
                        class_name = self.coco_classes[class_id] if class_id < len(self.coco_classes) else f"class_{class_id}"
                        
                        detection = {
                            "id": i,
                            "class_id": class_id,
                            "class_name": class_name,
                            "confidence": round(confidence, 3),
                            "bbox": [int(x1), int(y1), int(x2), int(y2)],
                            "area": int((x2 - x1) * (y2 - y1)),
                            "center": [int((x1 + x2) / 2), int((y1 + y2) / 2)]
                        }
                        detections.append(detection)
            
            # 统计信息
            class_counts = {}
            for detection in detections:
                class_name = detection["class_name"]
                class_counts[class_name] = class_counts.get(class_name, 0) + 1
            
            result_data = {
                "detections": detections,
                "total_detections": len(detections),
                "class_counts": class_counts,
                "image_info": {
                    "width": image.shape[1],
                    "height": image.shape[0],
                    "channels": image.shape[2]
                },
                "processing_info": {
                    "model_used": model_name,
                    "confidence_threshold": confidence_threshold,
                    "iou_threshold": iou_threshold,
                    "max_detections": max_detections
                }
            }
            
            return result_data
            
        except Exception as e:
            logger.error(f"目标检测失败: {str(e)}")
            raise Exception(f"目标检测失败: {str(e)}")
    
    def detect_video(
        self,
        video_path: str,
        model_name: str = "yolov8n",
        confidence_threshold: float = 0.5,
        iou_threshold: float = 0.5,
        max_detections: int = 100,
        frame_skip: int = 1,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """视频目标检测"""
        try:
            if not SUPERVISION_AVAILABLE:
                return self._simulate_detection(video_path, "video_detection")
            
            # 加载模型
            model = self.load_model(model_name)
            if model is None:
                raise Exception(f"无法加载模型 {model_name}")
            
            # 打开视频
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise Exception(f"无法打开视频: {video_path}")
            
            # 获取视频信息
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            frame_detections = []
            frame_count = 0
            processed_frames = 0
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # 跳帧处理
                if frame_count % (frame_skip + 1) != 0:
                    frame_count += 1
                    continue
                
                # 执行检测
                results = model(frame, conf=confidence_threshold, iou=iou_threshold, max_det=max_detections)
                
                # 解析当前帧的检测结果
                frame_result = {
                    "frame_id": processed_frames,
                    "timestamp": processed_frames / fps,
                    "detections": []
                }
                
                for result in results:
                    boxes = result.boxes
                    if boxes is not None:
                        for box in boxes:
                            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                            confidence = float(box.conf[0].cpu().numpy())
                            class_id = int(box.cls[0].cpu().numpy())
                            class_name = self.coco_classes[class_id] if class_id < len(self.coco_classes) else f"class_{class_id}"
                            
                            detection = {
                                "class_id": class_id,
                                "class_name": class_name,
                                "confidence": round(confidence, 3),
                                "bbox": [int(x1), int(y1), int(x2), int(y2)]
                            }
                            frame_result["detections"].append(detection)
                
                frame_detections.append(frame_result)
                processed_frames += 1
                frame_count += 1
                
                # 进度回调
                if progress_callback:
                    progress = (processed_frames / (total_frames // (frame_skip + 1))) * 100
                    progress_callback(progress, f"处理第 {processed_frames} 帧")
            
            cap.release()
            
            # 统计信息
            total_detections = sum(len(frame["detections"]) for frame in frame_detections)
            all_classes = set()
            for frame in frame_detections:
                for detection in frame["detections"]:
                    all_classes.add(detection["class_name"])
            
            result_data = {
                "frame_detections": frame_detections,
                "total_frames_processed": processed_frames,
                "total_detections": total_detections,
                "unique_classes": list(all_classes),
                "video_info": {
                    "total_frames": total_frames,
                    "fps": fps,
                    "width": width,
                    "height": height,
                    "duration": total_frames / fps
                },
                "processing_info": {
                    "model_used": model_name,
                    "confidence_threshold": confidence_threshold,
                    "iou_threshold": iou_threshold,
                    "frame_skip": frame_skip
                }
            }
            
            return result_data
            
        except Exception as e:
            logger.error(f"视频检测失败: {str(e)}")
            raise Exception(f"视频检测失败: {str(e)}")
    
    def _simulate_detection(self, file_path: str, detection_type: str) -> Dict[str, Any]:
        """模拟检测结果（当supervision库不可用时）"""
        logger.info(f"使用模拟检测: {file_path}")
        
        # 模拟检测结果
        if detection_type == "object_detection":
            return {
                "detections": [
                    {
                        "id": 0,
                        "class_id": 0,
                        "class_name": "person",
                        "confidence": 0.85,
                        "bbox": [100, 100, 200, 300],
                        "area": 20000,
                        "center": [150, 200]
                    },
                    {
                        "id": 1,
                        "class_id": 2,
                        "class_name": "car",
                        "confidence": 0.92,
                        "bbox": [300, 150, 500, 350],
                        "area": 40000,
                        "center": [400, 250]
                    }
                ],
                "total_detections": 2,
                "class_counts": {"person": 1, "car": 1},
                "image_info": {"width": 640, "height": 480, "channels": 3},
                "processing_info": {
                    "model_used": "simulated",
                    "confidence_threshold": 0.5,
                    "iou_threshold": 0.5,
                    "note": "这是模拟结果，请安装supervision库获得真实检测"
                }
            }
        
        elif detection_type == "video_detection":
            return {
                "frame_detections": [
                    {
                        "frame_id": 0,
                        "timestamp": 0.0,
                        "detections": [
                            {
                                "class_id": 0,
                                "class_name": "person",
                                "confidence": 0.85,
                                "bbox": [100, 100, 200, 300]
                            }
                        ]
                    },
                    {
                        "frame_id": 1,
                        "timestamp": 0.04,
                        "detections": [
                            {
                                "class_id": 2,
                                "class_name": "car",
                                "confidence": 0.92,
                                "bbox": [300, 150, 500, 350]
                            }
                        ]
                    }
                ],
                "total_frames_processed": 2,
                "total_detections": 2,
                "unique_classes": ["person", "car"],
                "video_info": {
                    "total_frames": 100,
                    "fps": 25.0,
                    "width": 640,
                    "height": 480,
                    "duration": 4.0
                },
                "processing_info": {
                    "model_used": "simulated",
                    "confidence_threshold": 0.5,
                    "iou_threshold": 0.5,
                    "frame_skip": 1,
                    "note": "这是模拟结果，请安装supervision库获得真实检测"
                }
            }
        
        return {"error": "未知的检测类型"}
    
    def process_detection_task(
        self,
        task: DetectionTask,
        file_record: FileRecord,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """处理检测任务"""
        try:
            file_path = file_record.file_path
            
            if not os.path.exists(file_path):
                raise Exception(f"文件不存在: {file_path}")
            
            # 根据文件类型选择检测方法
            if file_record.is_image:
                if progress_callback:
                    progress_callback(20, "开始图像检测")
                
                result_data = self.detect_objects(
                    image_path=file_path,
                    model_name=task.model_name,
                    confidence_threshold=task.confidence_threshold,
                    iou_threshold=task.iou_threshold,
                    max_detections=task.max_detections
                )
                
                if progress_callback:
                    progress_callback(80, "图像检测完成")
            
            elif file_record.is_video:
                if progress_callback:
                    progress_callback(20, "开始视频检测")
                
                def video_progress(progress, step):
                    if progress_callback:
                        # 将视频处理进度映射到20-80%
                        mapped_progress = 20 + (progress * 0.6)
                        progress_callback(mapped_progress, step)
                
                result_data = self.detect_video(
                    video_path=file_path,
                    model_name=task.model_name,
                    confidence_threshold=task.confidence_threshold,
                    iou_threshold=task.iou_threshold,
                    max_detections=task.max_detections,
                    frame_skip=1,  # 可以根据需要调整
                    progress_callback=video_progress
                )
                
                if progress_callback:
                    progress_callback(80, "视频检测完成")
            
            else:
                raise Exception(f"不支持的文件类型: {file_record.file_type}")
            
            # 生成结果摘要
            if file_record.is_image:
                summary = {
                    "total_detections": result_data.get("total_detections", 0),
                    "classes_detected": list(result_data.get("class_counts", {}).keys()),
                    "average_confidence": self._calculate_average_confidence(result_data.get("detections", [])),
                    "file_info": {
                        "filename": file_record.filename,
                        "file_size": file_record.file_size,
                        "dimensions": f"{file_record.width}x{file_record.height}" if file_record.width else None
                    }
                }
            else:  # video
                summary = {
                    "total_frames_processed": result_data.get("total_frames_processed", 0),
                    "total_detections": result_data.get("total_detections", 0),
                    "unique_classes": result_data.get("unique_classes", []),
                    "video_duration": result_data.get("video_info", {}).get("duration", 0),
                    "file_info": {
                        "filename": file_record.filename,
                        "file_size": file_record.file_size,
                        "dimensions": f"{file_record.width}x{file_record.height}" if file_record.width else None
                    }
                }
            
            if progress_callback:
                progress_callback(100, "检测任务完成")
            
            return {
                "result_data": result_data,
                "result_summary": summary
            }
            
        except Exception as e:
            logger.error(f"处理检测任务失败: {str(e)}")
            raise e
    
    def _calculate_average_confidence(self, detections: List[Dict]) -> float:
        """计算平均置信度"""
        if not detections:
            return 0.0
        
        total_confidence = sum(detection.get("confidence", 0) for detection in detections)
        return round(total_confidence / len(detections), 3)
    
    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """获取模型信息"""
        if model_name not in self.supported_models:
            return {"error": f"不支持的模型: {model_name}"}
        
        return {
            "name": model_name,
            "file": self.supported_models[model_name],
            "loaded": model_name in self.models_cache,
            "supported_tasks": ["object_detection"],
            "input_size": [640, 640],
            "classes": len(self.coco_classes),
            "class_names": self.coco_classes
        }
    
    def clear_model_cache(self):
        """清理模型缓存"""
        self.models_cache.clear()
        logger.info("模型缓存已清理")
    
    def is_supervision_available(self) -> bool:
        """检查supervision库是否可用"""
        return SUPERVISION_AVAILABLE