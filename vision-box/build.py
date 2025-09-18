#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视觉检测应用统一构建脚本
支持Docker和Windows应用的构建和部署
"""

import os
import subprocess
import shutil
import sys
import argparse
from pathlib import Path


def build_frontend():
    """构建前端应用"""
    print("🔨 构建前端应用...")
    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        print("❌ 前端目录不存在")
        return False
    
    os.chdir(frontend_dir)
    try:
        subprocess.run(['npm', 'install'], check=True)
        subprocess.run(['npm', 'run', 'build'], check=True)
        print("✅ 前端构建完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 前端构建失败: {e}")
        return False
    finally:
        os.chdir('..')


def build_backend():
    """构建后端应用"""
    print("🔨 构建后端应用...")
    backend_dir = Path("backend")
    if not backend_dir.exists():
        print("❌ 后端目录不存在")
        return False
    
    os.chdir(backend_dir)
    try:
        subprocess.run([sys.executable, 'build_backend.py'], check=True)
        print("✅ 后端构建完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 后端构建失败: {e}")
        return False
    finally:
        os.chdir('..')


def build_docker():
    """构建Docker镜像"""
    print("🐳 构建Docker镜像...")
    try:
        subprocess.run(['docker-compose', 'build'], check=True)
        print("✅ Docker镜像构建完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Docker构建失败: {e}")
        return False


def build_windows_app():
    """构建Windows桌面应用"""
    print("🖥️ 构建Windows桌面应用...")
    
    desktop_dir = Path("desktop")
    if not desktop_dir.exists():
        print("❌ 桌面应用目录不存在")
        return False
    
    # 复制前端构建文件
    frontend_dist = desktop_dir / "frontend"
    if frontend_dist.exists():
        shutil.rmtree(frontend_dist)
    
    frontend_build = Path("frontend/dist")
    if frontend_build.exists():
        shutil.copytree(frontend_build, frontend_dist)
    
    # 复制后端可执行文件
    backend_dist = desktop_dir / "backend"
    if backend_dist.exists():
        shutil.rmtree(backend_dist)
    backend_dist.mkdir()
    
    backend_exe = Path("backend/dist/vision_app.exe")
    if backend_exe.exists():
        shutil.copy(backend_exe, backend_dist / "vision_app.exe")
    
    # 构建Electron应用
    os.chdir(desktop_dir)
    try:
        subprocess.run(['npm', 'install'], check=True)
        subprocess.run(['npm', 'run', 'build'], check=True)
        print("✅ Windows应用构建完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Windows应用构建失败: {e}")
        return False
    finally:
        os.chdir('..')


def create_data_directories():
    """创建必要的数据目录"""
    print("📁 创建数据目录...")
    directories = [
        "data",
        "data/uploads",
        "data/results",
        "data/models"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("✅ 数据目录创建完成")


def main():
    parser = argparse.ArgumentParser(description='构建视觉检测应用')
    parser.add_argument('--target', choices=['docker', 'windows', 'all'], 
                       default='all', help='构建目标')
    parser.add_argument('--skip-frontend', action='store_true', 
                       help='跳过前端构建')
    parser.add_argument('--skip-backend', action='store_true', 
                       help='跳过后端构建')
    
    args = parser.parse_args()
    
    print("🚀 开始构建视觉检测应用")
    print(f"📋 构建目标: {args.target}")
    
    # 创建数据目录
    create_data_directories()
    
    success = True
    
    if args.target in ['docker', 'all']:
        if not args.skip_frontend:
            success &= build_frontend()
        if success:
            success &= build_docker()
    
    if args.target in ['windows', 'all']:
        if not args.skip_frontend:
            success &= build_frontend()
        if not args.skip_backend:
            success &= build_backend()
        if success:
            success &= build_windows_app()
    
    if success:
        print("🎉 构建完成！")
        if args.target in ['docker', 'all']:
            print("🐳 Docker部署: docker-compose up -d")
        if args.target in ['windows', 'all']:
            print("🖥️ Windows应用: desktop/dist/")
    else:
        print("❌ 构建失败")
        sys.exit(1)


if __name__ == '__main__':
    main()