#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
API服务器启动脚本
用于启动Web API服务器，为前端提供数据访问接口
"""

import sys
import logging
import threading
import asyncio
import time
from datetime import datetime

from src.utils.logger import setup_logging
from src.utils.error_handler import setup_error_handling
from src.api.web_api import start_api_server
from src.config.config import API_CONFIG, LISTEN_NEW_TOKEN, TOKEN_REPLIES_CONFIG
from src.pump_portal_client import PumpPortalClient
from src.api.pump_data_processor import PumpDataProcessor

# 配置日志和错误处理
setup_logging()
setup_error_handling()
logger = logging.getLogger("API-Server")

def start_websocket_client():
    """启动WebSocket客户端监听服务"""
    if not LISTEN_NEW_TOKEN:
        logger.info("WebSocket监听服务已禁用，跳过启动")
        return
    
    logger.info("启动WebSocket监听服务...")
    try:
        client = PumpPortalClient()
        asyncio.run(client.connect_and_listen())
    except Exception as e:
        logger.error(f"WebSocket监听服务异常: {str(e)}", exc_info=True)

def start_data_collection():
    """启动数据采集定时任务"""
    if not TOKEN_REPLIES_CONFIG["enabled"]:
        logger.info("代币回复数据采集服务已禁用，跳过启动")
        return
    
    logger.info("启动代币回复数据采集服务...")
    interval = TOKEN_REPLIES_CONFIG["interval"]
    sol_threshold = TOKEN_REPLIES_CONFIG["sol_threshold"]
    cookie = TOKEN_REPLIES_CONFIG["cookie"]
    
    try:
        processor = PumpDataProcessor()
        
        # 首次运行
        logger.info(f"执行代币回复数据采集任务，SOL阈值: {sol_threshold}")
        start_time = time.time()
        processor.process_high_value_tokens(sol_threshold=sol_threshold, cookie=cookie)
        elapsed = time.time() - start_time
        logger.info(f"代币回复数据采集任务完成，耗时: {elapsed:.2f}秒")
        
        # 定时循环执行
        while True:
            next_run = time.time() + interval
            next_run_time = datetime.fromtimestamp(next_run).strftime('%Y-%m-%d %H:%M:%S')
            logger.info(f"下次采集计划时间: {next_run_time} ({interval}秒后)")
            
            # 休眠直到下次执行时间
            time.sleep(interval)
            
            # 执行采集任务
            logger.info(f"执行代币回复数据采集任务，SOL阈值: {sol_threshold}")
            start_time = time.time()
            processor.process_high_value_tokens(sol_threshold=sol_threshold, cookie=cookie)
            elapsed = time.time() - start_time
            logger.info(f"代币回复数据采集任务完成，耗时: {elapsed:.2f}秒")
            
    except Exception as e:
        logger.error(f"代币回复数据采集服务异常: {str(e)}", exc_info=True)

def main():
    """主函数"""
    try:
        logger.info(f"启动API服务器 @ {API_CONFIG['host']}:{API_CONFIG['port']}")
        
        # 在单独的线程中启动WebSocket监听服务
        ws_thread = threading.Thread(target=start_websocket_client, daemon=True)
        ws_thread.start()
        logger.info("WebSocket监听线程已启动")
        
        # 在单独的线程中启动数据采集服务
        data_thread = threading.Thread(target=start_data_collection, daemon=True)
        data_thread.start()
        logger.info("数据采集线程已启动")
        
        # 启动API服务器（这会阻塞主线程）
        start_api_server()
        return 0
    except KeyboardInterrupt:
        logger.info("用户中断，关闭API服务器")
        return 0
    except Exception as e:
        logger.error(f"API服务器启动失败: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main()) 