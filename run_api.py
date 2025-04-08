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
import uvicorn

from src.core.logger import setup_logging
from src.core.error_handler import setup_error_handling
from src.web.web_api import start_api_server
from src.core.config import API_CONFIG, LISTEN_NEW_TOKEN, TOKEN_REPLIES_CONFIG
from src.client.pump_portal_client import PumpPortalClient
from src.client.metadata_scanner import MetadataScanner
from src.core.processors.pump_data_processor import PumpDataProcessor
from src.core.processors.token_processor import TokenProcessor
from src.core.processors.trade_processor import TradeProcessor
from src.core.handlers import handle_new_token, handle_migration, handle_account_trade, handle_token_trade
from src.core.services.sol_price_service import sol_price_service

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
        # 将客户端实例传递给TokenProcessor
        TokenProcessor.set_client(client)
        # 注册新代币创建事件回调
        client.on_new_token(handle_new_token)
        client.on_migration(handle_migration)
        client.on_account_trade(handle_account_trade)
        client.on_token_trade(handle_token_trade)
        
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

def start_metadata_scanner():
    """启动元数据扫描服务"""
    logger.info("启动代币元数据扫描服务...")
    try:
        scanner = MetadataScanner()
        
        # 首次运行
        logger.info("执行代币元数据扫描任务")
        start_time = time.time()
        asyncio.run(scanner.scan_and_update())
        elapsed = time.time() - start_time
        logger.info(f"代币元数据扫描任务完成，耗时: {elapsed:.2f}秒")
        
        # 定时循环执行，每3分钟扫描一次
        interval = 180  # 3分钟
        while True:
            next_run = time.time() + interval
            next_run_time = datetime.fromtimestamp(next_run).strftime('%Y-%m-%d %H:%M:%S')
            logger.info(f"下次元数据扫描计划时间: {next_run_time} ({interval}秒后)")
            
            # 休眠直到下次执行时间
            time.sleep(interval)
            
            # 执行扫描任务
            logger.info("执行代币元数据扫描任务")
            start_time = time.time()
            asyncio.run(scanner.scan_and_update())
            elapsed = time.time() - start_time
            logger.info(f"代币元数据扫描任务完成，耗时: {elapsed:.2f}秒")
            
    except Exception as e:
        logger.error(f"代币元数据扫描服务异常: {str(e)}", exc_info=True)

async def main():
    """主函数"""
    try:
        logger.info(f"启动API服务器 @ {API_CONFIG['host']}:{API_CONFIG['port']}")
        
        # 启动SOL价格服务
        logger.info("启动SOL价格更新服务...")
        sol_price_service.running = True
        asyncio.create_task(sol_price_service._run())
        
        # 在单独的线程中启动WebSocket监听服务
        ws_thread = threading.Thread(target=start_websocket_client, daemon=True)
        ws_thread.start()
        logger.info("WebSocket监听线程已启动")
        
        # 在单独的线程中启动数据采集服务
        data_thread = threading.Thread(target=start_data_collection, daemon=True)
        data_thread.start()
        logger.info("数据采集线程已启动")
        
        # 在单独的线程中启动元数据扫描服务
        metadata_thread = threading.Thread(target=start_metadata_scanner, daemon=True)
        metadata_thread.start()
        logger.info("元数据扫描线程已启动")
        
        # 启动API服务器
        app = start_api_server()
        config = uvicorn.Config(app, host=API_CONFIG['host'], port=API_CONFIG['port'])
        server = uvicorn.Server(config)
        await server.serve()
        
    except KeyboardInterrupt:
        logger.info("用户中断，关闭API服务器")
        sol_price_service.running = False
    except Exception as e:
        logger.error(f"API服务器启动失败: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    asyncio.run(main()) 