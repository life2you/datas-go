#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
代币回复数据采集服务
定期从Pump API获取高价值代币的回复数据，并存入数据库
"""

import asyncio
import logging
import time
from datetime import datetime

from src.api.pump_data_processor import PumpDataProcessor, ensure_token_replies_table
from src.config.config import TOKEN_REPLIES_CONFIG
from src.utils.logger import get_logger

logger = get_logger(__name__)


class TokenRepliesService:
    """代币回复数据采集服务，定期执行数据采集任务"""
    
    def __init__(self):
        """初始化服务"""
        self.enabled = TOKEN_REPLIES_CONFIG["enabled"]
        self.interval = TOKEN_REPLIES_CONFIG["interval"]
        self.sol_threshold = TOKEN_REPLIES_CONFIG["sol_threshold"]
        self.fetch_limit = TOKEN_REPLIES_CONFIG["fetch_limit"]
        self.cookie = TOKEN_REPLIES_CONFIG["cookie"]
        self.task = None
        self.running = False
        
    async def start(self):
        """启动定时采集服务"""
        if not self.enabled:
            logger.info("代币回复数据采集服务已禁用")
            return
            
        # 确保表存在
        if not ensure_token_replies_table():
            logger.error("无法创建必要的数据库表，服务无法启动")
            return
            
        if self.running:
            logger.warning("代币回复数据采集服务已在运行中")
            return
            
        self.running = True
        logger.info(f"启动代币回复数据采集服务 (SOL阈值: {self.sol_threshold}, 间隔: {self.interval}秒)")
        
        # 创建并运行任务
        self.task = asyncio.create_task(self._run_collection_loop())
        
    async def stop(self):
        """停止定时采集服务"""
        if not self.running or not self.task:
            return
            
        self.running = False
        if not self.task.done():
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
                
        logger.info("代币回复数据采集服务已停止")
        
    async def _run_collection_loop(self):
        """运行数据采集循环"""
        run_count = 0
        
        while self.running:
            try:
                run_count += 1
                logger.info(f"开始第 {run_count} 次代币回复数据采集 (SOL阈值: {self.sol_threshold})")
                
                # 记录开始时间
                start_time = time.time()
                
                # 异步执行数据采集
                await self._collect_token_replies()
                
                # 计算执行时间
                elapsed_time = time.time() - start_time
                logger.info(f"第 {run_count} 次数据采集完成，耗时: {elapsed_time:.2f} 秒")
                
                # 计算需要等待的时间
                wait_time = max(0, self.interval - elapsed_time)
                
                if wait_time > 0:
                    next_run = datetime.fromtimestamp(time.time() + wait_time)
                    logger.info(f"下一次采集将在 {next_run.strftime('%Y-%m-%d %H:%M:%S')} 开始")
                    await asyncio.sleep(wait_time)
                    
            except asyncio.CancelledError:
                logger.info("代币回复数据采集任务被取消")
                break
            except Exception as e:
                logger.error(f"代币回复数据采集出错: {str(e)}")
                # 发生错误时等待一段时间后继续
                await asyncio.sleep(min(60, self.interval))
    
    async def _collect_token_replies(self):
        """异步执行数据采集任务"""
        # 由于PumpDataProcessor是同步的，我们在线程池中运行它
        return await asyncio.to_thread(
            self._run_processor_sync
        )
        
    def _run_processor_sync(self):
        """同步运行数据处理器"""
        try:
            # 创建数据处理器
            with PumpDataProcessor(cookie=self.cookie) as processor:
                # 处理高价值代币的回复
                processor.process_high_value_tokens(
                    sol_threshold=self.sol_threshold,
                    limit=self.fetch_limit
                )
            return True
        except Exception as e:
            logger.error(f"运行数据处理器时出错: {str(e)}")
            return False


# 创建全局服务实例
token_replies_service = TokenRepliesService() 