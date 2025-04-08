#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
事件处理函数模块
定义用于处理各种事件的回调函数
"""

import json
import logging
from src.core.error_handler import async_error_handler
from src.core.processors.token_processor import TokenProcessor
from src.core.processors.trade_processor import TradeProcessor

logger = logging.getLogger(__name__)

# 回调函数：处理新代币创建事件
@async_error_handler
async def handle_new_token(data):
    logger.info(f"新代币创建: {json.dumps(data, ensure_ascii=False, indent=2)}")
    
    # 使用TokenProcessor处理代币创建事件并存入数据库
    if data.get('txType') == 'create':
        success = await TokenProcessor.process_token_creation(data)
        if success:
            logger.info(f"代币 {data.get('name')} ({data.get('symbol')}) 已成功存入数据库")
        else:
            logger.error(f"代币 {data.get('name')} ({data.get('symbol')}) 存入数据库失败", exc_info=True)

# 回调函数：处理迁移事件
@async_error_handler
async def handle_migration(data):
    logger.info(f"迁移事件: {json.dumps(data, ensure_ascii=False, indent=2)}")

# 回调函数：处理账户交易事件
@async_error_handler
async def handle_account_trade(data):
    logger.info(f"账户交易: {json.dumps(data, ensure_ascii=False, indent=2)}")
    
    # 使用TradeProcessor处理账户交易事件并存入数据库
    # 只处理与账户相关的特殊逻辑，不再存储交易数据
    # 交易数据统一由handle_token_trade处理
    pass

# 回调函数：处理代币交易事件
@async_error_handler
async def handle_token_trade(data):
    """
    处理代币交易事件
    
    参数:
        data: 交易事件数据
    """
    try:
        if not data:
            logger.error("处理代币交易事件失败: 数据为空", exc_info=True)
            return
            
        logger.info(f"代币交易: {json.dumps(data, ensure_ascii=False, indent=2)}")
        
        # 使用TradeProcessor处理代币交易事件并存入数据库
        if data.get('txType') in ['buy', 'sell']:
            try:
                success = await TradeProcessor.process_trade(data)
                if success:
                    logger.info(f"代币交易记录已成功存入数据库")
                else:
                    logger.error(f"代币交易记录存入数据库失败: {data.get('signature')}", exc_info=True)
            except Exception as e:
                logger.error(f"处理交易记录失败: {str(e)}", exc_info=True)
                logger.exception(e)
        else:
            logger.warning(f"忽略非交易类型事件: {data.get('txType')}")
    except Exception as e:
        logger.error(f"处理代币交易事件失败: {str(e)}", exc_info=True)
        logger.exception(e) 