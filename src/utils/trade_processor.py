#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
交易处理工具
处理代币交易事件并存入数据库
"""

import logging
import json
from src.db.database import db

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
        try:
            # 记录日志
            logger.info(f"处理交易事件: {data.get('mint')} 类型: {data.get('txType')}")
            
            # 检查必要字段
            if not TradeProcessor.validate_trade_data(data):
                logger.warning(f"无效的交易数据: 缺少必要字段")
                return False
            
            # 插入数据库
            trade_id = db.insert_trade_record(data)
            
            if trade_id:
                logger.info(f"交易记录已成功保存到数据库，ID: {trade_id}")
                return True
            else:
                logger.error(f"交易记录保存失败")
                return False
        except Exception as e:
            logger.error(f"处理交易事件失败: {str(e)}")
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
        required_fields = ['signature', 'mint', 'traderPublicKey', 'txType']
        for field in required_fields:
            if field not in data:
                logger.warning(f"无效的交易数据: 缺少字段 {field}")
                return False
        
        # 验证交易类型
        valid_tx_types = ['buy', 'sell']
        if data.get('txType') not in valid_tx_types:
            logger.warning(f"无效的交易类型: {data.get('txType')}")
            return False
            
        return True 