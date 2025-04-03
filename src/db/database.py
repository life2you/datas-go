#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据库连接模块
处理与PostgreSQL数据库的连接和交互
"""

import logging
import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
from src.config.config import DB_CONFIG

logger = logging.getLogger(__name__)

class Database:
    """PostgreSQL数据库连接和操作类"""
    
    def __init__(self):
        """初始化数据库连接"""
        self.conn = None
        self.cursor = None
    
    def connect(self):
        """连接到PostgreSQL数据库"""
        try:
            if self.conn is None or self.conn.closed:
                self.conn = psycopg2.connect(
                    host=DB_CONFIG['host'],
                    port=DB_CONFIG['port'],
                    database=DB_CONFIG['database'],
                    user=DB_CONFIG['user'],
                    password=DB_CONFIG['password']
                )
                # 设置自动提交
                self.conn.autocommit = True
                logger.info(f"成功连接到数据库 {DB_CONFIG['database']} @ {DB_CONFIG['host']}:{DB_CONFIG['port']}")
            return True
        except Exception as e:
            logger.error(f"数据库连接失败: {str(e)}")
            return False
    
    def get_cursor(self):
        """获取数据库游标"""
        if not self.connect():
            return None
        
        if self.cursor is None or self.cursor.closed:
            self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        return self.cursor
    
    def close(self):
        """关闭数据库连接"""
        if self.cursor:
            self.cursor.close()
            self.cursor = None
        
        if self.conn:
            self.conn.close()
            self.conn = None
            logger.info("数据库连接已关闭")
    
    def execute(self, query, params=None):
        """执行SQL查询语句"""
        cursor = self.get_cursor()
        if cursor is None:
            logger.error("无法获取数据库游标")
            return None
        
        try:
            # 打印SQL语句和参数
            formatted_query = query
            if params:
                # 尝试格式化查询以便更好地查看实际执行的SQL
                try:
                    if isinstance(params, dict):
                        # 对于命名参数
                        for key, value in params.items():
                            placeholder = f"%({key})s"
                            # 转换值为适合SQL的格式
                            if isinstance(value, str):
                                sql_value = f"'{value}'"
                            elif value is None:
                                sql_value = "NULL"
                            else:
                                sql_value = str(value)
                            formatted_query = formatted_query.replace(placeholder, sql_value)
                    elif isinstance(params, (list, tuple)):
                        # 对于位置参数
                        for i, value in enumerate(params):
                            # 转换值为适合SQL的格式
                            if isinstance(value, str):
                                sql_value = f"'{value}'"
                            elif value is None:
                                sql_value = "NULL"
                            else:
                                sql_value = str(value)
                            formatted_query = formatted_query.replace("%s", sql_value, 1)
                except Exception as format_error:
                    logger.warning(f"无法格式化SQL查询: {str(format_error)}")
                    # 如果格式化失败，仍然打印原始查询和参数
                    formatted_query = f"SQL: {query}, 参数: {params}"
            
            logger.debug(f"执行SQL: {formatted_query}")
            
            cursor.execute(query, params or {})
            return cursor
        except Exception as e:
            logger.error(f"执行SQL失败: {str(e)}")
            logger.error(f"SQL: {query}")
            logger.error(f"参数: {params}")
            # 无需关闭连接，只需确保事务回滚
            if self.conn:
                try:
                    self.conn.rollback()
                    logger.info("事务已回滚")
                except Exception as rollback_error:
                    logger.error(f"回滚事务失败: {str(rollback_error)}")
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
            logger.error(f"批量插入代币数据失败: {str(e)}")
            return 0
    
    def insert_trade_record(self, trade_data):
        """插入交易记录到token_trade表"""
        # 先检查是否已存在相同signature的记录
        check_query = """
        SELECT id FROM token_trade WHERE signature = %(signature)s LIMIT 1
        """
        cursor = self.execute(check_query, {'signature': trade_data.get('signature')})
        if cursor and cursor.rowcount > 0:
            # 已存在相同signature的记录，返回其ID
            result = cursor.fetchone()
            logger.info(f"交易记录已存在，signature: {trade_data.get('signature')}")
            return result['id']
            
        # 不存在相同记录，执行插入
        query = """
        INSERT INTO token_trade (
            signature, mint, trader_public_key, tx_type, 
            token_amount, sol_amount, new_token_balance, bonding_curve_key,
            v_tokens_in_bonding_curve, v_sol_in_bonding_curve, market_cap_sol,
            pool
        ) VALUES (
            %(signature)s, %(mint)s, %(traderPublicKey)s, %(txType)s,
            %(tokenAmount)s, %(solAmount)s, %(newTokenBalance)s, %(bondingCurveKey)s,
            %(vTokensInBondingCurve)s, %(vSolInBondingCurve)s, %(marketCapSol)s,
            %(pool)s
        ) RETURNING id;
        """
        cursor = self.execute(query, trade_data)
        if cursor:
            result = cursor.fetchone()
            trade_id = result['id'] if result else None
            
            # 成功插入交易记录后，更新token表中的绑定曲线数据
            if trade_id and trade_data.get('mint'):
                self._update_token_bonding_curve_data(
                    trade_data.get('mint'),
                    trade_data.get('vTokensInBondingCurve'),
                    trade_data.get('vSolInBondingCurve'),
                    trade_data.get('marketCapSol')
                )
                
            return trade_id
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
            # 构建批量更新语句
            case_statements = []
            params = {}
            
            for i, (mint, trade) in enumerate(trades_by_mint.items()):
                mint_param = f"mint_{i}"
                v_tokens_param = f"v_tokens_{i}"
                v_sol_param = f"v_sol_{i}"
                market_cap_param = f"market_cap_{i}"
                
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
                    
                case_statements[-1] = f"{case_statements[-1]} ({', '.join(updates)})"
            
            # 构建UPDATE语句中的CASE表达式
            mints_list = [f"%({param})s" for param in params.keys() if param.startswith("mint_")]
            
            update_query = f"""
            UPDATE token 
            SET 
                (v_tokens_in_bonding_curve, v_sol_in_bonding_curve, market_cap_sol) = 
                CASE 
                    {' '.join(case_statements)}
                    ELSE (v_tokens_in_bonding_curve, v_sol_in_bonding_curve, market_cap_sol)
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
            logger.error(f"批量更新代币绑定曲线数据失败: {str(e)}")
    
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
                    'new_token_balance': trade.get('newTokenBalance'),
                    'bonding_curve_key': trade.get('bondingCurveKey'),
                    'v_tokens_in_bonding_curve': trade.get('vTokensInBondingCurve'),
                    'v_sol_in_bonding_curve': trade.get('vSolInBondingCurve'),
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
            logger.error(f"批量插入交易记录失败: {str(e)}")
            return 0

# 数据库单例
db = Database() 