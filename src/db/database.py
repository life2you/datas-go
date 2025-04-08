#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据库连接模块
处理与PostgreSQL数据库的连接和交互
"""

import logging
import threading
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor, execute_values
from src.core.config import DB_CONFIG
import time
from datetime import datetime
from typing import Optional, Dict, List, Any, Tuple

logger = logging.getLogger(__name__)

class ConnectionPool:
    """PostgreSQL数据库连接池"""
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ConnectionPool, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.min_connections = 5
        self.max_connections = 20
        self.pool = None
        self._initialized = True
        self._create_pool()
    
    def _create_pool(self):
        """创建数据库连接池"""
        try:
            # 关闭现有连接池
            if self.pool:
                self.pool.closeall()
                
            # 创建连接池
            self.pool = pool.ThreadedConnectionPool(
                self.min_connections,
                self.max_connections,
                host=DB_CONFIG['host'],
                port=DB_CONFIG['port'],
                database=DB_CONFIG['database'],
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password']
            )
            logger.info(f"成功创建数据库连接池: min={self.min_connections}, max={self.max_connections}")
            logger.info(f"连接到数据库 {DB_CONFIG['database']} @ {DB_CONFIG['host']}:{DB_CONFIG['port']}")
            return True
        except Exception as e:
            logger.error(f"创建连接池失败: {str(e)}", exc_info=True)
            return False
    
    def get_connection(self):
        """从连接池获取一个连接"""
        if not self.pool:
            if not self._create_pool():
                return None
        
        try:
            conn = self.pool.getconn()
            conn.autocommit = True  # 默认设置自动提交
            return conn
        except Exception as e:
            logger.error(f"获取数据库连接失败: {str(e)}", exc_info=True)
            # 尝试重建连接池
            self._create_pool()
            return None
    
    def release_connection(self, conn):
        """将连接归还给连接池"""
        if conn and self.pool:
            try:
                self.pool.putconn(conn)
                return True
            except Exception as e:
                logger.error(f"归还连接到连接池失败: {str(e)}", exc_info=True)
                try:
                    conn.close()
                except:
                    pass
                return False
        return False
    
    def close_all(self):
        """关闭所有连接"""
        if self.pool:
            try:
                self.pool.closeall()
                logger.info("已关闭所有数据库连接")
                self.pool = None
                return True
            except Exception as e:
                logger.error(f"关闭所有数据库连接失败: {str(e)}", exc_info=True)
                return False
        return True

class Database:
    """PostgreSQL数据库连接和操作类"""
    
    def __init__(self):
        """初始化数据库连接"""
        self.max_retries = 3
        self.retry_delay = 1  # 秒
        self.thread_local = threading.local()  # 线程本地存储
        self.connection_pool = ConnectionPool()
    
    def _get_thread_connection(self):
        """获取当前线程的数据库连接"""
        if not hasattr(self.thread_local, 'conn') or not self.thread_local.conn:
            self.thread_local.conn = self.connection_pool.get_connection()
        return self.thread_local.conn
    
    def _get_thread_cursor(self):
        """获取当前线程的游标"""
        conn = self._get_thread_connection()
        if not conn:
            return None
            
        if not hasattr(self.thread_local, 'cursor') or not self.thread_local.cursor or self.thread_local.cursor.closed:
            self.thread_local.cursor = conn.cursor(cursor_factory=RealDictCursor)
        return self.thread_local.cursor
    
    def _release_resources(self):
        """释放当前线程的连接资源"""
        try:
            if hasattr(self.thread_local, 'cursor') and self.thread_local.cursor:
                self.thread_local.cursor.close()
                self.thread_local.cursor = None
        except:
            pass
            
        try:
            if hasattr(self.thread_local, 'conn') and self.thread_local.conn:
                self.connection_pool.release_connection(self.thread_local.conn)
                self.thread_local.conn = None
        except:
            pass
    
    def connect(self):
        """连接到PostgreSQL数据库"""
        # 使用连接池获取连接
        conn = self._get_thread_connection()
        return conn is not None
    
    def get_cursor(self):
        """获取数据库游标"""
        return self._get_thread_cursor()
    
    def close(self):
        """关闭数据库连接"""
        self._release_resources()
        logger.info("线程数据库连接已关闭")
    
    def execute(self, query, params=None):
        """执行SQL查询语句"""
        for attempt in range(self.max_retries):
            cursor = self.get_cursor()
            if cursor is None:
                logger.error("无法获取数据库游标", exc_info=True)
                return None
            
            try:
                # 打印SQL语句和参数
                formatted_query = query
                if params:
                    try:
                        if isinstance(params, dict):
                            for key, value in params.items():
                                placeholder = f"%({key})s"
                                if isinstance(value, str):
                                    sql_value = f"'{value}'"
                                elif value is None:
                                    sql_value = "NULL"
                                else:
                                    sql_value = str(value)
                                formatted_query = formatted_query.replace(placeholder, sql_value)
                        elif isinstance(params, (list, tuple)):
                            for i, value in enumerate(params):
                                if isinstance(value, str):
                                    sql_value = f"'{value}'"
                                elif value is None:
                                    sql_value = "NULL"
                                else:
                                    sql_value = str(value)
                                formatted_query = formatted_query.replace("%s", sql_value, 1)
                    except Exception as format_error:
                        logger.warning(f"无法格式化SQL查询: {str(format_error)}", exc_info=True)
                        formatted_query = f"SQL: {query}, 参数: {params}"
                
                logger.debug(f"执行SQL: {formatted_query}")
                
                cursor.execute(query, params or {})
                return cursor
            except Exception as e:
                if attempt < self.max_retries - 1:
                    logger.warning(f"执行SQL失败，尝试重试 ({attempt + 1}/{self.max_retries}): {str(e)}")
                    time.sleep(self.retry_delay)
                    # 重新连接数据库
                    self._release_resources()
                    self.connect()
                else:
                    logger.error(f"执行SQL失败: {str(e)}", exc_info=True)
                    logger.error(f"SQL: {query}")
                    logger.error(f"参数: {params}")
                    if hasattr(self.thread_local, 'conn') and self.thread_local.conn:
                        try:
                            self.thread_local.conn.rollback()
                            logger.info("事务已回滚")
                        except Exception as rollback_error:
                            logger.error(f"回滚事务失败: {str(rollback_error)}", exc_info=True)
                    return None
    
    def insert_token_event(self, event_data):
        """插入代币事件数据到token表"""
        # 先检查是否已存在相同signature的记录
        check_query = """
        SELECT id FROM token WHERE signature = %(signature)s LIMIT 1
        """
        cursor = self.execute(check_query, {'signature': event_data.get('signature')})
        if cursor and cursor.rowcount > 0:
            # 已存在相同signature的记录，返回其ID
            result = cursor.fetchone()
            logger.info(f"代币记录已存在，signature: {event_data.get('signature')}")
            return result['id']
            
        # 不存在相同记录，执行插入
        query = """
        INSERT INTO token (
            signature, mint, trader_public_key, 
            initial_buy, sol_amount, bonding_curve_key,
            v_tokens_in_bonding_curve, v_sol_in_bonding_curve, market_cap_sol,
            name, symbol, uri, pool
        ) VALUES (
            %(signature)s, %(mint)s, %(traderPublicKey)s,
            %(initialBuy)s, %(solAmount)s, %(bondingCurveKey)s,
            %(vTokensInBondingCurve)s, %(vSolInBondingCurve)s, %(marketCapSol)s,
            %(name)s, %(symbol)s, %(uri)s, %(pool)s
        ) RETURNING id;
        """
        cursor = self.execute(query, event_data)
        if cursor:
            result = cursor.fetchone()
            return result['id'] if result else None
        return None
    
    def insert_many_token_events(self, events):
        """批量插入多个代币事件"""
        if not events:
            return 0
        
        cursor = self.get_cursor()
        if cursor is None:
            return 0
        
        try:
            # 提取所有代币的signatures
            signatures = [event.get('signature') for event in events if event.get('signature')]
            
            if not signatures:
                return 0
                
            # 查询已存在的signatures
            placeholders = ', '.join(['%s'] * len(signatures))
            check_query = f"""
            SELECT signature FROM token 
            WHERE signature IN ({placeholders})
            """
            cursor.execute(check_query, signatures)
            existing_signatures = set(row['signature'] for row in cursor.fetchall())
            
            # 过滤掉已存在的代币记录
            new_events = [event for event in events if event.get('signature') not in existing_signatures]
            
            if not new_events:
                logger.info(f"所有代币记录已存在，跳过插入")
                return 0
                
            logger.info(f"已过滤掉 {len(events) - len(new_events)} 条重复代币记录")
            
            query = """
            INSERT INTO token (
                signature, mint, trader_public_key, 
                initial_buy, sol_amount, bonding_curve_key,
                v_tokens_in_bonding_curve, v_sol_in_bonding_curve, market_cap_sol,
                name, symbol, uri, pool
            ) VALUES %s
            """
            
            # 准备数据
            template = "(%(signature)s, %(mint)s, %(trader_public_key)s, " \
                      "%(initial_buy)s, %(sol_amount)s, %(bonding_curve_key)s, " \
                      "%(v_tokens_in_bonding_curve)s, %(v_sol_in_bonding_curve)s, %(market_cap_sol)s, " \
                      "%(name)s, %(symbol)s, %(uri)s, %(pool)s)"
            
            # 转换字段名
            normalized_events = []
            for event in new_events:
                normalized_event = {
                    'signature': event.get('signature'),
                    'mint': event.get('mint'),
                    'trader_public_key': event.get('traderPublicKey'),
                    'initial_buy': event.get('initialBuy'),
                    'sol_amount': event.get('solAmount'),
                    'bonding_curve_key': event.get('bondingCurveKey'),
                    'v_tokens_in_bonding_curve': event.get('vTokensInBondingCurve'),
                    'v_sol_in_bonding_curve': event.get('vSolInBondingCurve'),
                    'market_cap_sol': event.get('marketCapSol'),
                    'name': event.get('name'),
                    'symbol': event.get('symbol'),
                    'uri': event.get('uri'),
                    'pool': event.get('pool')
                }
                normalized_events.append(normalized_event)
            
            result_count = 0
            if normalized_events:
                # 执行批量插入
                execute_values(cursor, query, normalized_events, template)
                result_count = cursor.rowcount
                
            return result_count
        except Exception as e:
            logger.error(f"批量插入代币数据失败: {str(e)}", exc_info=True)
            return 0
    
    def insert_trade_record(self, data):
        """
        插入交易记录到token_trade表
        
        参数:
            data: 交易数据
            
        返回:
            插入记录的ID，如果插入失败则返回None
        """
        try:
            # 先检查是否已存在相同signature的记录
            check_query = """
            SELECT id FROM token_trade WHERE signature = %s LIMIT 1
            """
            cursor = self.execute(check_query, (data.get('signature'),))
            if cursor and cursor.rowcount > 0:
                # 已存在相同signature的记录，返回其ID
                result = cursor.fetchone()
                # 如果result is none，则返回None
                if result is None:
                    return None
                return result['id']
            
            # 准备插入字段和值
            fields = []
            placeholders = []
            values = {}
            
            field_map = {
                'signature': 'signature',
                'mint': 'mint',
                'trader_public_key': 'traderPublicKey',
                'tx_type': 'txType',
                'token_amount': 'tokenAmount',
                'sol_amount': 'solAmount',
                'new_token_balance': 'newTokenBalance',
                'bonding_curve_key': 'bondingCurveKey',
                'v_tokens_in_bonding_curve': 'vTokensInBondingCurve',
                'v_sol_in_bonding_curve': 'vSolInBondingCurve',
                'market_cap_sol': 'marketCapSol',
                'pool': 'pool'
            }
            
            for db_field, data_field in field_map.items():
                if data_field in data and data[data_field] is not None:
                    fields.append(db_field)
                    placeholders.append(f"%({db_field})s")
                    values[db_field] = data[data_field]
            
            # 构建插入语句
            query = f"""
            INSERT INTO token_trade (
                {', '.join(fields)}
            ) VALUES (
                {', '.join(placeholders)}
            ) RETURNING id;
            """
            
            cursor = self.execute(query, values)
            if cursor:
                result = cursor.fetchone()
                record_id = result['id'] if result else None
            else:
                return None
                
            if not record_id:
                logger.error("插入交易记录失败: 未返回ID", exc_info=True)
                return None
                
            logger.info(f"成功插入交易记录，ID: {record_id}")
            
            # 检查token表是否存在updated_at列
            check_column_query = """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'token' 
            AND column_name = 'updated_at'
            """
            
            cursor = self.execute(check_column_query)
            column_exists = cursor.fetchone() is not None
            
            # 如果不存在，添加该列
            if not column_exists:
                add_column_query = """
                ALTER TABLE token 
                ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                """
                self.execute(add_column_query)
                logger.info("已为token表添加updated_at列")
            
            # 更新token表的数据（bonding curve等）
            update_query = """
            UPDATE token 
            SET v_tokens_in_bonding_curve = %s,
                v_sol_in_bonding_curve = %s,
                market_cap_sol = %s,
                updated_at = NOW()
            WHERE mint = %s
            """
            
            self.execute(update_query, (
                data.get('vTokensInBondingCurve'),
                data.get('vSolInBondingCurve'),
                data.get('marketCapSol'),
                data.get('mint')
            ))
            
            logger.info(f"更新了代币 {data.get('mint')} 的bonding curve数据")
            
            return record_id
        except Exception as e:
            logger.error(f"插入交易记录失败: {str(e)}", exc_info=True)
            self.rollback()
            return None
    
    def _update_tokens_from_trades(self, trades):
        """
        从交易记录更新token表中的绑定曲线数据
        
        参数:
            trades: 交易记录列表
        """
        # 按mint分组，获取每个代币的最新交易
        latest_trades_by_mint = {}
        for trade in trades:
            mint = trade.get('mint')
            if not mint:
                continue
                
            # 如果已存在相同mint的交易，比较signature以确定哪个更新
            if mint in latest_trades_by_mint:
                # 这里假设signature越长，交易越新
                if len(trade.get('signature', '')) > len(latest_trades_by_mint[mint].get('signature', '')):
                    latest_trades_by_mint[mint] = trade
            else:
                latest_trades_by_mint[mint] = trade
        
        if not latest_trades_by_mint:
            return
            
        # 批量更新token表
        self._batch_update_token_bonding_curve_data(latest_trades_by_mint)
    
    def _batch_update_token_bonding_curve_data(self, trades_by_mint):
        """
        批量更新token表中的绑定曲线数据
        
        参数:
            trades_by_mint: 以mint为键的交易记录字典
        """
        if not trades_by_mint:
            return
            
        cursor = self.get_cursor()
        if cursor is None:
            return
            
        try:
            # 尝试获取SOL价格用于计算美元价格
            sol_usd_price = 0
            try:
                from src.core.services.sol_price_service import sol_price_service
                sol_usd_price = sol_price_service.get_current_price()
                if sol_usd_price > 0:
                    logger.info(f"批量更新将使用SOL价格: ${sol_usd_price:.2f}")
            except Exception as e:
                logger.error(f"获取SOL价格失败: {str(e)}", exc_info=True)
            
            # 构建批量更新语句
            case_statements = []
            params = {}
            
            for i, (mint, trade) in enumerate(trades_by_mint.items()):
                mint_param = f"mint_{i}"
                v_tokens_param = f"v_tokens_{i}"
                v_sol_param = f"v_sol_{i}"
                market_cap_param = f"market_cap_{i}"
                usd_price_param = f"usd_price_{i}"
                
                params[mint_param] = mint
                
                v_tokens = trade.get('vTokensInBondingCurve')
                v_sol = trade.get('vSolInBondingCurve')
                market_cap_sol = trade.get('marketCapSol')
                
                case_statements.append(f"WHEN mint = %({mint_param})s THEN")
                
                updates = []
                if v_tokens is not None:
                    params[v_tokens_param] = v_tokens
                    updates.append(f"%({v_tokens_param})s")
                else:
                    updates.append("v_tokens_in_bonding_curve")
                    
                if v_sol is not None:
                    params[v_sol_param] = v_sol
                    updates.append(f"%({v_sol_param})s")
                else:
                    updates.append("v_sol_in_bonding_curve")
                    
                if market_cap_sol is not None:
                    params[market_cap_param] = market_cap_sol
                    updates.append(f"%({market_cap_param})s")
                else:
                    updates.append("market_cap_sol")
                    
                # 计算美元价格 - 仅当同时有代币数量和SOL数量时才计算
                if v_tokens is not None and v_sol is not None and float(v_tokens) > 0 and sol_usd_price > 0:
                    # 计算代币美元价格: SOL价格 * SOL数量 / 代币数量
                    token_usd_price = sol_usd_price * float(v_sol) / float(v_tokens)
                    params[usd_price_param] = token_usd_price
                    updates.append(f"%({usd_price_param})s")
                    logger.debug(f"计算代币 {mint} 的美元价格: ${token_usd_price:.12f}")
                else:
                    updates.append("latest_usd_price")
                    
                case_statements[-1] = f"{case_statements[-1]} ({', '.join(updates)})"
            
            # 构建UPDATE语句中的CASE表达式
            mints_list = [f"%({param})s" for param in params.keys() if param.startswith("mint_")]
            
            update_query = f"""
            UPDATE token 
            SET 
                (v_tokens_in_bonding_curve, v_sol_in_bonding_curve, market_cap_sol, latest_usd_price) = 
                CASE 
                    {' '.join(case_statements)}
                    ELSE (v_tokens_in_bonding_curve, v_sol_in_bonding_curve, market_cap_sol, latest_usd_price)
                END
            WHERE mint IN ({', '.join(mints_list)})
            """
            
            cursor.execute(update_query, params)
            updated_count = cursor.rowcount
            
            if updated_count > 0:
                logger.info(f"已批量更新 {updated_count} 个代币的绑定曲线数据")
            else:
                logger.warning("没有代币的绑定曲线数据被更新")
                
        except Exception as e:
            logger.error(f"批量更新代币绑定曲线数据失败: {str(e)}", exc_info=True)
            logger.exception(e)
    
    def _update_token_bonding_curve_data(self, mint, v_tokens, v_sol, market_cap_sol):
        """
        更新token表中的绑定曲线数据
        
        参数:
            mint: 代币mint地址
            v_tokens: 绑定曲线中的代币数量
            v_sol: 绑定曲线中的SOL数量
            market_cap_sol: 市值(SOL)
        """
        if not mint or (v_tokens is None and v_sol is None and market_cap_sol is None):
            return False
            
        # 构建更新字段
        update_fields = []
        params = {'mint': mint}
        
        if v_tokens is not None:
            update_fields.append("v_tokens_in_bonding_curve = %(v_tokens)s")
            params['v_tokens'] = v_tokens
            
        if v_sol is not None:
            update_fields.append("v_sol_in_bonding_curve = %(v_sol)s")
            params['v_sol'] = v_sol
            
        if market_cap_sol is not None:
            update_fields.append("market_cap_sol = %(market_cap_sol)s")
            params['market_cap_sol'] = market_cap_sol
        
        # 计算美元价格 - 仅当同时有代币数量和SOL数量时才计算
        if v_tokens is not None and v_sol is not None and float(v_tokens) > 0:
            try:
                # 从SOL价格服务获取最新SOL价格
                from src.core.services.sol_price_service import sol_price_service
                sol_usd_price = sol_price_service.get_current_price()
                
                if sol_usd_price > 0:
                    # 计算代币美元价格: SOL价格 * SOL数量 / 代币数量
                    token_usd_price = sol_usd_price * float(v_sol) / float(v_tokens)
                    update_fields.append("latest_usd_price = %(usd_price)s")
                    params['usd_price'] = token_usd_price
                    logger.info(f"计算代币 {mint} 的美元价格: ${token_usd_price:.12f}")
            except Exception as e:
                logger.error(f"计算代币美元价格时出错: {str(e)}", exc_info=True)
            
        if not update_fields:
            return False
            
        # 构建更新语句
        query = f"""
        UPDATE token SET 
            {', '.join(update_fields)}
        WHERE mint = %(mint)s
        """
        
        cursor = self.execute(query, params)
        if cursor and cursor.rowcount > 0:
            logger.info(f"已更新代币 {mint} 的绑定曲线数据")
            return True
        else:
            logger.warning(f"更新代币 {mint} 的绑定曲线数据失败")
            return False
    
    def insert_many_trade_records(self, trades):
        """批量插入多个交易记录"""
        if not trades:
            return 0
        
        cursor = self.get_cursor()
        if cursor is None:
            return 0
        
        try:
            # 提取所有交易的signatures
            signatures = [trade.get('signature') for trade in trades if trade.get('signature')]
            
            if not signatures:
                return 0
                
            # 查询已存在的signatures
            placeholders = ', '.join(['%s'] * len(signatures))
            check_query = f"""
            SELECT signature FROM token_trade 
            WHERE signature IN ({placeholders})
            """
            cursor.execute(check_query, signatures)
            existing_signatures = set(row['signature'] for row in cursor.fetchall())
            
            # 过滤掉已存在的交易记录
            new_trades = [trade for trade in trades if trade.get('signature') not in existing_signatures]
            
            if not new_trades:
                logger.info(f"所有交易记录已存在，跳过插入")
                return 0
                
            logger.info(f"已过滤掉 {len(trades) - len(new_trades)} 条重复交易记录")
            
            query = """
            INSERT INTO token_trade (
                signature, mint, trader_public_key, tx_type, 
                token_amount, sol_amount, new_token_balance, bonding_curve_key,
                v_tokens_in_bonding_curve, v_sol_in_bonding_curve, market_cap_sol,
                pool
            ) VALUES %s
            """
            
            # 准备数据
            template = "(%(signature)s, %(mint)s, %(trader_public_key)s, %(tx_type)s, " \
                      "%(token_amount)s, %(sol_amount)s, %(new_token_balance)s, %(bonding_curve_key)s, " \
                      "%(v_tokens_in_bonding_curve)s, %(v_sol_in_bonding_curve)s, %(market_cap_sol)s, " \
                      "%(pool)s)"
            
            # 转换字段名
            normalized_trades = []
            for trade in new_trades:
                normalized_trade = {
                    'signature': trade.get('signature'),
                    'mint': trade.get('mint'),
                    'trader_public_key': trade.get('traderPublicKey'),
                    'tx_type': trade.get('txType'),
                    'token_amount': trade.get('tokenAmount'),
                    'sol_amount': trade.get('solAmount'),
                    # 处理可能缺失的字段，提供默认值或替代方案
                    'new_token_balance': trade.get('newTokenBalance') or trade.get('tokensInPool') or None,
                    'bonding_curve_key': trade.get('bondingCurveKey'),
                    'v_tokens_in_bonding_curve': trade.get('vTokensInBondingCurve') or trade.get('tokensInPool'),
                    'v_sol_in_bonding_curve': trade.get('vSolInBondingCurve') or trade.get('solInPool'),
                    'market_cap_sol': trade.get('marketCapSol'),
                    'pool': trade.get('pool')
                }
                normalized_trades.append(normalized_trade)
            
            result_count = 0
            if normalized_trades:
                # 执行批量插入
                execute_values(cursor, query, normalized_trades, template)
                result_count = cursor.rowcount
                
                # 对每个代币的最新交易更新token表中的绑定曲线数据
                self._update_tokens_from_trades(new_trades)
                
            return result_count
        except Exception as e:
            logger.error(f"批量插入交易记录失败: {str(e)}", exc_info=True)
            return 0
    
    def save_sol_price(self, price: float, timestamp: float = None) -> bool:
        """
        保存SOL价格记录到数据库
        
        参数:
            price: SOL的美元价格
            timestamp: 价格时间戳，如果为None则使用当前时间
            
        返回:
            是否保存成功
        """
        if timestamp is None:
            timestamp = time.time()
            
        # 转换时间戳为datetime对象
        dt = datetime.fromtimestamp(timestamp)
        
        query = """
        INSERT INTO sol_price (price, timestamp)
        VALUES (%s, %s)
        RETURNING id
        """
        
        cursor = self.execute(query, (price, dt))
        if cursor and cursor.rowcount > 0:
            result = cursor.fetchone()
            logger.info(f"SOL价格记录已保存，ID: {result['id']}, 价格: ${price:.2f}")
            return True
        
        logger.error(f"保存SOL价格记录失败")
        return False
    
    def get_latest_sol_price(self) -> Optional[Dict[str, Any]]:
        """
        获取最新的SOL价格记录
        
        返回:
            包含价格和时间戳的字典，如果没有记录则返回None
        """
        query = """
        SELECT price, timestamp
        FROM sol_price
        ORDER BY timestamp DESC
        LIMIT 1
        """
        
        cursor = self.execute(query)
        if cursor and cursor.rowcount > 0:
            result = cursor.fetchone()
            logger.debug(f"获取到最新SOL价格: ${float(result['price']):.2f} @ {result['timestamp']}")
            return result
        
        logger.warning("未找到SOL价格记录")
        return None
    
    def get_sol_price_history(self, start_time=None, end_time=None, limit=100) -> List[Dict[str, Any]]:
        """
        获取SOL价格历史记录
        
        参数:
            start_time: 开始时间，datetime对象或时间戳
            end_time: 结束时间，datetime对象或时间戳
            limit: 最大记录数
            
        返回:
            价格记录列表
        """
        conditions = []
        params = []
        
        if start_time:
            if isinstance(start_time, (int, float)):
                start_time = datetime.fromtimestamp(start_time)
            conditions.append("timestamp >= %s")
            params.append(start_time)
            
        if end_time:
            if isinstance(end_time, (int, float)):
                end_time = datetime.fromtimestamp(end_time)
            conditions.append("timestamp <= %s")
            params.append(end_time)
            
        where_clause = " AND ".join(conditions)
        if where_clause:
            where_clause = "WHERE " + where_clause
            
        query = f"""
        SELECT id, price, timestamp
        FROM sol_price
        {where_clause}
        ORDER BY timestamp DESC
        LIMIT {limit}
        """
        
        cursor = self.execute(query, params)
        if cursor:
            results = cursor.fetchall()
            logger.debug(f"获取到 {len(results)} 条SOL价格历史记录")
            return results
        
        logger.warning("查询SOL价格历史记录失败")
        return []
    
    def rollback(self):
        """回滚当前事务"""
        if hasattr(self.thread_local, 'conn') and self.thread_local.conn:
            try:
                self.thread_local.conn.rollback()
                logger.info("事务已回滚")
                return True
            except Exception as rollback_error:
                logger.error(f"回滚事务失败: {str(rollback_error)}", exc_info=True)
                return False
        return False

# 数据库单例
db = Database() 