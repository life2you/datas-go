#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PumpPortal实时数据客户端
连接到PumpPortal WebSocket API获取实时交易和代币创建数据，并存储到PostgreSQL数据库
"""

import asyncio
import json
import websockets
import logging
from typing import List, Dict, Any, Optional

from src.config.config import WEBSOCKET_URI, LOG_LEVEL, LOG_FORMAT
from src.db.database import db
from src.models.token_event import TokenEvent

# 配置日志
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format=LOG_FORMAT
)
logger = logging.getLogger("PumpPortalClient")

class PumpPortalClient:
    """
    PumpPortal WebSocket API客户端
    用于订阅和接收实时数据流，并存储到数据库
    """
    
    def __init__(self, uri: str = WEBSOCKET_URI):
        """
        初始化PumpPortal客户端
        
        参数:
            uri: WebSocket服务器URI
        """
        self.uri = uri
        self.websocket = None
        self.running = False
        self.callbacks = {
            "new_token": [],
            "migration": [],
            "account_trade": [],
            "token_trade": []
        }
        self.batch_size = 50  # 批量插入的大小
        self.event_buffer = []  # 事件缓冲区
        
        # 监控的代币和账户列表
        self.watching_tokens = set()  # 使用集合避免重复
        self.watching_accounts = set()  # 使用集合避免重复
    
    async def connect(self) -> bool:
        """
        连接到WebSocket服务器
        
        返回:
            bool: 连接是否成功
        """
        try:
            self.websocket = await websockets.connect(self.uri)
            self.running = True
            logger.info(f"已连接到 {self.uri}")
            
            # 连接数据库
            if not db.connect():
                logger.warning("无法连接到数据库，将不会存储数据")
            
            return True
        except Exception as e:
            logger.error(f"连接失败: {str(e)}")
            return False
    
    async def disconnect(self) -> None:
        """
        断开与WebSocket服务器的连接
        """
        if self.websocket:
            await self.websocket.close()
            self.running = False
            logger.info("已断开与WebSocket服务器的连接")
        
        # 断开数据库连接
        db.close()
    
    async def send_payload(self, payload: Dict[str, Any]) -> None:
        """
        发送payload到WebSocket服务器
        
        参数:
            payload: 要发送的JSON payload
        """
        if not self.websocket:
            logger.error("未连接到服务器")
            return
        
        try:
            await self.websocket.send(json.dumps(payload))
            logger.debug(f"已发送: {payload}")
        except Exception as e:
            logger.error(f"发送失败: {str(e)}")
    
    async def subscribe_new_token(self) -> None:
        """
        订阅代币创建事件
        """
        payload = {
            "method": "subscribeNewToken",
        }
        await self.send_payload(payload)
        logger.info("已订阅代币创建事件")
    
    async def subscribe_migration(self) -> None:
        """
        订阅迁移事件
        """
        payload = {
            "method": "subscribeMigration",
        }
        await self.send_payload(payload)
        logger.info("已订阅迁移事件")
    
    async def subscribe_account_trade(self, accounts: List[str]) -> None:
        """
        订阅账户交易事件
        
        参数:
            accounts: 要监控的账户地址列表
        """
        if not accounts:
            return
            
        # 将新账户添加到监控列表
        for account in accounts:
            if account:
                self.watching_accounts.add(account)
        
        payload = {
            "method": "subscribeAccountTrade",
            "keys": accounts
        }
        await self.send_payload(payload)
        logger.info(f"已订阅账户交易事件: {accounts}")
    
    async def subscribe_token_trade(self, tokens: List[str]) -> None:
        """
        订阅代币交易事件
        
        参数:
            tokens: 要监控的代币合约地址列表
        """
        if not tokens:
            return
            
        # 将新代币添加到监控列表
        for token in tokens:
            if token:
                self.watching_tokens.add(token)
        
        payload = {
            "method": "subscribeTokenTrade",
            "keys": tokens
        }
        await self.send_payload(payload)
        logger.info(f"已订阅代币交易事件: {tokens}")
    
    async def unsubscribe_new_token(self) -> None:
        """
        取消订阅代币创建事件
        """
        payload = {
            "method": "unsubscribeNewToken",
        }
        await self.send_payload(payload)
        logger.info("已取消订阅代币创建事件")
    
    async def unsubscribe_account_trade(self) -> None:
        """
        取消订阅账户交易事件
        """
        payload = {
            "method": "unsubscribeAccountTrade",
        }
        await self.send_payload(payload)
        logger.info("已取消订阅账户交易事件")
    
    async def unsubscribe_token_trade(self) -> None:
        """
        取消订阅代币交易事件
        """
        payload = {
            "method": "unsubscribeTokenTrade",
        }
        await self.send_payload(payload)
        logger.info("已取消订阅代币交易事件")
    
    def on_new_token(self, callback):
        """
        注册代币创建事件回调函数
        
        参数:
            callback: 回调函数，接收事件数据作为参数
        """
        self.callbacks["new_token"].append(callback)
        return self
    
    def on_migration(self, callback):
        """
        注册迁移事件回调函数
        
        参数:
            callback: 回调函数，接收事件数据作为参数
        """
        self.callbacks["migration"].append(callback)
        return self
    
    def on_account_trade(self, callback):
        """
        注册账户交易事件回调函数
        
        参数:
            callback: 回调函数，接收事件数据作为参数
        """
        self.callbacks["account_trade"].append(callback)
        return self
    
    def on_token_trade(self, callback):
        """
        注册代币交易事件回调函数
        
        参数:
            callback: 回调函数，接收事件数据作为参数
        """
        self.callbacks["token_trade"].append(callback)
        return self
    
    async def process_message(self, message: Dict[str, Any]) -> None:
        """
        处理接收到的消息
        
        参数:
            message: 接收到的消息
        """
        tx_type = message.get('txType')
        
        # 处理代币创建事件
        if tx_type == 'create':
            # 新代币创建事件
            try:
                # 添加到缓冲区并在缓冲区满时批量处理
                self.event_buffer.append(message)
                if len(self.event_buffer) >= self.batch_size:
                    await self._flush_event_buffer()
                
                # 触发回调函数
                for callback in self.callbacks["new_token"]:
                    try:
                        await callback(message)
                    except Exception as e:
                        logger.error(f"执行新代币回调失败: {str(e)}")
            except Exception as e:
                logger.error(f"处理代币创建事件失败: {str(e)}")
        
        # 处理迁移事件
        elif tx_type == 'migrate':
            for callback in self.callbacks["migration"]:
                try:
                    await callback(message)
                except Exception as e:
                    logger.error(f"执行迁移回调失败: {str(e)}")
        
        # 处理交易事件
        elif tx_type in ['buy', 'sell']:
            account_callbacks = self.callbacks["account_trade"]
            token_callbacks = self.callbacks["token_trade"]
            
            for callback in account_callbacks:
                try:
                    await callback(message)
                except Exception as e:
                    logger.error(f"执行账户交易回调失败: {str(e)}")
            
            for callback in token_callbacks:
                try:
                    await callback(message)
                except Exception as e:
                    logger.error(f"执行代币交易回调失败: {str(e)}")
        
        # 处理未知消息格式
        else:
            logger.warning(f"收到未知消息格式: {message}")
    
    def _should_store_event(self, message: Dict[str, Any]) -> bool:
        """
        判断事件是否应该存储到数据库
        
        参数:
            message: 接收到的消息
            
        返回:
            bool: 是否应该存储
        """
        # 包含signature和mint字段的消息会被存储
        return 'signature' in message and 'mint' in message
    
    async def _flush_event_buffer(self) -> None:
        """
        将缓冲区中的事件批量写入数据库
        """
        if not self.event_buffer:
            return
        
        try:
            count = db.insert_many_token_events(self.event_buffer)
            logger.info(f"成功批量插入 {count} 条事件记录")
        except Exception as e:
            logger.error(f"批量插入事件记录失败: {str(e)}")
        
        # 清空缓冲区
        self.event_buffer = []
    
    async def listen(self) -> None:
        """
        开始监听消息
        """
        if not self.websocket:
            logger.error("未连接到服务器")
            return
        
        try:
            logger.info("开始监听消息")
            
            while self.running:
                try:
                    message = await self.websocket.recv()
                    data = json.loads(message)
                    await self.process_message(data)
                except json.JSONDecodeError:
                    logger.error(f"无效的JSON: {message}")
                except Exception as e:
                    logger.error(f"接收消息错误: {str(e)}")
                    await asyncio.sleep(1)  # 防止错误消息导致CPU占用过高
        finally:
            # 确保所有缓冲数据都写入数据库
            await self._flush_event_buffer()
            
            # 关闭连接
            await self.disconnect()
    
    async def connect_and_listen(self) -> None:
        """
        连接并开始监听消息的综合方法
        先连接到WebSocket服务器，然后开始订阅事件和监听消息
        """
        try:
            # 连接到WebSocket服务器
            if await self.connect():
                # 从数据库加载所有代币到监控列表
                await self.load_tokens_from_database()
                
                # 订阅事件
                from src.config.config import LISTEN_NEW_TOKEN, LISTEN_MIGRATION, WATCH_ACCOUNTS, WATCH_TOKENS
                
                if LISTEN_NEW_TOKEN:
                    await self.subscribe_new_token()
                
                if LISTEN_MIGRATION:
                    await self.subscribe_migration()
                
                if WATCH_ACCOUNTS:
                    await self.subscribe_account_trade(WATCH_ACCOUNTS)
                
                if WATCH_TOKENS:
                    # 合并配置中的代币和从数据库加载的代币
                    config_tokens = [token for token in WATCH_TOKENS if token not in self.watching_tokens]
                    if config_tokens:
                        await self.subscribe_token_trade(config_tokens)
                
                # 开始监听消息
                await self.listen()
            else:
                logger.error("连接失败，无法开始监听")
        except Exception as e:
            logger.error(f"连接和监听过程中发生错误: {str(e)}")
            # 确保连接关闭
            await self.disconnect()
    
    async def add_token_to_watch(self, token_address: str) -> bool:
        """
        动态添加代币到监控列表
        
        参数:
            token_address: 要监控的代币地址
            
        返回:
            bool: 是否成功添加
        """
        if not token_address:
            logger.warning("无效的代币地址")
            return False
            
        # 如果已经在监控列表中，跳过
        if token_address in self.watching_tokens:
            logger.debug(f"代币 {token_address} 已在监控列表中")
            return True
            
        # 添加到监控列表
        self.watching_tokens.add(token_address)
        
        # 如果已经连接，立即订阅
        if self.websocket and self.running:
            try:
                await self.subscribe_token_trade([token_address])
                logger.info(f"已添加代币 {token_address} 到监控列表并订阅交易")
                return True
            except Exception as e:
                logger.error(f"订阅代币 {token_address} 交易失败: {str(e)}")
                self.watching_tokens.remove(token_address)  # 移除失败的代币
                return False
        
        return True
    
    async def add_account_to_watch(self, account_address: str) -> bool:
        """
        动态添加账户到监控列表
        
        参数:
            account_address: 要监控的账户地址
            
        返回:
            bool: 是否成功添加
        """
        if not account_address:
            logger.warning("无效的账户地址")
            return False
            
        # 如果已经在监控列表中，跳过
        if account_address in self.watching_accounts:
            logger.debug(f"账户 {account_address} 已在监控列表中")
            return True
            
        # 添加到监控列表
        self.watching_accounts.add(account_address)
        
        # 如果已经连接，立即订阅
        if self.websocket and self.running:
            try:
                await self.subscribe_account_trade([account_address])
                logger.info(f"已添加账户 {account_address} 到监控列表并订阅交易")
                return True
            except Exception as e:
                logger.error(f"订阅账户 {account_address} 交易失败: {str(e)}")
                self.watching_accounts.remove(account_address)  # 移除失败的账户
                return False
        
        return True
    
    async def load_tokens_from_database(self) -> None:
        """
        从数据库加载所有代币到监控列表中
        用于系统重启后恢复所有代币监控
        """
        try:
            # 查询所有代币
            query = "SELECT DISTINCT mint FROM token WHERE mint IS NOT NULL"
            cursor = db.execute(query)
            
            if not cursor:
                logger.error("从数据库加载代币失败：无法执行查询")
                return
            
            tokens = cursor.fetchall()
            if not tokens:
                logger.info("数据库中没有找到代币记录")
                return
            
            # 提取代币地址列表
            token_addresses = [token['mint'] for token in tokens if token.get('mint')]
            
            # 按批次添加代币到监控列表，每批最多100个
            batch_size = 100
            for i in range(0, len(token_addresses), batch_size):
                batch = token_addresses[i:i+batch_size]
                
                # 将代币添加到监控列表
                for token in batch:
                    self.watching_tokens.add(token)
                
                # 如果已经连接，立即订阅
                if self.websocket and self.running:
                    try:
                        await self.subscribe_token_trade(batch)
                        logger.info(f"已添加一批 {len(batch)} 个代币到监控列表并订阅交易")
                    except Exception as e:
                        logger.error(f"订阅代币批次失败: {str(e)}")
            
            logger.info(f"成功从数据库加载了 {len(token_addresses)} 个代币到监控列表")
        except Exception as e:
            logger.error(f"从数据库加载代币失败: {str(e)}") 