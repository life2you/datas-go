#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
交易处理工具
处理代币交易事件并存入数据库
"""

import logging
import json
from src.db.database import db
import asyncio
import traceback

logger = logging.getLogger(__name__)

class TradeProcessor:
    """代币交易数据处理器"""
    
    @staticmethod
    async def process_trade(data):
        """
        处理代币交易事件并存入数据库
        
        参数:
            data: 代币交易事件数据
        """
        if not data:
            logger.error("处理交易事件失败: 数据为空", exc_info=True)
            return False
            
        max_retries = 3
        retry_delay = 1  # 秒
        
        for attempt in range(max_retries):
            try:
                # 记录日志
                logger.info(f"处理交易事件: {data.get('mint')} 类型: {data.get('txType')}")
                
                # 检查必要字段
                if not TradeProcessor.validate_trade_data(data):
                    logger.warning(f"无效的交易数据: 缺少必要字段", exc_info=True)
                    return False
                
                # 插入数据库
                trade_id = db.insert_trade_record(data)
                
                if trade_id:
                    logger.info(f"交易记录已成功保存到数据库，ID: {trade_id}")
                    return True
                else:
                    if attempt < max_retries - 1:
                        logger.warning(f"交易记录保存失败，尝试重试 ({attempt + 1}/{max_retries})")
                        await asyncio.sleep(retry_delay)
                    else:
                        logger.error(f"交易记录保存失败，已达到最大重试次数", exc_info=True)
                        return False
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"处理交易事件失败，尝试重试 ({attempt + 1}/{max_retries}): {str(e)}")
                    await asyncio.sleep(retry_delay)
                else:
                    logger.error(f"处理交易事件失败: {str(e)}", exc_info=True)
                    logger.exception(e)
                    return False
    
    @staticmethod
    def validate_trade_data(data):
        """
        验证交易数据是否有效
        
        参数:
            data: 交易数据
            
        返回:
            bool: 数据是否有效
        """
        if not isinstance(data, dict):
            logger.warning("无效的交易数据: 不是字典类型", exc_info=True)
            return False
            
        required_fields = ['signature', 'mint', 'traderPublicKey', 'txType', 'solAmount']
        for field in required_fields:
            if field not in data:
                logger.warning(f"无效的交易数据: 缺少字段 {field}", exc_info=True)
                return False
            if data[field] is None:
                logger.warning(f"无效的交易数据: 字段 {field} 的值为None", exc_info=True)
                return False
        
        # 验证交易类型
        valid_tx_types = ['buy', 'sell']
        if data.get('txType') not in valid_tx_types:
            logger.warning(f"无效的交易类型: {data.get('txType')}", exc_info=True)
            return False
            
        # 验证金额
        try:
            sol_amount = float(data.get('solAmount', 0))
            if sol_amount <= 0:
                logger.warning(f"无效的交易金额: {sol_amount}", exc_info=True)
                return False
        except (ValueError, TypeError) as e:
            logger.warning(f"无效的交易金额格式: {data.get('solAmount')}", exc_info=True)
            return False
            
        return True 