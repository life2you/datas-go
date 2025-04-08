#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Web API模块
为前端提供代币数据访问接口
"""

from fastapi import FastAPI, HTTPException, Query, Depends, Path
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any, Generic, TypeVar
from pydantic import BaseModel, Field, ConfigDict
import logging
import uvicorn
import os
from datetime import datetime

from src.db.database import db
from src.core.logger import get_logger, setup_logging
from src.core.error_handler import error_handler
from src.core.config import API_CONFIG, ROOT_DIR
from src.core.services.sol_price_service import sol_price_service

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
    image: Optional[str] = None
    twitter: Optional[str] = None
    website: Optional[str] = None
    has_metadata: Optional[bool] = None
    
    model_config = {
        "json_schema_extra": {
            "properties": {
                "description": {"description": "代币描述"},
                "creator": {"description": "创建者地址"},
                "creator_name": {"description": "创建者名称"},
                "max_supply": {"description": "最大供应量"},
                "image": {"description": "代币图片链接"},
                "twitter": {"description": "代币Twitter链接"},
                "website": {"description": "代币官网链接"},
                "has_metadata": {"description": "是否有元数据"}
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

class TokenMetadata(BaseModel):
    """代币元数据模型"""
    mint: str
    description: Optional[str] = None
    image: Optional[str] = None
    twitter: Optional[str] = None
    website: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = {
        "json_schema_extra": {
            "properties": {
                "mint": {"description": "代币地址"},
                "description": {"description": "代币描述"},
                "image": {"description": "代币图片链接"},
                "twitter": {"description": "代币Twitter链接"},
                "website": {"description": "代币官网链接"},
                "created_at": {"description": "元数据创建时间"},
                "updated_at": {"description": "元数据更新时间"}
            }
        }
    }

# API路由
@app.get("/api/tokens", tags=["代币"])
async def get_tokens(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页记录数"),
    order_by: str = Query("created_at", description="排序字段"),
    order_dir: str = Query("desc", description="排序方向 (asc/desc)"),
    name: Optional[str] = Query(None, description="按名称过滤"),
    symbol: Optional[str] = Query(None, description="按符号过滤"),
    min_market_cap: Optional[float] = Query(None, ge=0, description="最小市值(SOL)"),
    min_usd_price: Optional[float] = Query(None, ge=0, description="最小美元价格")
):
    """
    获取代币列表
    
    参数：
        - page: 页码
        - page_size: 每页记录数
        - order_by: 排序字段
        - order_dir: 排序方向
        - name: 按名称过滤
        - symbol: 按符号过滤
        - min_market_cap: 最小市值(SOL)
        - min_usd_price: 最小美元价格
    
    返回：
        代币列表
    """
    try:
        # 构建查询
        conditions = []
        params = []
        
        # 添加过滤条件
        if name:
            conditions.append("LOWER(t.name) LIKE LOWER(%s)")
            params.append(f"%{name}%")
            
        if symbol:
            conditions.append("LOWER(t.symbol) LIKE LOWER(%s)")
            params.append(f"%{symbol}%")
            
        if min_market_cap is not None:
            conditions.append("t.market_cap_sol >= %s")
            params.append(min_market_cap)
            
        if min_usd_price is not None:
            conditions.append("t.latest_usd_price >= %s")
            params.append(min_usd_price)
            
        # 构建WHERE子句
        where_clause = " AND ".join(conditions)
        if where_clause:
            where_clause = "WHERE " + where_clause
        
        # 验证排序字段，防止SQL注入
        valid_order_fields = ["created_at", "market_cap_sol", "name", "symbol", "latest_usd_price"]
        if order_by not in valid_order_fields:
            order_by = "created_at"
            
        # 验证排序方向
        order_dir = order_dir.lower()
        if order_dir not in ["asc", "desc"]:
            order_dir = "desc"
            
        # 计算分页
        offset = (page - 1) * page_size
        
        # 获取总记录数
        count_query = f"""
        SELECT COUNT(*) as total FROM token t {where_clause}
        """
        count_cursor = db.execute(count_query, params)
        
        if not count_cursor:
            logger.error("执行计数查询失败")
            raise HTTPException(status_code=500, detail="查询代币列表失败")
            
        total = count_cursor.fetchone()["total"]
        
        # 获取数据
        query = f"""
        SELECT 
            t.id, 
            t.signature, 
            t.mint, 
            t.trader_public_key, 
            t.name, 
            t.symbol, 
            t.uri, 
            t.v_tokens_in_bonding_curve,
            t.v_sol_in_bonding_curve,
            t.market_cap_sol,
            t.latest_usd_price,
            t.created_at
        FROM token t
        {where_clause}
        ORDER BY t.{order_by} {order_dir}
        LIMIT %s OFFSET %s
        """
        
        # 添加分页参数
        params.append(page_size)
        params.append(offset)
        
        cursor = db.execute(query, params)
        
        if not cursor:
            logger.error("执行查询失败")
            raise HTTPException(status_code=500, detail="查询代币列表失败")
            
        tokens = cursor.fetchall()
        
        # 获取SOL/USD价格用于计算美元市值
        from src.core.services.sol_price_service import sol_price_service
        sol_price = sol_price_service.get_current_price()
        
        # 转换数据
        results = []
        for token in tokens:
            # 计算美元市值
            market_cap_usd = None
            if token["market_cap_sol"] and sol_price:
                market_cap_usd = float(token["market_cap_sol"]) * sol_price
            
            results.append({
                "id": token["id"],
                "mint": token["mint"],
                "trader_public_key": token["trader_public_key"],
                "name": token["name"],
                "symbol": token["symbol"],
                "uri": token["uri"],
                "token_supply": float(token["v_tokens_in_bonding_curve"]) if token["v_tokens_in_bonding_curve"] else None,
                "sol_in_pool": float(token["v_sol_in_bonding_curve"]) if token["v_sol_in_bonding_curve"] else None,
                "market_cap_sol": float(token["market_cap_sol"]) if token["market_cap_sol"] else None,
                "market_cap_usd": market_cap_usd,
                "usd_price": float(token["latest_usd_price"]) if token["latest_usd_price"] else None,
                "created_at": token["created_at"].strftime("%Y-%m-%d %H:%M:%S") if token["created_at"] else None
            })
        
        # 返回结果
        return {
            "success": True,
            "data": results,
            "pagination": {
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size
            }
        }
    except Exception as e:
        logger.error(f"获取代币列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取代币列表失败: {str(e)}")


@app.get("/api/tokens/{mint}", response_model=TokenDetail, tags=["代币"])
@error_handler
def get_token_detail(mint: str):
    """
    获取代币详细信息
    
    参数:
    - mint: 代币地址
    
    返回:
    - TokenDetail: 代币详细信息
    """
    try:
        # 查询代币基本信息
        query = """
        SELECT 
            t.mint, t.name, t.symbol, t.uri, t.initial_buy, 
            t.v_tokens_in_bonding_curve, t.v_sol_in_bonding_curve, 
            t.created_at, t.has_meta_data
        FROM token t
        WHERE t.mint = %s
        LIMIT 1
        """
        cursor = db.execute(query, (mint,))
        if not cursor or cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail=f"找不到代币: {mint}")
        
        token = cursor.fetchone()
        
        # 查询买入交易数量
        buy_query = """
        SELECT COUNT(*) as buy_count 
        FROM token_trade 
        WHERE mint = %s AND tx_type = 'buy'
        """
        cursor = db.execute(buy_query, (mint,))
        buy_count = 0
        if cursor and cursor.rowcount > 0:
            buy_count = cursor.fetchone()['buy_count']
        
        # 查询卖出交易数量
        sell_query = """
        SELECT COUNT(*) as sell_count 
        FROM token_trade 
        WHERE mint = %s AND tx_type = 'sell'
        """
        cursor = db.execute(sell_query, (mint,))
        sell_count = 0
        if cursor and cursor.rowcount > 0:
            sell_count = cursor.fetchone()['sell_count']
        
        # 查询回复数量
        reply_query = """
        SELECT COUNT(*) as reply_count 
        FROM token_reply 
        WHERE mint = %s
        """
        cursor = db.execute(reply_query, (mint,))
        reply_count = 0
        if cursor and cursor.rowcount > 0:
            reply_count = cursor.fetchone()['reply_count']
        
        # 补充计数信息
        token['buy_count'] = buy_count
        token['sell_count'] = sell_count
        token['reply_count'] = reply_count
        
        # 查询元数据信息
        if token['has_meta_data'] == 1:
            metadata_query = """
            SELECT description, image, twitter, website
            FROM token_metadata
            WHERE mint = %s
            LIMIT 1
            """
            cursor = db.execute(metadata_query, (mint,))
            if cursor and cursor.rowcount > 0:
                metadata = cursor.fetchone()
                token['description'] = metadata['description']
                token['image'] = metadata['image']
                token['twitter'] = metadata['twitter']
                token['website'] = metadata['website']
                token['has_metadata'] = True
            else:
                token['has_metadata'] = False
        else:
            token['has_metadata'] = False
        
        return token
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取代币详情失败: {str(e)}")
        logger.exception(e)
        raise HTTPException(status_code=500, detail="服务器内部错误")


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


@app.get("/api/sol/price", tags=["SOL价格"])
async def get_sol_price():
    """
    获取当前SOL价格
    
    返回：
        当前SOL价格和更新时间
    """
    try:
        price_data = sol_price_service.get_price_with_timestamp()
        
        if price_data['price'] == 0:
            # 如果缓存中没有价格数据，尝试从服务中获取一次
            price = sol_price_service.api.get_sol_usd_price()
            if price:
                sol_price_service._update_sol_price()
                price_data = sol_price_service.get_price_with_timestamp()
        
        return {
            "success": True,
            "data": {
                "price": price_data['price'],
                "timestamp": price_data['timestamp'],
                "formatted_time": price_data['formatted_time']
            }
        }
    except Exception as e:
        logger.error(f"获取SOL价格失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取SOL价格失败: {str(e)}")

@app.get("/api/sol/price/history", tags=["SOL价格"])
async def get_sol_price_history(days: int = Query(1, ge=1, le=30, description="获取最近几天的数据"),
                              limit: int = Query(100, ge=1, le=1000, description="返回的记录数量")):
    """
    获取SOL价格历史记录
    
    参数：
        - days: 获取最近几天的数据
        - limit: 返回的最大记录数
    
    返回：
        SOL价格历史记录列表
    """
    try:
        history = sol_price_service.get_price_history(days, limit)
        
        # 格式化输出
        formatted_history = []
        for record in history:
            formatted_history.append({
                "id": record['id'],
                "price": float(record['price']),
                "timestamp": record['timestamp'].timestamp(),
                "formatted_time": record['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
            })
            
        return {
            "success": True,
            "data": formatted_history,
            "count": len(formatted_history)
        }
    except Exception as e:
        logger.error(f"获取SOL价格历史记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取SOL价格历史记录失败: {str(e)}")

@app.get("/api/tokens/{mint}/price", tags=["代币"])
async def get_token_price(mint: str = Path(..., description="代币地址")):
    """
    获取代币的美元价格
    
    参数：
        - mint: 代币mint地址
    
    返回：
        代币的美元价格信息
    """
    try:
        query = """
        SELECT 
            t.latest_usd_price, 
            t.v_tokens_in_bonding_curve as token_supply,
            t.v_sol_in_bonding_curve as sol_in_pool,
            t.market_cap_sol,
            t.name,
            t.symbol
        FROM 
            token t
        WHERE 
            t.mint = %s
        """
        
        cursor = db.execute(query, (mint,))
        if not cursor or cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail=f"代币 {mint} 不存在")
            
        token = cursor.fetchone()
        
        # 获取SOL/USD价格
        from src.core.services.sol_price_service import sol_price_service
        sol_price = sol_price_service.get_current_price()
        
        # 准备返回数据
        price_data = {
            "token_address": mint,
            "name": token["name"],
            "symbol": token["symbol"],
            "usd_price": float(token["latest_usd_price"]) if token["latest_usd_price"] else None,
            "sol_in_pool": float(token["sol_in_pool"]) if token["sol_in_pool"] else None,
            "token_supply": float(token["token_supply"]) if token["token_supply"] else None,
            "market_cap_sol": float(token["market_cap_sol"]) if token["market_cap_sol"] else None,
            "market_cap_usd": float(token["market_cap_sol"] * sol_price) if token["market_cap_sol"] and sol_price else None,
            "sol_price": sol_price,
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return {
            "success": True,
            "data": price_data
        }
    except Exception as e:
        logger.error(f"获取代币价格失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取代币价格失败: {str(e)}")

@app.get("/api/tokens/{mint}/metadata", response_model=TokenMetadata, tags=["代币元数据"])
@error_handler
def get_token_metadata(mint: str = Path(..., description="代币地址")):
    """
    获取指定代币的元数据
    
    参数:
    - mint: 代币地址
    
    返回:
    - TokenMetadata: 代币元数据
    """
    try:
        # 检查代币是否存在
        check_query = """
        SELECT id FROM token WHERE mint = %s LIMIT 1
        """
        cursor = db.execute(check_query, (mint,))
        if not cursor or cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail=f"找不到代币: {mint}")
        
        # 查询代币元数据
        query = """
        SELECT mint, description, image, twitter, website, created_at, updated_at
        FROM token_metadata
        WHERE mint = %s
        LIMIT 1
        """
        cursor = db.execute(query, (mint,))
        if not cursor or cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail=f"找不到代币元数据: {mint}")
        
        metadata = cursor.fetchone()
        return metadata
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取代币元数据失败: {str(e)}")
        logger.exception(e)
        raise HTTPException(status_code=500, detail="服务器内部错误")

@app.get("/api/metadata/stats", tags=["代币元数据"])
@error_handler
def get_metadata_stats():
    """
    获取元数据统计信息
    
    返回:
    - 元数据统计信息，包括总数、已处理数、未处理数等
    """
    try:
        # 查询元数据统计信息
        query = """
        SELECT 
            COUNT(*) as total_tokens,
            SUM(CASE WHEN has_meta_data = 1 THEN 1 ELSE 0 END) as processed,
            SUM(CASE WHEN has_meta_data = 0 THEN 1 ELSE 0 END) as pending,
            SUM(CASE WHEN has_meta_data < 0 THEN 1 ELSE 0 END) as failed
        FROM token
        """
        cursor = db.execute(query)
        if not cursor:
            raise HTTPException(status_code=500, detail="查询元数据统计信息失败")
        
        stats = cursor.fetchone()
        
        # 查询元数据表统计信息
        query = """
        SELECT COUNT(*) as metadata_count
        FROM token_metadata
        """
        cursor = db.execute(query)
        metadata_count = 0
        if cursor:
            result = cursor.fetchone()
            metadata_count = result['metadata_count'] if result else 0
        
        return {
            "total_tokens": stats['total_tokens'],
            "processed_tokens": stats['processed'],
            "pending_tokens": stats['pending'],
            "failed_tokens": stats['failed'],
            "metadata_count": metadata_count,
            "scan_time": datetime.now()
        }
    except Exception as e:
        logger.error(f"获取元数据统计信息失败: {str(e)}")
        logger.exception(e)
        raise HTTPException(status_code=500, detail="服务器内部错误")

# API服务运行配置
def start_api_server(host: str = None, port: int = None):
    """启动API服务器"""
    if host is None:
        host = API_CONFIG['host']
    if port is None:
        port = API_CONFIG['port']
    
    logger.info(f"启动API服务器 @ {host}:{port}")
    return app


if __name__ == "__main__":
    # 直接运行此模块时启动API服务器
    start_api_server() 