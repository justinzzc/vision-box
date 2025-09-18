#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库初始化脚本
"""

import asyncio
import logging
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from app.core.database import engine, SessionLocal, Base
from app.core.config import get_settings
from app.models import get_all_models, User, FileRecord, DetectionTask
from app.core.security import get_password_hash
import uuid
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()


async def create_tables():
    """创建数据库表"""
    try:
        logger.info("开始创建数据库表...")
        
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        
        logger.info("数据库表创建成功")
        return True
        
    except SQLAlchemyError as e:
        logger.error(f"创建数据库表失败: {e}")
        return False
    except Exception as e:
        logger.error(f"创建数据库表时发生未知错误: {e}")
        return False


async def drop_tables():
    """删除数据库表"""
    try:
        logger.info("开始删除数据库表...")
        
        # 删除所有表
        Base.metadata.drop_all(bind=engine)
        
        logger.info("数据库表删除成功")
        return True
        
    except SQLAlchemyError as e:
        logger.error(f"删除数据库表失败: {e}")
        return False
    except Exception as e:
        logger.error(f"删除数据库表时发生未知错误: {e}")
        return False


async def create_default_admin():
    """创建默认管理员用户"""
    try:
        db = SessionLocal()
        
        # 检查是否已存在管理员
        existing_admin = db.query(User).filter(User.username == "admin").first()
        if existing_admin:
            logger.info("管理员用户已存在，跳过创建")
            db.close()
            return True
        
        # 创建管理员用户
        admin_user = User(
            id=str(uuid.uuid4()),
            username="admin",
            email="admin@visionbox.com",
            password_hash=get_password_hash("admin123"),
            full_name="系统管理员",
            is_active=True,
            is_superuser=True,
            is_verified=True,
            bio="Vision Box 系统管理员",
            created_at=datetime.utcnow()
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        logger.info(f"管理员用户创建成功: {admin_user.username} (ID: {admin_user.id})")
        db.close()
        return True
        
    except SQLAlchemyError as e:
        logger.error(f"创建管理员用户失败: {e}")
        if 'db' in locals():
            db.rollback()
            db.close()
        return False
    except Exception as e:
        logger.error(f"创建管理员用户时发生未知错误: {e}")
        if 'db' in locals():
            db.rollback()
            db.close()
        return False


async def create_sample_data():
    """创建示例数据"""
    try:
        db = SessionLocal()
        
        # 检查是否已有数据
        existing_tasks = db.query(DetectionTask).count()
        if existing_tasks > 0:
            logger.info("示例数据已存在，跳过创建")
            db.close()
            return True
        
        # 获取管理员用户
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            logger.warning("未找到管理员用户，跳过创建示例数据")
            db.close()
            return False
        
        # 创建示例文件记录
        sample_files = [
            {
                "filename": "sample_image.jpg",
                "stored_filename": "sample_image_001.jpg",
                "file_path": "/uploads/sample_image_001.jpg",
                "file_type": "image",
                "file_size": 1024000,
                "mime_type": "image/jpeg",
                "width": 1920,
                "height": 1080
            },
            {
                "filename": "sample_video.mp4",
                "stored_filename": "sample_video_001.mp4",
                "file_path": "/uploads/sample_video_001.mp4",
                "file_type": "video",
                "file_size": 10240000,
                "mime_type": "video/mp4",
                "width": 1280,
                "height": 720,
                "duration": 30,
                "fps": 25
            }
        ]
        
        file_records = []
        for file_data in sample_files:
            file_record = FileRecord(
                id=str(uuid.uuid4()),
                **file_data,
                uploaded_at=datetime.utcnow()
            )
            db.add(file_record)
            file_records.append(file_record)
        
        db.commit()
        
        # 创建示例检测任务
        sample_tasks = [
            {
                "task_name": "图像目标检测示例",
                "description": "使用YOLOv8模型进行目标检测",
                "detection_type": "object_detection",
                "model_name": "yolov8n",
                "confidence_threshold": 0.5,
                "file_record": file_records[0]
            },
            {
                "task_name": "视频目标检测示例",
                "description": "对视频进行逐帧目标检测",
                "detection_type": "object_detection",
                "model_name": "yolov8s",
                "confidence_threshold": 0.6,
                "file_record": file_records[1]
            }
        ]
        
        for task_data in sample_tasks:
            file_record = task_data.pop("file_record")
            detection_task = DetectionTask(
                id=str(uuid.uuid4()),
                user_id=admin_user.id,
                file_record_id=file_record.id,
                **task_data,
                created_at=datetime.utcnow()
            )
            db.add(detection_task)
        
        db.commit()
        
        logger.info("示例数据创建成功")
        db.close()
        return True
        
    except SQLAlchemyError as e:
        logger.error(f"创建示例数据失败: {e}")
        if 'db' in locals():
            db.rollback()
            db.close()
        return False
    except Exception as e:
        logger.error(f"创建示例数据时发生未知错误: {e}")
        if 'db' in locals():
            db.rollback()
            db.close()
        return False


async def check_database_connection():
    """检查数据库连接"""
    try:
        db = SessionLocal()
        
        # 执行简单查询测试连接
        result = db.execute(text("SELECT 1"))
        result.fetchone()
        
        logger.info("数据库连接正常")
        db.close()
        return True
        
    except SQLAlchemyError as e:
        logger.error(f"数据库连接失败: {e}")
        return False
    except Exception as e:
        logger.error(f"检查数据库连接时发生未知错误: {e}")
        return False


async def get_database_info():
    """获取数据库信息"""
    try:
        db = SessionLocal()
        
        # 获取表信息
        tables_info = {}
        for model in get_all_models():
            table_name = model.__tablename__
            count = db.query(model).count()
            tables_info[table_name] = count
        
        logger.info(f"数据库表信息: {tables_info}")
        db.close()
        return tables_info
        
    except SQLAlchemyError as e:
        logger.error(f"获取数据库信息失败: {e}")
        return {}
    except Exception as e:
        logger.error(f"获取数据库信息时发生未知错误: {e}")
        return {}


async def init_database(create_sample: bool = True):
    """初始化数据库"""
    logger.info("开始初始化数据库...")
    
    # 检查数据库连接
    if not await check_database_connection():
        logger.error("数据库连接失败，初始化中止")
        return False
    
    # 创建表
    if not await create_tables():
        logger.error("创建数据库表失败，初始化中止")
        return False
    
    # 创建默认管理员
    if not await create_default_admin():
        logger.error("创建默认管理员失败，初始化中止")
        return False
    
    # 创建示例数据（可选）
    if create_sample:
        if not await create_sample_data():
            logger.warning("创建示例数据失败，但不影响系统运行")
    
    # 显示数据库信息
    await get_database_info()
    
    logger.info("数据库初始化完成")
    return True


async def reset_database():
    """重置数据库（删除所有表并重新创建）"""
    logger.info("开始重置数据库...")
    
    # 删除所有表
    if not await drop_tables():
        logger.error("删除数据库表失败，重置中止")
        return False
    
    # 重新初始化
    return await init_database()


if __name__ == "__main__":
    import sys
    
    async def main():
        if len(sys.argv) > 1:
            command = sys.argv[1]
            if command == "reset":
                await reset_database()
            elif command == "init":
                await init_database()
            elif command == "check":
                await check_database_connection()
                await get_database_info()
            else:
                print("可用命令: init, reset, check")
        else:
            await init_database()
    
    asyncio.run(main())