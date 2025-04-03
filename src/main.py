#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
主启动脚本
用于启动PumpPortal客户端，监听和存储事件数据
"""

import asyncio
import json
import logging
import argparse
import sys

from src.config.config import (
    LOG_LEVEL, LOG_FORMAT, 
    LISTEN_NEW_TOKEN, LISTEN_MIGRATION, QUIET_MODE,
    WATCH_ACCOUNTS, WATCH_TOKENS,
    TOKEN_REPLIES_CONFIG
)
from src.pump_portal_client import PumpPortalClient
from src.db.database import db
from src.utils.token_processor import TokenProcessor
from src.utils.trade_processor import TradeProcessor
from src.services.token_replies_service import token_replies_service
from src.utils.logger import setup_logging
from src.utils.error_handler import setup_error_handling, error_handler, async_error_handler

# 配置日志
setup_logging()
# 配置错误处理
setup_error_handling()
logger = logging.getLogger("PumpPortalMain")

# 全局客户端实例
client = None

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
            logger.error(f"代币 {data.get('name')} ({data.get('symbol')}) 存入数据库失败")

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
    logger.info(f"代币交易: {json.dumps(data, ensure_ascii=False, indent=2)}")
    
    # 使用TradeProcessor处理代币交易事件并存入数据库
    if data.get('txType') in ['buy', 'sell']:
        success = await TradeProcessor.process_trade(data)
        if success:
            logger.info(f"代币交易记录已成功存入数据库")
        else:
            logger.error(f"代币交易记录存入数据库失败")

@async_error_handler
async def main():
    """主函数"""
    global client
    
    parser = argparse.ArgumentParser(description='PumpPortal数据收集器')
    parser.add_argument('--accounts', nargs='+', help='要监控的账户地址列表（覆盖配置文件）')
    parser.add_argument('--tokens', nargs='+', help='要监控的代币地址列表（覆盖配置文件）')
    parser.add_argument('--no-new-token', action='store_true', help='不订阅新代币创建事件')
    parser.add_argument('--no-migration', action='store_true', help='不订阅迁移事件')
    parser.add_argument('--quiet', action='store_true', help='不在控制台打印事件数据')
    parser.add_argument('--config', action='store_true', help='显示当前配置信息')
    parser.add_argument('--no-replies', action='store_true', help='不启动代币回复数据采集服务')
    args = parser.parse_args()
    
    # 显示配置信息
    if args.config:
        logger.info("当前配置信息:")
        logger.info(f"监听新代币创建事件: {LISTEN_NEW_TOKEN}")
        logger.info(f"监听迁移事件: {LISTEN_MIGRATION}")
        logger.info(f"静默模式: {QUIET_MODE}")
        logger.info(f"监控账户: {WATCH_ACCOUNTS}")
        logger.info(f"监控代币: {WATCH_TOKENS}")
        logger.info(f"代币回复采集: {TOKEN_REPLIES_CONFIG['enabled']}")
        logger.info(f"回复采集间隔: {TOKEN_REPLIES_CONFIG['interval']}秒")
        logger.info(f"回复采集SOL阈值: {TOKEN_REPLIES_CONFIG['sol_threshold']}")
        return 0
    
    # 合并配置文件和命令行参数
    listen_new_token = not args.no_new_token and LISTEN_NEW_TOKEN
    listen_migration = not args.no_migration and LISTEN_MIGRATION
    quiet_mode = args.quiet or QUIET_MODE
    watch_accounts = args.accounts if args.accounts else WATCH_ACCOUNTS
    watch_tokens = args.tokens if args.tokens else WATCH_TOKENS
    enable_replies = not args.no_replies and TOKEN_REPLIES_CONFIG["enabled"]
    
    # 创建客户端实例
    client = PumpPortalClient()
    
    # 将客户端实例传递给TokenProcessor
    TokenProcessor.set_client(client)
    
    # 如果不是静默模式，注册事件处理回调
    if not quiet_mode:
        client.on_new_token(handle_new_token)
        client.on_migration(handle_migration)
        client.on_account_trade(handle_account_trade)
        client.on_token_trade(handle_token_trade)
    
    # 连接到服务器
    connected = await client.connect()
    if not connected:
        logger.error("无法连接到服务器，程序退出")
        return 1
    
    try:
        # 订阅感兴趣的事件
        if listen_new_token:
            await client.subscribe_new_token()
            logger.info("从配置中启用了新代币监听")
        
        if listen_migration:
            await client.subscribe_migration()
            logger.info("从配置中启用了迁移事件监听")
        
        # 订阅特定账户的交易
        if watch_accounts:
            await client.subscribe_account_trade(watch_accounts)
            logger.info(f"从配置中监听账户: {watch_accounts}")
        
        # 订阅特定代币的交易
        if watch_tokens:
            await client.subscribe_token_trade(watch_tokens)
            logger.info(f"从配置中监听代币: {watch_tokens}")
            logger.info(f"初始监控代币数量: {len(client.watching_tokens)}")
        
        # 启动代币回复数据采集服务
        if enable_replies:
            logger.info("启动代币回复数据采集服务...")
            await token_replies_service.start()
            logger.info(f"代币回复数据采集服务已启动，间隔: {TOKEN_REPLIES_CONFIG['interval']}秒")
        
        # 开始监听消息
        await client.listen()
    except KeyboardInterrupt:
        logger.info("用户中断，正在关闭连接...")
    except Exception as e:
        logger.error(f"发生错误: {str(e)}")
        return 1
    finally:
        # 停止代币回复数据采集服务
        if enable_replies:
            logger.info("停止代币回复数据采集服务...")
            await token_replies_service.stop()
            
        # 断开连接
        await client.disconnect()
    
    return 0

if __name__ == "__main__":
    sys.exit(asyncio.run(main())) 