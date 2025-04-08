#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
错误处理模块
提供统一的错误处理、日志记录和通知功能
"""

import sys
import traceback
import logging
import functools
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

from src.core.logger import get_logger
from src.core.config import LOG_ERROR_FILE, LOG_DIR, ERROR_EMAIL_CONFIG

# 获取日志记录器
logger = get_logger(__name__)

# 错误通知配置从config.py获取
EMAIL_ENABLED = ERROR_EMAIL_CONFIG['enabled']
EMAIL_HOST = ERROR_EMAIL_CONFIG['host']
EMAIL_PORT = ERROR_EMAIL_CONFIG['port']
EMAIL_USER = ERROR_EMAIL_CONFIG['user']
EMAIL_PASSWORD = ERROR_EMAIL_CONFIG['password']
EMAIL_FROM = ERROR_EMAIL_CONFIG['from']
EMAIL_TO = ERROR_EMAIL_CONFIG['to']
EMAIL_SUBJECT_PREFIX = ERROR_EMAIL_CONFIG['subject_prefix']


def log_exception(exc_type, exc_value, exc_traceback):
    """
    记录未捕获的异常
    这个函数用于替代sys.excepthook
    """
    if issubclass(exc_type, KeyboardInterrupt):
        # 对于键盘中断，使用默认处理
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    # 构建完整的错误消息
    error_message = f"未捕获的异常: {exc_type.__name__}\n"
    error_message += f"错误信息: {exc_value}\n"
    error_message += "堆栈跟踪:\n"
    error_message += ''.join(traceback.format_tb(exc_traceback))
    
    # 记录错误日志
    logger.critical(error_message)
    
    # 如果配置了邮件通知，发送错误通知
    if EMAIL_ENABLED:
        send_error_email(error_message, exc_type.__name__)


def send_error_email(error_message, error_type):
    """
    发送错误通知邮件
    
    Args:
        error_message: 完整的错误消息
        error_type: 错误类型名称
    """
    if not EMAIL_USER or not EMAIL_PASSWORD or not EMAIL_TO:
        logger.warning("邮件通知配置不完整，无法发送错误通知")
        return
    
    try:
        # 创建邮件
        msg = MIMEMultipart()
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        msg['Subject'] = f"{EMAIL_SUBJECT_PREFIX}{error_type} - {timestamp}"
        msg['From'] = EMAIL_FROM or EMAIL_USER
        msg['To'] = ', '.join(EMAIL_TO)
        
        # 添加错误信息
        msg.attach(MIMEText(error_message, 'plain'))
        
        # 发送邮件
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            server.send_message(msg)
        
        logger.info(f"已发送错误通知邮件至 {', '.join(EMAIL_TO)}")
    except Exception as e:
        logger.error(f"发送错误通知邮件失败: {str(e)}")


def error_handler(func):
    """
    错误处理装饰器
    捕获函数执行中的异常，记录日志并可选择性地发送通知
    
    用法:
    @error_handler
    def some_function():
        # 函数内容
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # 获取堆栈跟踪
            stack_trace = traceback.format_exc()
            
            # 构建错误消息
            error_message = f"函数 {func.__name__} 执行出错: {type(e).__name__}\n"
            error_message += f"错误信息: {str(e)}\n"
            error_message += f"堆栈跟踪:\n{stack_trace}"
            
            # 记录错误日志
            logger.error(error_message)
            
            # 如果配置了邮件通知，发送错误通知
            if EMAIL_ENABLED:
                send_error_email(error_message, type(e).__name__)
            
            # 重新抛出异常
            raise
    
    return wrapper


def async_error_handler(func):
    """
    异步函数的错误处理装饰器
    
    用法:
    @async_error_handler
    async def some_async_function():
        # 函数内容
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            # 获取堆栈跟踪
            stack_trace = traceback.format_exc()
            
            # 构建错误消息
            error_message = f"异步函数 {func.__name__} 执行出错: {type(e).__name__}\n"
            error_message += f"错误信息: {str(e)}\n"
            error_message += f"堆栈跟踪:\n{stack_trace}"
            
            # 记录错误日志
            logger.error(error_message)
            
            # 如果配置了邮件通知，发送错误通知
            if EMAIL_ENABLED:
                send_error_email(error_message, type(e).__name__)
            
            # 重新抛出异常
            raise
    
    return wrapper


def setup_error_handling():
    """
    设置全局的错误处理
    替换默认的异常处理钩子
    """
    sys.excepthook = log_exception
    logger.info("全局错误处理已设置")


def get_latest_errors(count=10):
    """
    获取最新的错误日志
    
    Args:
        count: 要获取的错误数量
        
    Returns:
        list: 错误日志列表
    """
    error_file = os.path.join(LOG_DIR, LOG_ERROR_FILE)
    if not os.path.exists(error_file):
        return []
    
    try:
        with open(error_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 按时间戳分割日志
        errors = []
        current_error = []
        
        for line in lines:
            # 检查是否为新日志条目的开始（通常以时间戳开头）
            if line.strip() and line[0].isdigit() and ' - ' in line:
                if current_error:
                    errors.append(''.join(current_error))
                    current_error = []
                current_error.append(line)
            elif current_error:
                current_error.append(line)
        
        # 添加最后一个错误
        if current_error:
            errors.append(''.join(current_error))
        
        # 返回最近的count个错误
        return errors[-count:]
    
    except Exception as e:
        logger.error(f"读取错误日志失败: {str(e)}")
        return [] 