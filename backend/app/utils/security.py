#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全工具模块
提供密码哈希、JWT令牌等安全功能
"""

from datetime import datetime, timedelta
from typing import Optional, Union
from passlib.context import CryptContext
from jose import JWTError, jwt
from loguru import logger

from app.core.config import settings

# 密码上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT配置
ALGORITHM = "HS256"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"密码验证失败: {e}")
        return False


def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    try:
        return pwd_context.hash(password)
    except Exception as e:
        logger.error(f"密码哈希生成失败: {e}")
        raise


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建访问令牌"""
    try:
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
        
        return encoded_jwt
    except Exception as e:
        logger.error(f"创建访问令牌失败: {e}")
        raise


def verify_token(token: str) -> Optional[dict]:
    """验证令牌"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        logger.warning(f"令牌验证失败: {e}")
        return None
    except Exception as e:
        logger.error(f"令牌验证错误: {e}")
        return None


def get_user_id_from_token(token: str) -> Optional[str]:
    """从令牌中获取用户ID"""
    payload = verify_token(token)
    if payload:
        return payload.get("sub")
    return None


def create_refresh_token(user_id: str) -> str:
    """创建刷新令牌"""
    try:
        data = {"sub": user_id, "type": "refresh"}
        expires_delta = timedelta(days=7)  # 刷新令牌7天有效
        return create_access_token(data, expires_delta)
    except Exception as e:
        logger.error(f"创建刷新令牌失败: {e}")
        raise


def verify_refresh_token(token: str) -> Optional[str]:
    """验证刷新令牌并返回用户ID"""
    payload = verify_token(token)
    if payload and payload.get("type") == "refresh":
        return payload.get("sub")
    return None


def generate_api_key() -> str:
    """生成API密钥"""
    import secrets
    import string
    
    alphabet = string.ascii_letters + string.digits
    api_key = ''.join(secrets.choice(alphabet) for _ in range(32))
    return f"vd_{api_key}"  # vd = vision detection


def hash_api_key(api_key: str) -> str:
    """哈希API密钥"""
    return get_password_hash(api_key)


def verify_api_key(plain_api_key: str, hashed_api_key: str) -> bool:
    """验证API密钥"""
    return verify_password(plain_api_key, hashed_api_key)


def generate_file_token(file_id: str, expires_minutes: int = 60) -> str:
    """生成文件访问令牌"""
    try:
        data = {
            "file_id": file_id,
            "type": "file_access"
        }
        expires_delta = timedelta(minutes=expires_minutes)
        return create_access_token(data, expires_delta)
    except Exception as e:
        logger.error(f"生成文件令牌失败: {e}")
        raise


def verify_file_token(token: str) -> Optional[str]:
    """验证文件访问令牌并返回文件ID"""
    payload = verify_token(token)
    if payload and payload.get("type") == "file_access":
        return payload.get("file_id")
    return None


def sanitize_filename(filename: str) -> str:
    """清理文件名，移除危险字符"""
    import re
    import os
    
    # 移除路径分隔符和其他危险字符
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # 移除控制字符
    filename = ''.join(char for char in filename if ord(char) >= 32)
    
    # 限制文件名长度
    name, ext = os.path.splitext(filename)
    if len(name) > 200:
        name = name[:200]
    
    return name + ext


def generate_secure_filename(original_filename: str) -> str:
    """生成安全的文件名"""
    import uuid
    import os
    
    # 获取文件扩展名
    _, ext = os.path.splitext(original_filename)
    
    # 生成UUID作为文件名
    secure_name = str(uuid.uuid4())
    
    return secure_name + ext.lower()


def check_file_security(file_path: str) -> bool:
    """检查文件安全性"""
    import os
    from pathlib import Path
    
    try:
        # 检查文件是否存在
        if not os.path.exists(file_path):
            return False
        
        # 检查是否为文件（不是目录）
        if not os.path.isfile(file_path):
            return False
        
        # 检查文件大小
        file_size = os.path.getsize(file_path)
        if file_size > settings.MAX_FILE_SIZE:
            return False
        
        # 检查文件扩展名
        file_ext = Path(file_path).suffix.lower().lstrip('.')
        if file_ext not in settings.all_supported_formats:
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"文件安全检查失败: {e}")
        return False


def rate_limit_key(identifier: str, endpoint: str) -> str:
    """生成速率限制键"""
    return f"rate_limit:{identifier}:{endpoint}"


def generate_csrf_token() -> str:
    """生成CSRF令牌"""
    import secrets
    return secrets.token_urlsafe(32)


def verify_csrf_token(token: str, expected_token: str) -> bool:
    """验证CSRF令牌"""
    import hmac
    return hmac.compare_digest(token, expected_token)


class SecurityHeaders:
    """安全头部类"""
    
    @staticmethod
    def get_security_headers() -> dict:
        """获取安全头部"""
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'",
            "Referrer-Policy": "strict-origin-when-cross-origin"
        }


if __name__ == "__main__":
    # 测试代码
    password = "test123"
    hashed = get_password_hash(password)
    print(f"原密码: {password}")
    print(f"哈希值: {hashed}")
    print(f"验证结果: {verify_password(password, hashed)}")
    
    # 测试JWT
    token = create_access_token({"sub": "user123"})
    print(f"JWT令牌: {token}")
    print(f"验证结果: {verify_token(token)}")