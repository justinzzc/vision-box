#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
异常处理模块
定义自定义异常和全局异常处理器
"""

from typing import Union
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from loguru import logger
import traceback


class VisionAppException(Exception):
    """应用基础异常类"""
    
    def __init__(self, message: str, code: str = "UNKNOWN_ERROR", status_code: int = 500):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(self.message)


class FileNotFoundError(VisionAppException):
    """文件未找到异常"""
    
    def __init__(self, filename: str):
        super().__init__(
            message=f"文件未找到: {filename}",
            code="FILE_NOT_FOUND",
            status_code=404
        )


class FileFormatError(VisionAppException):
    """文件格式错误异常"""
    
    def __init__(self, filename: str, supported_formats: list):
        super().__init__(
            message=f"不支持的文件格式: {filename}，支持的格式: {', '.join(supported_formats)}",
            code="UNSUPPORTED_FILE_FORMAT",
            status_code=400
        )


class FileSizeError(VisionAppException):
    """文件大小错误异常"""
    
    def __init__(self, filename: str, size: int, max_size: int):
        super().__init__(
            message=f"文件大小超出限制: {filename} ({size} bytes)，最大允许: {max_size} bytes",
            code="FILE_SIZE_EXCEEDED",
            status_code=400
        )


class DetectionError(VisionAppException):
    """检测错误异常"""
    
    def __init__(self, message: str):
        super().__init__(
            message=f"检测失败: {message}",
            code="DETECTION_ERROR",
            status_code=500
        )


class ModelNotFoundError(VisionAppException):
    """模型未找到异常"""
    
    def __init__(self, model_name: str):
        super().__init__(
            message=f"模型未找到: {model_name}",
            code="MODEL_NOT_FOUND",
            status_code=404
        )


class TaskNotFoundError(VisionAppException):
    """任务未找到异常"""
    
    def __init__(self, task_id: str):
        super().__init__(
            message=f"任务未找到: {task_id}",
            code="TASK_NOT_FOUND",
            status_code=404
        )


class DatabaseError(VisionAppException):
    """数据库错误异常"""
    
    def __init__(self, message: str):
        super().__init__(
            message=f"数据库错误: {message}",
            code="DATABASE_ERROR",
            status_code=500
        )


class AuthenticationError(VisionAppException):
    """认证错误异常"""
    
    def __init__(self, message: str = "认证失败"):
        super().__init__(
            message=message,
            code="AUTHENTICATION_ERROR",
            status_code=401
        )


class AuthorizationError(VisionAppException):
    """授权错误异常"""
    
    def __init__(self, message: str = "权限不足"):
        super().__init__(
            message=message,
            code="AUTHORIZATION_ERROR",
            status_code=403
        )


async def vision_app_exception_handler(request: Request, exc: VisionAppException):
    """自定义异常处理器"""
    logger.error(f"应用异常: {exc.code} - {exc.message}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "code": exc.code,
            "message": exc.message,
            "detail": exc.message
        }
    )


async def http_exception_handler(request: Request, exc: Union[HTTPException, StarletteHTTPException]):
    """HTTP异常处理器"""
    logger.warning(f"HTTP异常: {exc.status_code} - {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "code": f"HTTP_{exc.status_code}",
            "message": exc.detail,
            "detail": exc.detail
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """请求验证异常处理器"""
    logger.warning(f"请求验证失败: {exc.errors()}")
    
    # 格式化验证错误信息
    errors = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        message = error["msg"]
        errors.append(f"{field}: {message}")
    
    return JSONResponse(
        status_code=422,
        content={
            "error": True,
            "code": "VALIDATION_ERROR",
            "message": "请求参数验证失败",
            "detail": "; ".join(errors),
            "errors": exc.errors()
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理器"""
    logger.error(f"未处理的异常: {type(exc).__name__} - {str(exc)}")
    logger.error(f"异常堆栈: {traceback.format_exc()}")
    
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "code": "INTERNAL_SERVER_ERROR",
            "message": "服务器内部错误",
            "detail": "服务器遇到了一个意外的错误，请稍后重试"
        }
    )


def setup_exception_handlers(app: FastAPI):
    """设置异常处理器"""
    
    # 自定义异常处理器
    app.add_exception_handler(VisionAppException, vision_app_exception_handler)
    
    # HTTP异常处理器
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    
    # 请求验证异常处理器
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    
    # 通用异常处理器（必须放在最后）
    app.add_exception_handler(Exception, general_exception_handler)
    
    logger.info("异常处理器设置完成")


# 异常工具函数
def raise_file_not_found(filename: str):
    """抛出文件未找到异常"""
    raise FileNotFoundError(filename)


def raise_file_format_error(filename: str, supported_formats: list):
    """抛出文件格式错误异常"""
    raise FileFormatError(filename, supported_formats)


def raise_file_size_error(filename: str, size: int, max_size: int):
    """抛出文件大小错误异常"""
    raise FileSizeError(filename, size, max_size)


def raise_detection_error(message: str):
    """抛出检测错误异常"""
    raise DetectionError(message)


def raise_model_not_found(model_name: str):
    """抛出模型未找到异常"""
    raise ModelNotFoundError(model_name)


def raise_task_not_found(task_id: str):
    """抛出任务未找到异常"""
    raise TaskNotFoundError(task_id)


def raise_database_error(message: str):
    """抛出数据库错误异常"""
    raise DatabaseError(message)


def raise_authentication_error(message: str = "认证失败"):
    """抛出认证错误异常"""
    raise AuthenticationError(message)


def raise_authorization_error(message: str = "权限不足"):
    """抛出授权错误异常"""
    raise AuthorizationError(message)