#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库配置和连接管理
"""

import asyncio
from typing import AsyncGenerator
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base, sessionmaker
from loguru import logger

from .config import settings

# 创建基础模型类
Base = declarative_base()

# 元数据
metadata = MetaData()

# 数据库引擎
if settings.DATABASE_URL.startswith("sqlite"):
    # SQLite配置
    SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL
    
    # 同步引擎
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=settings.DEBUG
    )
    
    # 异步引擎（SQLite使用aiosqlite）
    async_database_url = SQLALCHEMY_DATABASE_URL.replace("sqlite:///", "sqlite+aiosqlite:///")
    async_engine = create_async_engine(
        async_database_url,
        echo=settings.DEBUG,
        future=True
    )
else:
    # 其他数据库配置
    engine = create_engine(settings.DATABASE_URL, echo=settings.DEBUG)
    async_engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG)

# 会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"数据库会话错误: {e}")
            raise
        finally:
            await session.close()


def get_sync_db():
    """获取同步数据库会话"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        logger.error(f"同步数据库会话错误: {e}")
        raise
    finally:
        db.close()


async def init_db():
    """初始化数据库"""
    try:
        logger.info("开始初始化数据库...")
        
        # 导入所有模型以确保它们被注册
        from app.models import user, file_record, detection_task
        
        # 创建所有表
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("数据库表创建完成")
        
        # 创建初始数据
        await create_initial_data()
        
        logger.info("数据库初始化完成")
        
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise


async def create_initial_data():
    """创建初始数据"""
    try:
        async with AsyncSessionLocal() as session:
            # 检查是否已有用户数据
            from app.models.user import User
            from sqlalchemy import select
            
            result = await session.execute(select(User))
            existing_users = result.scalars().all()
            
            if not existing_users:
                # 创建默认管理员用户
                from app.utils.security import get_password_hash
                
                admin_user = User(
                    username="admin",
                    email="admin@example.com",
                    password_hash=get_password_hash("admin123"),
                    is_active=True,
                    is_superuser=True
                )
                
                demo_user = User(
                    username="demo",
                    email="demo@example.com",
                    password_hash=get_password_hash("demo123"),
                    is_active=True,
                    is_superuser=False
                )
                
                session.add(admin_user)
                session.add(demo_user)
                await session.commit()
                
                logger.info("创建默认用户完成")
                logger.info("管理员账号: admin / admin123")
                logger.info("演示账号: demo / demo123")
            
    except Exception as e:
        logger.error(f"创建初始数据失败: {e}")
        # 不抛出异常，允许应用继续启动


async def check_db_connection():
    """检查数据库连接"""
    try:
        async with AsyncSessionLocal() as session:
            await session.execute("SELECT 1")
        logger.info("数据库连接正常")
        return True
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        return False


async def close_db():
    """关闭数据库连接"""
    try:
        await async_engine.dispose()
        logger.info("数据库连接已关闭")
    except Exception as e:
        logger.error(f"关闭数据库连接失败: {e}")


def create_tables():
    """同步创建数据库表（用于开发和测试）"""
    try:
        # 导入所有模型
        from app.models import user, file_record, detection_task
        
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        logger.info("同步创建数据库表完成")
        
    except Exception as e:
        logger.error(f"同步创建数据库表失败: {e}")
        raise


def drop_tables():
    """删除所有数据库表（谨慎使用）"""
    try:
        Base.metadata.drop_all(bind=engine)
        logger.warning("所有数据库表已删除")
    except Exception as e:
        logger.error(f"删除数据库表失败: {e}")
        raise


if __name__ == "__main__":
    # 用于直接运行此文件进行数据库初始化
    asyncio.run(init_db())