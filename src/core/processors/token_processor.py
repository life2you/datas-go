#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
代币处理工具
处理代币创建事件并存入数据库
"""

import logging
import json
from src.db.database import db
from src.core.services.sol_price_service import sol_price_service

logger = logging.getLogger(__name__)

class TokenProcessor:
    """代币数据处理器"""
    
    # 用于存储客户端实例的类变量
    _client = None
    
    @classmethod
    def set_client(cls, client):
        """设置客户端实例"""
        cls._client = client
    
    @staticmethod
    async def process_token_creation(data):
        """
        处理代币创建事件并存入数据库
        
        参数:
            data: 代币创建事件数据
        """
        try:
            # 记录日志
            logger.info(f"处理代币创建事件: {data.get('name')} ({data.get('symbol')})")
            
            # 检查必要字段
            if not TokenProcessor.validate_token_data(data):
                logger.warning(f"无效的代币创建数据: 缺少必要字段")
                return False
            
            # 插入数据库
            token_id = db.insert_token_event(data)
            
            if token_id:
                logger.info(f"代币数据已成功保存到数据库，ID: {token_id}")
                
                # 计算并更新美元价格
                try:
                    v_tokens = data.get('vTokensInBondingCurve')
                    v_sol = data.get('vSolInBondingCurve')
                    
                    if v_tokens and v_sol and float(v_tokens) > 0:
                        # 获取SOL价格
                        sol_usd_price = sol_price_service.get_current_price()
                        
                        if sol_usd_price > 0:
                            # 计算代币美元价格
                            token_usd_price = sol_usd_price * float(v_sol) / float(v_tokens)
                            
                            # 构建更新SQL
                            query = """
                            UPDATE token 
                            SET latest_usd_price = %s
                            WHERE id = %s
                            """
                            
                            # 执行更新
                            db.execute(query, (token_usd_price, token_id))
                            logger.info(f"初次代币美元价格已更新: {data.get('name')} (${token_usd_price:.12f})")
                except Exception as e:
                    logger.error(f"计算初次代币美元价格失败: {str(e)}")
                
                # 订阅代币交易
                if TokenProcessor._client:
                    try:
                        await TokenProcessor._client.subscribe_token_trade([data.get('mint')])
                        logger.info(f"已订阅代币交易: {data.get('name')} ({data.get('mint')})")
                    except Exception as e:
                        logger.error(f"订阅代币交易失败: {str(e)}")
                
                return True
            else:
                logger.error(f"代币数据保存失败")
                return False
        except Exception as e:
            logger.error(f"处理代币创建事件失败: {str(e)}")
            return False
    
    @staticmethod
    def validate_token_data(data):
        """
        验证代币数据是否有效
        
        参数:
            data: 代币数据
            
        返回:
            bool: 数据是否有效
        """
        required_fields = ['signature', 'mint', 'name', 'symbol']
        for field in required_fields:
            if field not in data:
                logger.warning(f"无效的代币数据: 缺少字段 {field}")
                return False
                
        return True 