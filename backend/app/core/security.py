#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全相关工具函数
"""

import secrets
from datetime import datetime, timedelta
from typing import Any, Union, Optional

from jose import jwt
from passlib.context import CryptContext
from loguru import logger

from .config import settings

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(
    subject: Union[str, Any], expires_delta: timedelta = None
) -> str:
    """
    创建访问令牌
    
    Args:
        subject: 令牌主题（通常是用户ID或用户名）
        expires_delta: 过期时间增量
    
    Returns:
        JWT令牌字符串
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码
    
    Args:
        plain_password: 明文密码
        hashed_password: 哈希密码
    
    Returns:
        验证结果
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    获取密码哈希
    
    Args:
        password: 明文密码
    
    Returns:
        哈希密码
    """
    return pwd_context.hash(password)


def generate_password_reset_token(email: str) -> str:
    """
    生成密码重置令牌
    
    Args:
        email: 用户邮箱
    
    Returns:
        重置令牌
    """
    delta = timedelta(hours=settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS)
    now = datetime.utcnow()
    expires = now + delta
    exp = expires.timestamp()
    encoded_jwt = jwt.encode(
        {"exp": exp, "nbf": now, "sub": email},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    return encoded_jwt


def verify_password_reset_token(token: str) -> Optional[str]:
    """
    验证密码重置令牌
    
    Args:
        token: 重置令牌
    
    Returns:
        用户邮箱或None
    """
    try:
        decoded_token = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return decoded_token["sub"]
    except jwt.JWTError:
        return None


def verify_token(token: str) -> Optional[str]:
    """
    验证访问令牌
    
    Args:
        token: 访问令牌
    
    Returns:
        用户标识或None
    """
    try:
        decoded_token = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return decoded_token.get("sub")
    except jwt.JWTError:
        return None


def generate_api_key() -> str:
    """
    生成API密钥
    
    Returns:
        API密钥字符串
    """
    return secrets.token_urlsafe(32)


def generate_secure_filename(original_filename: str) -> str:
    """
    生成安全的文件名
    
    Args:
        original_filename: 原始文件名
    
    Returns:
        安全的文件名
    """
    import os
    import re
    from datetime import datetime
    
    # 获取文件扩展名
    name, ext = os.path.splitext(original_filename)
    
    # 清理文件名，只保留字母数字和部分特殊字符
    safe_name = re.sub(r'[^\w\-_\.]', '_', name)
    
    # 限制长度
    if len(safe_name) > 50:
        safe_name = safe_name[:50]
    
    # 添加时间戳确保唯一性
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    random_suffix = secrets.token_hex(4)
    
    return f"{safe_name}_{timestamp}_{random_suffix}{ext}"


def validate_file_type(filename: str, allowed_types: list) -> bool:
    """
    验证文件类型
    
    Args:
        filename: 文件名
        allowed_types: 允许的文件类型列表
    
    Returns:
        验证结果
    """
    import os
    
    if not filename:
        return False
    
    ext = os.path.splitext(filename)[1].lower()
    return ext in allowed_types


def sanitize_input(input_str: str, max_length: int = 1000) -> str:
    """
    清理输入字符串
    
    Args:
        input_str: 输入字符串
        max_length: 最大长度
    
    Returns:
        清理后的字符串
    """
    if not input_str:
        return ""
    
    # 移除潜在的危险字符
    import re
    
    # 移除HTML标签
    clean_str = re.sub(r'<[^>]+>', '', input_str)
    
    # 移除SQL注入相关字符
    dangerous_chars = ['<', '>', '"', "'", '&', ';', '--', '/*', '*/', 'xp_', 'sp_']
    for char in dangerous_chars:
        clean_str = clean_str.replace(char, '')
    
    # 限制长度
    if len(clean_str) > max_length:
        clean_str = clean_str[:max_length]
    
    return clean_str.strip()


def check_rate_limit(user_id: str, action: str, limit: int = 100, window: int = 3600) -> bool:
    """
    检查速率限制（简单实现，生产环境建议使用Redis）
    
    Args:
        user_id: 用户ID
        action: 操作类型
        limit: 限制次数
        window: 时间窗口（秒）
    
    Returns:
        是否允许操作
    """
    # 这里是简单实现，生产环境应该使用Redis或其他缓存系统
    # 暂时返回True，允许所有操作
    return True


def generate_csrf_token() -> str:
    """
    生成CSRF令牌
    
    Returns:
        CSRF令牌
    """
    return secrets.token_urlsafe(32)


def verify_csrf_token(token: str, expected_token: str) -> bool:
    """
    验证CSRF令牌
    
    Args:
        token: 提交的令牌
        expected_token: 期望的令牌
    
    Returns:
        验证结果
    """
    return secrets.compare_digest(token, expected_token)


class SecurityHeaders:
    """
    安全头部工具类
    """
    
    @staticmethod
    def get_security_headers() -> dict:
        """
        获取安全头部
        
        Returns:
            安全头部字典
        """
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'",
            "Referrer-Policy": "strict-origin-when-cross-origin"
        }


def log_security_event(event_type: str, user_id: str = None, details: dict = None):
    """
    记录安全事件
    
    Args:
        event_type: 事件类型
        user_id: 用户ID
        details: 事件详情
    """
    log_data = {
        "event_type": event_type,
        "user_id": user_id,
        "timestamp": datetime.utcnow().isoformat(),
        "details": details or {}
    }
    
    logger.warning(f"Security Event: {log_data}")