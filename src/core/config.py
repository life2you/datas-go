#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
配置文件
存储应用程序配置，包括数据库连接信息
"""

import os
import sys
from dotenv import load_dotenv

# 获取项目根目录
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 加载.env文件中的环境变量
load_dotenv()

# 辅助函数
def str_to_bool(value):
    """将字符串转换为布尔值"""
    return value.lower() in ('true', 'yes', '1', 't', 'y')

def parse_list(value):
    """解析逗号分隔的列表"""
    if not value:
        return []
    return [item.strip() for item in value.split(',') if item.strip()]

# 数据库配置
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'pumpportal'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'postgres')
}

# WebSocket API配置
WEBSOCKET_URI = os.getenv('WEBSOCKET_URI', 'wss://pumpportal.fun/api/data')

# 日志配置
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_DIR = os.path.abspath(os.getenv('LOG_DIR', os.path.join(ROOT_DIR, 'logs')))
LOG_FILE = os.getenv('LOG_FILE', 'pump_portal.log')
LOG_ERROR_FILE = os.getenv('LOG_ERROR_FILE', 'pump_portal_error.log')
LOG_SQL_FILE = os.getenv('LOG_SQL_FILE', 'sql.log')
LOG_MAX_BYTES = int(os.getenv('LOG_MAX_BYTES', '10485760'))  # 默认10MB
LOG_BACKUP_COUNT = int(os.getenv('LOG_BACKUP_COUNT', '5'))  # 默认保留5个备份
LOG_TO_FILE = str_to_bool(os.getenv('LOG_TO_FILE', 'true'))
SQL_LOG_ENABLED = str_to_bool(os.getenv('SQL_LOG_ENABLED', 'true'))  # 是否启用SQL日志
SQL_LOG_LEVEL = os.getenv('SQL_LOG_LEVEL', 'DEBUG')  # SQL日志级别

# 其他配置
RETRY_ATTEMPTS = int(os.getenv('RETRY_ATTEMPTS', '3'))
RETRY_DELAY = int(os.getenv('RETRY_DELAY', '5'))

# 事件类型监听设置
LISTEN_NEW_TOKEN = str_to_bool(os.getenv('LISTEN_NEW_TOKEN', 'true'))
LISTEN_MIGRATION = str_to_bool(os.getenv('LISTEN_MIGRATION', 'true'))
QUIET_MODE = str_to_bool(os.getenv('QUIET_MODE', 'false'))

# 监听的账户和代币列表，以逗号分隔
WATCH_ACCOUNTS = parse_list(os.getenv('WATCH_ACCOUNTS', ''))
WATCH_TOKENS = parse_list(os.getenv('WATCH_TOKENS', ''))

# HTTP代理配置
HTTP_PROXY = os.getenv("HTTP_PROXY", "")
HTTPS_PROXY = os.getenv("HTTPS_PROXY", "")
PROXY_ENABLED = str_to_bool(os.getenv("PROXY_ENABLED", "false"))
PROXY_USERNAME = os.getenv("PROXY_USERNAME", "")
PROXY_PASSWORD = os.getenv("PROXY_PASSWORD", "")

# HTTP客户端配置
HTTP_CONFIG = {
    "timeout": int(os.getenv("HTTP_TIMEOUT", "30")),
    "verify_ssl": str_to_bool(os.getenv("HTTP_VERIFY_SSL", "true")),
    "proxy": HTTP_PROXY or HTTPS_PROXY,  # 使用HTTP或HTTPS代理
    "proxy_username": PROXY_USERNAME,
    "proxy_password": PROXY_PASSWORD,
    "proxy_enabled": PROXY_ENABLED,
    "headers": {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
}

# API服务器配置
API_CONFIG = {
    "host": os.getenv("API_HOST", "0.0.0.0"),
    "port": int(os.getenv("API_PORT", "8000")),
    "enable_cors": str_to_bool(os.getenv("API_ENABLE_CORS", "true")),
    "cors_origins": parse_list(os.getenv("API_CORS_ORIGINS", "*")),
    "allowed_methods": parse_list(os.getenv("API_ALLOWED_METHODS", "GET,POST,OPTIONS")),
    "allowed_headers": parse_list(os.getenv("API_ALLOWED_HEADERS", "*")),
    "allow_credentials": str_to_bool(os.getenv("API_ALLOW_CREDENTIALS", "true")),
    "docs_url": os.getenv("API_DOCS_URL", "/docs"),
    "redoc_url": os.getenv("API_REDOC_URL", "/redoc"),
    "title": os.getenv("API_TITLE", "Pump Data API"),
    "description": os.getenv("API_DESCRIPTION", "提供代币数据访问的API接口"),
    "version": os.getenv("API_VERSION", "1.0.0")
}

# 代币回复数据采集配置
TOKEN_REPLIES_CONFIG = {
    "enabled": str_to_bool(os.getenv("TOKEN_REPLIES_ENABLED", "true")),
    "interval": int(os.getenv("TOKEN_REPLIES_INTERVAL", "300")),  # 默认5分钟
    "sol_threshold": float(os.getenv("TOKEN_REPLIES_SOL_THRESHOLD", "35.0")),
    "fetch_limit": int(os.getenv("TOKEN_REPLIES_FETCH_LIMIT", "1000")),
    "cookie": os.getenv("TOKEN_REPLIES_COOKIE", "")
}

# 错误邮件通知配置
ERROR_EMAIL_CONFIG = {
    "enabled": str_to_bool(os.getenv("ERROR_EMAIL_ENABLED", "false")),
    "host": os.getenv("ERROR_EMAIL_HOST", "smtp.example.com"),
    "port": int(os.getenv("ERROR_EMAIL_PORT", "587")),
    "user": os.getenv("ERROR_EMAIL_USER", ""),
    "password": os.getenv("ERROR_EMAIL_PASSWORD", ""),
    "from": os.getenv("ERROR_EMAIL_FROM", ""),
    "to": parse_list(os.getenv("ERROR_EMAIL_TO", "")),
    "subject_prefix": os.getenv("ERROR_EMAIL_SUBJECT_PREFIX", "[PUMP-ERROR]")
}

# Moralis API配置
MORALIS_CONFIG = {
    "api_key": os.getenv("MORALIS_API_KEY", ""),
} 