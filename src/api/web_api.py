#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Web API模块
为前端提供代币数据访问接口
"""

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any, Generic, TypeVar
from pydantic import BaseModel, Field, ConfigDict
import logging
import uvicorn
import os
from datetime import datetime

from src.db.database import db
from src.utils.logger import get_logger, setup_logging
from src.utils.error_handler import error_handler
from src.config.config import API_CONFIG

# 设置日志
setup_logging()
logger = get_logger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title=API_CONFIG["title"],
    description=API_CONFIG["description"],
    version=API_CONFIG["version"],
    docs_url=API_CONFIG["docs_url"],
    redoc_url=API_CONFIG["redoc_url"]
)

# 配置CORS
if API_CONFIG["enable_cors"]:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=API_CONFIG["cors_origins"],
        allow_credentials=API_CONFIG["allow_credentials"],
        allow_methods=API_CONFIG["allowed_methods"],
        allow_headers=API_CONFIG["allowed_headers"],
    )

# 数据模型
class TokenBase(BaseModel):
    """代币基本信息模型"""
    mint: str
    name: str
    symbol: str
    uri: Optional[str] = None
    initial_buy: Optional[float] = None
    v_tokens_in_bonding_curve: Optional[float] = None
    v_sol_in_bonding_curve: Optional[float] = None
    created_at: datetime
    buy_count: int = 0
    sell_count: int = 0
    reply_count: int = 0
    
    model_config = {
        "json_schema_extra": {
            "properties": {
                "mint": {"description": "代币地址"},
                "name": {"description": "代币名称"},
                "symbol": {"description": "代币符号"},
                "uri": {"description": "代币头像URI"},
                "initial_buy": {"description": "初始购买代币数量"},
                "v_tokens_in_bonding_curve": {"description": "当前池子代币数量"},
                "v_sol_in_bonding_curve": {"description": "当前池子SOL数量"},
                "created_at": {"description": "记录创建时间"},
                "buy_count": {"description": "买入交易数量"},
                "sell_count": {"description": "卖出交易数量"},
                "reply_count": {"description": "回复总数"}
            }
        }
    }

class TokenDetail(TokenBase):
    """代币详细信息模型"""
    description: Optional[str] = None
    creator: Optional[str] = None
    creator_name: Optional[str] = None
    max_supply: Optional[int] = None
    
    model_config = {
        "json_schema_extra": {
            "properties": {
                "description": {"description": "代币描述"},
                "creator": {"description": "创建者地址"},
                "creator_name": {"description": "创建者名称"},
                "max_supply": {"description": "最大供应量"}
            }
        }
    }

class TokenReply(BaseModel):
    """代币回复模型"""
    id: int
    mint: str
    is_buy: Optional[bool] = None
    sol_amount: Optional[float] = None
    user_address: str
    username: Optional[str] = None
    timestamp: int
    datetime: datetime
    text: Optional[str] = None
    total_likes: int = 0
    
    model_config = {
        "json_schema_extra": {
            "properties": {
                "id": {"description": "回复ID"},
                "mint": {"description": "代币地址"},
                "is_buy": {"description": "是否买入"},
                "sol_amount": {"description": "SOL金额"},
                "user_address": {"description": "用户地址"},
                "username": {"description": "用户名"},
                "timestamp": {"description": "时间戳"},
                "datetime": {"description": "时间"},
                "text": {"description": "回复内容"},
                "total_likes": {"description": "点赞数"}
            }
        }
    }

class TokenTrade(BaseModel):
    """代币交易模型"""
    id: int
    mint: str
    tx_type: str
    user_address: str
    username: Optional[str] = None
    timestamp: int
    datetime: datetime
    sol_amount: float
    token_amount: float
    tx_signature: Optional[str] = None
    
    model_config = {
        "json_schema_extra": {
            "properties": {
                "id": {"description": "交易ID"},
                "mint": {"description": "代币地址"},
                "tx_type": {"description": "交易类型(buy/sell)"},
                "user_address": {"description": "用户地址"},
                "username": {"description": "用户名"},
                "timestamp": {"description": "时间戳"},
                "datetime": {"description": "时间"},
                "sol_amount": {"description": "SOL金额"},
                "token_amount": {"description": "代币数量"},
                "tx_signature": {"description": "交易签名"}
            }
        }
    }

class PaginatedTokens(BaseModel):
    """代币分页响应模型"""
    items: List[TokenBase]
    total: int
    page: int
    limit: int
    pages: int
    
    model_config = {
        "json_schema_extra": {
            "properties": {
                "items": {"description": "数据项列表"},
                "total": {"description": "总数据量"},
                "page": {"description": "当前页码"},
                "limit": {"description": "每页数量"},
                "pages": {"description": "总页数"}
            }
        }
    }

class PaginatedReplies(BaseModel):
    """回复分页响应模型"""
    items: List[TokenReply]
    total: int
    page: int
    limit: int
    pages: int
    
    model_config = {
        "json_schema_extra": {
            "properties": {
                "items": {"description": "数据项列表"},
                "total": {"description": "总数据量"},
                "page": {"description": "当前页码"},
                "limit": {"description": "每页数量"},
                "pages": {"description": "总页数"}
            }
        }
    }

class PaginatedTrades(BaseModel):
    """交易分页响应模型"""
    items: List[TokenTrade]
    total: int
    page: int
    limit: int
    pages: int
    
    model_config = {
        "json_schema_extra": {
            "properties": {
                "items": {"description": "数据项列表"},
                "total": {"description": "总数据量"},
                "page": {"description": "当前页码"},
                "limit": {"description": "每页数量"},
                "pages": {"description": "总页数"}
            }
        }
    }

# API路由
@app.get("/api/tokens", response_model=PaginatedTokens, tags=["代币"])
@error_handler
def get_tokens(
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    sort: str = Query("v_sol_in_bonding_curve", description="排序字段"),
    order: str = Query("desc", description="排序方向(asc/desc)"),
    search: str = Query(None, description="搜索关键词，可搜索名称或符号")
):
    """
    获取代币列表，支持分页、排序和搜索
    如果查询失败，将记录日志并返回适当的HTTP异常
    如果没有符合条件的代币，将返回空列表而不是错误
    """
    # 验证并设置默认值
    valid_sort_fields = ["created_at", "v_sol_in_bonding_curve", "v_tokens_in_bonding_curve"]
    if sort not in valid_sort_fields:
        logger.warning(f"无效的排序字段: {sort}，使用默认排序字段: v_sol_in_bonding_curve")
        sort = "v_sol_in_bonding_curve"
    
    if order.lower() not in ["asc", "desc"]:
        logger.warning(f"无效的排序方向: {order}，使用默认排序方向: desc")
        order = "desc"
    
    # 构建查询条件
    where_clauses = []
    params = []
    
    # 添加搜索条件
    if search:
        search_pattern = f"%{search}%"
        where_clauses.append("(name ILIKE %s OR symbol ILIKE %s)")
        params.extend([search_pattern, search_pattern])
    
    # 构建WHERE子句
    where_clause = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
    
    # 获取总数
    count_query = f"""
    SELECT COUNT(*) as count FROM token {where_clause}
    """
    try:
        cursor = db.execute(count_query, params)
        if not cursor:
            logger.error(f"执行代币计数查询失败: {count_query}, 搜索条件: {search}")
            raise HTTPException(status_code=500, detail="数据库查询失败")
            
        result = cursor.fetchone()
        total = 0 if result is None else result.get("count", 0)
    except Exception as e:
        logger.error(f"获取代币总数失败: {str(e)}, 搜索条件: {search}")
        raise HTTPException(status_code=500, detail="数据库查询失败")
    
    # 计算分页信息
    offset = (page - 1) * limit
    pages = (total + limit - 1) // limit if total > 0 else 1
    
    # 如果没有记录，直接返回空列表
    if total == 0:
        logger.info(f"没有找到符合条件的代币, 搜索条件: {search}")
        return {
            "items": [],
            "total": 0,
            "page": page,
            "limit": limit,
            "pages": 1
        }
    
    # 获取代币列表
    tokens_query = f"""
    SELECT 
        t.mint, t.name, t.symbol, t.uri, t.initial_buy,
        t.v_tokens_in_bonding_curve, t.v_sol_in_bonding_curve,
        t.created_at,
        (SELECT COUNT(*) FROM token_trade WHERE mint = t.mint AND tx_type = 'buy') as buy_count,
        (SELECT COUNT(*) FROM token_trade WHERE mint = t.mint AND tx_type = 'sell') as sell_count,
        (SELECT COUNT(*) FROM token_replies WHERE mint = t.mint) as reply_count
    FROM token t
    {where_clause}
    ORDER BY {sort} {order}
    LIMIT %s OFFSET %s
    """
    
    try:
        params.extend([limit, offset])
        cursor = db.execute(tokens_query, params)
        if not cursor:
            logger.error(f"执行代币列表查询失败: {tokens_query}, 搜索条件: {search}")
            raise HTTPException(status_code=500, detail="数据库查询失败")
            
        tokens = cursor.fetchall() or []
    except Exception as e:
        logger.error(f"获取代币列表失败: {str(e)}, 搜索条件: {search}")
        raise HTTPException(status_code=500, detail="数据库查询失败")
    
    # 构建响应
    return {
        "items": tokens,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": pages
    }


@app.get("/api/tokens/{mint}", response_model=TokenDetail, tags=["代币"])
@error_handler
def get_token_detail(mint: str):
    """
    获取代币详情，包括名称、符号、创建者等基本信息
    如果查询失败，将记录日志并返回适当的HTTP异常
    如果代币不存在，将返回404错误
    """
    # 获取代币基本信息
    token_query = """
    SELECT 
        t.mint, t.name, t.symbol, t.uri, t.initial_buy,
        t.v_tokens_in_bonding_curve, t.v_sol_in_bonding_curve,
        t.created_at, t.trader_public_key as creator,
        '' as creator_name,
        (SELECT COUNT(*) FROM token_trade WHERE mint = t.mint AND tx_type = 'buy') as buy_count,
        (SELECT COUNT(*) FROM token_trade WHERE mint = t.mint AND tx_type = 'sell') as sell_count,
        (SELECT COUNT(*) FROM token_replies WHERE mint = t.mint) as reply_count
    FROM token t
    WHERE t.mint = %s
    """
    
    try:
        cursor = db.execute(token_query, [mint])
        if not cursor:
            logger.error(f"执行查询失败: {token_query}, 参数: {mint}")
            raise HTTPException(status_code=500, detail="数据库查询失败")
            
        token = cursor.fetchone()
        if token is None:
            logger.warning(f"请求的代币不存在: {mint}")
            raise HTTPException(status_code=404, detail="代币不存在")
        
        return token
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        logger.error(f"获取代币详情失败: {str(e)}, 代币: {mint}")
        raise HTTPException(status_code=500, detail="数据库查询失败")


@app.get("/api/tokens/{mint}/replies", response_model=PaginatedReplies, tags=["代币回复"])
@error_handler
def get_token_replies(
    mint: str,
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(20, ge=1, le=100, description="每页数量")
):
    """
    获取代币回复列表，支持分页
    如果查询失败，将记录日志并返回适当的HTTP异常
    如果没有回复，将返回空列表而不是错误
    """
    # 获取总数
    count_query = """
    SELECT COUNT(*) as count FROM token_replies
    WHERE mint = %s
    """
    try:
        cursor = db.execute(count_query, [mint])
        if not cursor:
            logger.error(f"执行回复计数查询失败: {count_query}, 代币: {mint}")
            raise HTTPException(status_code=500, detail="数据库查询失败")
            
        result = cursor.fetchone()
        total = 0 if result is None else result.get("count", 0)
    except Exception as e:
        logger.error(f"获取代币回复总数失败: {str(e)}, 代币: {mint}")
        raise HTTPException(status_code=500, detail="数据库查询失败")
    
    # 计算分页信息
    offset = (page - 1) * limit
    pages = (total + limit - 1) // limit if total > 0 else 1
    
    # 如果没有记录，直接返回空列表
    if total == 0:
        logger.info(f"代币 {mint} 没有回复记录")
        return {
            "items": [],
            "total": 0,
            "page": page,
            "limit": limit,
            "pages": 1
        }
    
    # 获取回复列表
    replies_query = """
    SELECT 
        id, mint, is_buy, sol_amount, user_address,
        username, timestamp, datetime, text, total_likes
    FROM token_replies
    WHERE mint = %s
    ORDER BY timestamp DESC
    LIMIT %s OFFSET %s
    """
    
    try:
        cursor = db.execute(replies_query, [mint, limit, offset])
        if not cursor:
            logger.error(f"执行回复列表查询失败: {replies_query}, 代币: {mint}")
            raise HTTPException(status_code=500, detail="数据库查询失败")
            
        replies = cursor.fetchall() or []
    except Exception as e:
        logger.error(f"获取代币回复列表失败: {str(e)}, 代币: {mint}")
        raise HTTPException(status_code=500, detail="数据库查询失败")
    
    # 构建响应
    return {
        "items": replies,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": pages
    }


@app.get("/api/tokens/{mint}/trades", response_model=PaginatedTrades, tags=["代币交易"])
@error_handler
def get_token_trades(
    mint: str,
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    type: str = Query("all", description="交易类型(buy/sell/all)")
):
    """
    获取代币交易列表，支持分页和交易类型筛选
    如果查询失败，将记录日志并返回适当的HTTP异常
    如果没有交易记录，将返回空列表而不是错误
    """
    # 构建查询条件
    where_clauses = ["mint = %s"]
    params = [mint]
    
    if type.lower() == "buy":
        where_clauses.append("tx_type = 'buy'")
    elif type.lower() == "sell":
        where_clauses.append("tx_type = 'sell'")
    
    # 构建WHERE子句
    where_clause = "WHERE " + " AND ".join(where_clauses)
    
    # 获取总数
    count_query = f"""
    SELECT COUNT(*) as count FROM token_trade
    {where_clause}
    """
    try:
        cursor = db.execute(count_query, params)
        if not cursor:
            logger.error(f"执行交易计数查询失败: {count_query}, 代币: {mint}, 类型: {type}")
            raise HTTPException(status_code=500, detail="数据库查询失败")
            
        result = cursor.fetchone()
        total = 0 if result is None else result.get("count", 0)
    except Exception as e:
        logger.error(f"获取代币交易总数失败: {str(e)}, 代币: {mint}, 类型: {type}")
        raise HTTPException(status_code=500, detail="数据库查询失败")
    
    # 计算分页信息
    offset = (page - 1) * limit
    pages = (total + limit - 1) // limit if total > 0 else 1
    
    # 如果没有记录，直接返回空列表
    if total == 0:
        logger.info(f"代币 {mint} 没有交易记录（类型: {type}）")
        return {
            "items": [],
            "total": 0,
            "page": page,
            "limit": limit,
            "pages": 1
        }
    
    # 获取交易列表
    trades_query = f"""
    SELECT 
        id, mint, tx_type, trader_public_key as user_address, 
        '' as username, -- 临时添加空用户名
        EXTRACT(EPOCH FROM trade_time)::bigint * 1000 as timestamp, 
        trade_time as datetime, 
        sol_amount, token_amount, signature as tx_signature
    FROM token_trade
    {where_clause}
    ORDER BY trade_time DESC
    LIMIT %s OFFSET %s
    """
    
    try:
        params.extend([limit, offset])
        cursor = db.execute(trades_query, params)
        if not cursor:
            logger.error(f"执行交易列表查询失败: {trades_query}, 代币: {mint}, 类型: {type}")
            raise HTTPException(status_code=500, detail="数据库查询失败")
            
        trades = cursor.fetchall() or []
    except Exception as e:
        logger.error(f"获取代币交易列表失败: {str(e)}, 代币: {mint}, 类型: {type}")
        raise HTTPException(status_code=500, detail="数据库查询失败")
    
    # 构建响应
    return {
        "items": trades,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": pages
    }


# API服务运行配置
def start_api_server(host=None, port=None):
    """启动API服务器"""
    # 使用传入的参数或配置文件中的设置
    host = host or API_CONFIG["host"]
    port = port or API_CONFIG["port"]
    
    logger.info(f"启动API服务器，监听 {host}:{port}")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    # 直接运行此模块时启动API服务器
    start_api_server() 