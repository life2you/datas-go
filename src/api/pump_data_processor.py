#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Pump数据处理模块
处理Pump API返回的回复数据，存入数据库，并根据条件自动查询多个token的回复
"""

import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

from src.api.pump_api import PumpApiClient
from src.db.database import db

logger = logging.getLogger(__name__)


class PumpDataProcessor:
    """Pump数据处理器，处理API数据并存入数据库"""
    
    def __init__(self, cookie: str = "", use_proxy: bool = False):
        """
        初始化数据处理器
        
        参数:
            cookie: 可选的Cookie字符串，用于身份验证
            use_proxy: 是否使用代理
        """
        self.api_client = PumpApiClient(cookie=cookie, use_proxy=use_proxy)
    
    def close(self):
        """关闭API客户端连接"""
        self.api_client.close()
    
    def __enter__(self):
        """支持上下文管理器"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """支持上下文管理器，自动关闭连接"""
        self.close()
    
    def timestamp_to_datetime(self, timestamp: int) -> str:
        """
        将毫秒时间戳转换为日期时间字符串
        
        参数:
            timestamp: 毫秒时间戳
            
        返回:
            日期时间字符串，格式为 YYYY-MM-DD HH:MM:SS
        """
        try:
            dt = datetime.fromtimestamp(timestamp / 1000.0)
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except Exception as e:
            logger.error(f"时间戳转换失败: {str(e)}")
            return None
    
    def process_reply(self, reply: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理单条回复数据，提取关键字段
        
        参数:
            reply: 回复数据字典
            
        返回:
            处理后的数据字典，包含关键字段
        """
        processed_data = {
            'mint': reply.get('mint'),
            'is_buy': reply.get('is_buy'),
            'sol_amount': reply.get('sol_amount'),
            'user': reply.get('user'),
            'timestamp': reply.get('timestamp'),
            'datetime': self.timestamp_to_datetime(reply.get('timestamp')) if reply.get('timestamp') else None,
            'text': reply.get('text'),
            'username': reply.get('username'),
            'total_likes': reply.get('total_likes')
        }
        return processed_data
    
    def save_replies_to_db(self, replies: List[Dict[str, Any]]) -> int:
        """
        将处理后的回复数据保存到数据库
        
        参数:
            replies: 处理后的回复数据列表
            
        返回:
            成功保存的记录数量
        """
        if not replies:
            return 0
            
        # 构建SQL插入语句
        query = """
        INSERT INTO token_replies (
            mint, is_buy, sol_amount, user_address, timestamp, datetime, 
            text, username, total_likes
        ) VALUES (
            %(mint)s, %(is_buy)s, %(sol_amount)s, %(user)s, %(timestamp)s, %(datetime)s,
            %(text)s, %(username)s, %(total_likes)s
        )
        ON CONFLICT (mint, user_address, timestamp) DO NOTHING
        RETURNING id;
        """
        
        # 批量插入
        saved_count = 0
        for reply in replies:
            try:
                cursor = db.execute(query, reply)
                if cursor and cursor.rowcount > 0:
                    saved_count += 1
            except Exception as e:
                logger.error(f"保存回复数据失败: {str(e)}")
        
        logger.info(f"成功保存 {saved_count} 条回复数据")
        return saved_count
    
    def get_token_reply_count(self, mint: str) -> int:
        """
        获取数据库中指定token的回复数量
        
        参数:
            mint: token的mint地址
            
        返回:
            回复数量
        """
        query = "SELECT COUNT(*) as count FROM token_replies WHERE mint = %s"
        
        try:
            cursor = db.execute(query, (mint,))
            if cursor:
                result = cursor.fetchone()
                return result['count'] if result else 0
        except Exception as e:
            logger.error(f"查询token回复数量失败: {str(e)}")
        
        return 0
    
    def get_tokens_with_sol_gt(self, sol_amount: float = 35.0) -> List[Dict[str, Any]]:
        """
        获取bonding curve中SOL数量大于指定值的token列表
        
        参数:
            sol_amount: SOL数量阈值
            
        返回:
            符合条件的token列表
        """
        query = """
        SELECT mint, name, symbol, v_sol_in_bonding_curve 
        FROM token 
        WHERE v_sol_in_bonding_curve > %s
        ORDER BY v_sol_in_bonding_curve DESC
        """
        
        try:
            cursor = db.execute(query, (sol_amount,))
            if cursor:
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"查询高价值token失败: {str(e)}")
        
        return []
    
    def fetch_token_replies(self, 
                            token_mint: str, 
                            limit: int = 1000,
                            check_db_first: bool = True) -> List[Dict[str, Any]]:
        """
        获取并处理token的回复数据
        
        参数:
            token_mint: token的mint地址
            limit: 每页回复数量
            check_db_first: 是否先检查数据库中的数量
            
        返回:
            处理后的回复数据列表
        """
        all_replies = []
        offset = 0
        has_more = True
        
        # 如果需要先检查数据库
        if check_db_first:
            db_count = self.get_token_reply_count(token_mint)
            logger.info(f"数据库中已有 {db_count} 条 {token_mint} 的回复")
        
        # 循环获取所有分页数据
        while has_more:
            try:
                # 获取回复数据
                response = self.api_client.get_token_replies(token_mint, limit=limit, offset=offset)
                
                # 获取当前页的回复列表
                if 'replies' in response and response['replies']:
                    current_page_replies = response['replies']
                    total_offset = response.get('offset', 0)
                    
                    # 处理回复数据
                    processed_replies = [self.process_reply(reply) for reply in current_page_replies]
                    all_replies.extend(processed_replies)
                    
                    # 检查是否有更多数据
                    has_more = response.get('hasMore', False)
                    
                    # 如果先前检查了数据库，且数据库数量等于总数量，则跳过后续处理
                    if check_db_first and db_count == total_offset:
                        logger.info(f"数据库中已有所有 {token_mint} 的回复数据，跳过处理")
                        return []
                    
                    # 更新偏移量
                    if has_more:
                        offset += len(current_page_replies)
                else:
                    # 没有回复数据，结束循环
                    has_more = False
                
                # 添加延迟避免API速率限制
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"获取token回复失败: {str(e)}")
                break
        
        return all_replies
    
    def process_high_value_tokens(self, sol_threshold: float = 35.0, limit: int = 1000, cookie: str = None, use_proxy: bool = False):
        """
        处理高价值token的回复数据
        
        参数:
            sol_threshold: SOL数量阈值
            limit: 每页回复数量
            cookie: 可选的Cookie字符串，用于API身份验证
            use_proxy: 是否使用代理
        """
        # 如果提供了新的cookie，则更新API客户端
        if cookie is not None:
            self.api_client.update_cookie(cookie)
        
        # 获取高价值token列表
        high_value_tokens = self.get_tokens_with_sol_gt(sol_threshold)
        logger.info(f"找到 {len(high_value_tokens)} 个bonding curve中SOL大于 {sol_threshold} 的token")
        
        # 处理每个token的回复
        for i, token in enumerate(high_value_tokens):
            mint = token['mint']
            name = token.get('name', 'Unknown')
            symbol = token.get('symbol', 'Unknown')
            sol_value = token.get('v_sol_in_bonding_curve', 0)
            
            logger.info(f"处理第 {i+1}/{len(high_value_tokens)} 个token: {name} ({symbol}), "
                       f"Mint: {mint}, SOL: {sol_value}")
            
            # 获取并处理回复
            replies = self.fetch_token_replies(mint, limit=limit)
            
            # 如果获取到回复，保存到数据库
            if replies:
                saved_count = self.save_replies_to_db(replies)
                logger.info(f"为token {name} ({mint}) 保存了 {saved_count} 条新回复")
            else:
                logger.info(f"没有新的回复数据需要保存，或者API返回为空")
            
            # 添加延迟避免API速率限制
            time.sleep(2)


def ensure_token_replies_table():
    """确保token_replies表存在"""
    query = """
    CREATE TABLE IF NOT EXISTS token_replies (
        id SERIAL PRIMARY KEY,
        mint TEXT NOT NULL,
        is_buy BOOLEAN,
        sol_amount NUMERIC(20, 9),
        user_address TEXT NOT NULL,
        timestamp BIGINT NOT NULL,
        datetime TIMESTAMP,
        text TEXT,
        username TEXT,
        total_likes INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(mint, user_address, timestamp)
    );
    
    CREATE INDEX IF NOT EXISTS idx_token_replies_mint ON token_replies(mint);
    CREATE INDEX IF NOT EXISTS idx_token_replies_user ON token_replies(user_address);
    CREATE INDEX IF NOT EXISTS idx_token_replies_timestamp ON token_replies(timestamp);
    CREATE INDEX IF NOT EXISTS idx_token_replies_datetime ON token_replies(datetime);
    """
    
    try:
        db.execute(query)
        logger.info("已确保token_replies表存在")
        return True
    except Exception as e:
        logger.error(f"创建token_replies表失败: {str(e)}")
        return False


def main():
    """主函数，处理高价值token的回复数据"""
    # 确保表存在
    if not ensure_token_replies_table():
        logger.error("无法创建必要的数据库表，程序退出")
        return 1
    
    # 创建数据处理器
    with PumpDataProcessor() as processor:
        # 处理高价值token的回复
        processor.process_high_value_tokens(sol_threshold=35.0)
    
    return 0


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # 运行主函数
    exit_code = main()
    exit(exit_code) 