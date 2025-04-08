#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
日志配置模块
配置应用程序的日志记录系统，支持控制台和文件输出
"""

import os
import logging
from logging.handlers import RotatingFileHandler
import sys

from src.core.config import (
    LOG_LEVEL, LOG_FORMAT, LOG_DIR, LOG_FILE, LOG_ERROR_FILE, LOG_SQL_FILE,
    LOG_MAX_BYTES, LOG_BACKUP_COUNT, LOG_TO_FILE, SQL_LOG_ENABLED, SQL_LOG_LEVEL
)


def setup_logging():
    """
    设置日志系统
    - 设置根日志记录器的级别
    - 配置控制台处理器
    - 如果启用，配置文件处理器
    - 如果启用，配置错误日志文件处理器
    - 配置SQL日志记录
    """
    # 获取根日志记录器
    root_logger = logging.getLogger()
    
    # 设置根日志记录器的级别
    root_logger.setLevel(getattr(logging, LOG_LEVEL))
    
    # 清除所有现有的处理器
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 创建格式化器
    formatter = logging.Formatter(LOG_FORMAT)
    
    # 添加控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # 如果启用了文件日志，添加文件处理器
    if LOG_TO_FILE:
        # 确保日志目录存在
        os.makedirs(LOG_DIR, exist_ok=True)
        
        # 添加普通日志文件处理器
        file_path = os.path.join(LOG_DIR, LOG_FILE)
        logging.info(f"设置日志文件路径: {file_path}")
        
        # 确保路径存在
        log_dir = os.path.dirname(file_path)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
            logging.info(f"创建日志目录: {log_dir}")
        
        file_handler = RotatingFileHandler(
            file_path,
            maxBytes=LOG_MAX_BYTES,
            backupCount=LOG_BACKUP_COUNT,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        
        # 添加错误日志文件处理器（只记录ERROR及以上级别）
        error_file_path = os.path.join(LOG_DIR, LOG_ERROR_FILE)
        logging.info(f"设置错误日志文件路径: {error_file_path}")
        
        error_file_handler = RotatingFileHandler(
            error_file_path,
            maxBytes=LOG_MAX_BYTES,
            backupCount=LOG_BACKUP_COUNT,
            encoding='utf-8'
        )
        error_file_handler.setLevel(logging.ERROR)
        error_file_handler.setFormatter(formatter)
        root_logger.addHandler(error_file_handler)
        
        # 如果启用了SQL日志，添加SQL日志文件处理器
        if SQL_LOG_ENABLED:
            sql_log_file = os.path.join(LOG_DIR, LOG_SQL_FILE)
            logging.info(f"设置SQL日志文件路径: {sql_log_file}")
            
            sql_handler = RotatingFileHandler(
                sql_log_file,
                maxBytes=LOG_MAX_BYTES,
                backupCount=LOG_BACKUP_COUNT,
                encoding='utf-8'
            )
            sql_handler.setFormatter(formatter)
            
            # 创建SQL日志记录器
            sql_logger = logging.getLogger('src.db')
            sql_logger.propagate = False  # 避免日志消息传播到根记录器
            sql_logger.addHandler(sql_handler)
            sql_logger.setLevel(getattr(logging, SQL_LOG_LEVEL))
            
            # 添加控制台处理器给SQL日志记录器（可选，便于调试）
            if SQL_LOG_LEVEL == 'DEBUG':
                sql_console_handler = logging.StreamHandler()
                sql_console_handler.setFormatter(formatter)
                sql_console_handler.setLevel(logging.DEBUG)
                sql_logger.addHandler(sql_console_handler)
            
            logging.info(f"SQL日志已启用，级别: {SQL_LOG_LEVEL}, 文件: {sql_log_file}")
        
        # 记录初始化信息
        logging.info(f"日志系统已初始化，日志文件: {file_path}")
        logging.info(f"错误日志文件: {error_file_path}")


def get_logger(name):
    """
    获取指定名称的日志记录器
    
    Args:
        name: 日志记录器名称
        
    Returns:
        logging.Logger: 指定名称的日志记录器
    """
    return logging.getLogger(name) 