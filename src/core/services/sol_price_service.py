#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
SOL价格服务
定时获取SOL价格并存储到数据库，同时保持内存缓存
"""

import logging
import threading
import time
from datetime import datetime
from typing import Optional, Dict, Any
import asyncio

from src.client.moralis_api import MoralisAPI
from src.db.database import db
from src.core.config import MORALIS_CONFIG

logger = logging.getLogger(__name__)

class SolPriceService:
    """SOL价格服务"""
    
    def __init__(self):
        self.db = db
        self.running = False
        self.update_interval = 60  # 更新间隔（秒）
        self.api = MoralisAPI(MORALIS_CONFIG["api_key"])
        logger.info(f"SOL价格服务已初始化，更新间隔: {self.update_interval}秒")
        
        # 尝试从数据库加载最新价格到缓存
        self._load_price_from_db()
    
    def _load_price_from_db(self):
        """从数据库加载最新的SOL价格到缓存"""
        try:
            latest = self.db.get_latest_sol_price()
            if latest:
                price = float(latest['price'])
                # 将datetime转换为时间戳
                timestamp = latest['timestamp'].timestamp()
                MoralisAPI.update_sol_price_cache(price, timestamp)
                logger.info(f"已从数据库加载SOL价格缓存: ${price:.2f} @ {latest['timestamp']}")
        except Exception as e:
            logger.error(f"从数据库加载SOL价格失败: {str(e)}")
    
    async def _run(self):
        """运行SOL价格更新服务"""
        self.running = True
        while self.running:
            try:
                await self._update_sol_price()
            except Exception as e:
                logger.error(f"更新SOL价格时发生错误: {str(e)}")
            await asyncio.sleep(self.update_interval)
    
    async def _update_sol_price(self):
        """更新SOL价格"""
        max_retries = 3
        retry_delay = 1  # 秒
        
        for attempt in range(max_retries):
            try:
                # 获取当前SOL价格
                price = await self._get_sol_price()
                if price is None:
                    if attempt < max_retries - 1:
                        logger.warning(f"获取SOL价格失败，尝试重试 ({attempt + 1}/{max_retries})")
                        await asyncio.sleep(retry_delay)
                        continue
                    else:
                        logger.error("无法获取SOL价格，已达到最大重试次数")
                        return
                
                current_time = datetime.now()
                
                # 保存到数据库
                success = self.save_sol_price(price, current_time)
                if not success:
                    if attempt < max_retries - 1:
                        logger.warning(f"保存SOL价格失败，尝试重试 ({attempt + 1}/{max_retries})")
                        await asyncio.sleep(retry_delay)
                        continue
                    else:
                        logger.error("保存SOL价格到数据库失败，已达到最大重试次数")
                        return
                
                logger.info(f"SOL价格已更新: ${price:.2f}")
                return
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"更新SOL价格时发生错误，尝试重试 ({attempt + 1}/{max_retries}): {str(e)}")
                    await asyncio.sleep(retry_delay)
                else:
                    logger.error(f"更新SOL价格时发生错误: {str(e)}")
                    raise
    
    def save_sol_price(self, price: float, timestamp: datetime) -> bool:
        """保存SOL价格到数据库"""
        max_retries = 3
        retry_delay = 1  # 秒
        
        for attempt in range(max_retries):
            try:
                query = """
                INSERT INTO sol_price (price, timestamp)
                VALUES (%s, %s)
                RETURNING id;
                """
                cursor = self.db.execute(query, (price, timestamp))
                if cursor:
                    result = cursor.fetchone()
                    if result and 'id' in result:
                        logger.info(f"SOL价格记录已保存，ID: {result['id']}, 价格: ${price:.2f}")
                        return True
                    else:
                        if attempt < max_retries - 1:
                            logger.warning(f"保存SOL价格失败：未返回ID，尝试重试 ({attempt + 1}/{max_retries})")
                            time.sleep(retry_delay)
                            continue
                        else:
                            logger.error("保存SOL价格失败：未返回ID，已达到最大重试次数")
                            return False
                return False
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"保存SOL价格失败，尝试重试 ({attempt + 1}/{max_retries}): {str(e)}")
                    time.sleep(retry_delay)
                else:
                    logger.error(f"保存SOL价格失败: {str(e)}")
                    return False
    
    async def _get_sol_price(self):
        """获取最新的SOL价格"""
        try:
            price = self.api.get_sol_usd_price()
            if price is None:
                logger.warning("获取SOL价格失败，跳过本次更新")
                return None
            return price
        except Exception as e:
            logger.error(f"获取SOL价格时发生错误: {str(e)}")
            return None
    
    def get_current_price(self) -> float:
        """
        获取当前缓存的SOL价格
        
        返回:
            当前SOL价格，如果没有缓存则返回0.0
        """
        price, _ = MoralisAPI.get_cached_sol_price()
        return price
    
    def get_price_with_timestamp(self) -> Dict[str, Any]:
        """
        获取当前缓存的SOL价格和时间戳
        
        返回:
            包含价格和时间戳的字典
        """
        price, timestamp = MoralisAPI.get_cached_sol_price()
        return {
            "price": price,
            "timestamp": timestamp,
            "formatted_time": datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S') if timestamp else None
        }
    
    def get_price_history(self, days: int = 1, limit: int = 100) -> list:
        """
        获取SOL价格历史记录
        
        参数:
            days: 获取最近几天的数据，默认为1天
            limit: 最大记录数，默认为100
            
        返回:
            价格记录列表
        """
        if days <= 0:
            days = 1
            
        # 计算起始时间
        end_time = time.time()
        start_time = end_time - (days * 24 * 60 * 60)
        
        # 查询数据库
        history = self.db.get_sol_price_history(start_time, end_time, limit)
        return history


# 创建全局单例
sol_price_service = SolPriceService()


# 用法示例
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # 启动服务
    asyncio.run(sol_price_service._run())
    
    try:
        # 等待一段时间，让服务运行
        print("SOL价格服务已启动，按Ctrl+C退出...")
        while True:
            # 每5秒输出当前价格
            time.sleep(5)
            price_data = sol_price_service.get_price_with_timestamp()
            print(f"当前SOL价格: ${price_data['price']:.2f} @ {price_data['formatted_time']}")
    except KeyboardInterrupt:
        print("正在停止服务...")
    finally:
        # 停止服务
        sol_price_service.running = False 