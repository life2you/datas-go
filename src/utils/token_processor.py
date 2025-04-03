#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
代币处理工具
处理代币创建事件并存入数据库
"""

import logging
import json
from src.db.database import db

logger = logging.getLogger(__name__)

class TokenProcessor:
    """代币数据处理器"""
    
    # 添加一个类变量来存储PumpPortalClient实例的引用
    client = None
    
    @classmethod
    def set_client(cls, client):
        """
        设置PumpPortalClient实例
        
        参数:
            client: PumpPortalClient实例
        """
        cls.client = client
    
    @classmethod
    async def process_token_creation(cls, data):
        """
        处理代币创建事件并存入数据库
        
        参数:
            data: 代币创建事件数据
        """
        try:
            # 记录日志
            logger.info(f"处理代币创建事件: {data.get('mint')}")
            
            # 检查必要字段
            if not data.get('signature') or not data.get('mint'):
                logger.warning(f"无效的代币创建数据: 缺少必要字段")
                return False
            
            # 获取代币mint地址
            mint_address = data.get('mint')
            
            # 插入数据库
            token_id = db.insert_token_event(data)
            
            if token_id:
                logger.info(f"代币 {mint_address} 已成功保存到数据库，ID: {token_id}")
                
                # 将新代币添加到监控列表，并订阅其交易事件
                if cls.client:
                    success = await cls.client.add_token_to_watch(mint_address)
                    if success:
                        logger.info(f"已将新代币 {mint_address} 添加到监控列表")
                    else:
                        logger.warning(f"添加新代币 {mint_address} 到监控列表失败")
                else:
                    logger.warning("无法监控新代币交易: 客户端未设置")
                
                return True
            else:
                logger.error(f"代币 {mint_address} 保存失败")
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
        required_fields = ['signature', 'mint', 'traderPublicKey']
        for field in required_fields:
            if field not in data:
                logger.warning(f"无效的代币数据: 缺少字段 {field}")
                return False
        return True 