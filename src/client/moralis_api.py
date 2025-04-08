#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Moralis API客户端
用于查询Solana代币价格和其他区块链数据
"""

import logging
import requests
import json
import os
import time
from typing import Optional, Dict, Any, Tuple
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class MoralisAPI:
    """
    Moralis API客户端类
    用于与Moralis区块链API交互，查询代币价格等信息
    """
    
    BASE_URL = "https://solana-gateway.moralis.io"
    
    # 价格缓存，格式为 (价格, 时间戳)
    _sol_price_cache: Tuple[float, float] = (0.0, 0.0)
    
    def __init__(self, api_key: str):
        """
        初始化Moralis API客户端
        
        参数:
            api_key: Moralis API密钥
        """
        self.api_key = api_key
        self.headers = {
            "accept": "application/json",
            "X-API-Key": api_key
        }
        logger.info("Moralis API客户端已初始化")
    
    def get_token_price(self, token_address: str, network: str = "mainnet") -> Optional[Dict[str, Any]]:
        """
        获取指定代币的价格信息
        
        参数:
            token_address: 代币合约地址
            network: 网络名称，默认为mainnet
            
        返回:
            代币价格信息的字典，如果失败则返回None
        """
        url = f"{self.BASE_URL}/token/{network}/{token_address}/price"
        
        try:
            logger.debug(f"正在请求代币价格: {token_address}")
            response = requests.get(url, headers=self.headers)
            
            # 检查响应状态
            if response.status_code == 200:
                data = response.json()
                logger.info(f"成功获取代币价格: {token_address}")
                return data
            else:
                logger.error(f"获取代币价格失败，状态码: {response.status_code}")
                logger.error(f"响应内容: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"请求代币价格时发生错误: {str(e)}")
            return None
    
    def get_sol_usd_price(self) -> Optional[float]:
        """
        获取SOL代币的美元价格
        
        返回:
            SOL的美元价格，如果失败则返回None
        """
        # SOL代币的地址是一个众所周知的常量
        sol_address = "So11111111111111111111111111111111111111112"
        
        result = self.get_token_price(sol_address)
        if result and 'usdPrice' in result:
            price = float(result['usdPrice'])
            logger.info(f"当前SOL价格: ${price:.2f}")
            return price
        
        logger.warning("无法获取SOL价格")
        return None
    
    @classmethod
    def get_cached_sol_price(cls) -> Tuple[float, float]:
        """
        获取缓存的SOL价格和时间戳
        
        返回:
            (价格, 时间戳)的元组
        """
        return cls._sol_price_cache
    
    @classmethod
    def update_sol_price_cache(cls, price: float, timestamp: Optional[float] = None) -> None:
        """
        更新SOL价格缓存
        
        参数:
            price: SOL的美元价格
            timestamp: 价格的时间戳，如果为None则使用当前时间
        """
        if timestamp is None:
            timestamp = time.time()
        
        cls._sol_price_cache = (price, timestamp)
        logger.info(f"SOL价格缓存已更新: ${price:.2f} @ {timestamp}")
    
    def get_token_usd_price(self, token_address: str) -> Optional[float]:
        """
        获取任意代币的美元价格
        
        参数:
            token_address: 代币合约地址
            
        返回:
            代币的美元价格，如果失败则返回None
        """
        result = self.get_token_price(token_address)
        if result and 'usdPrice' in result:
            price = float(result['usdPrice'])
            logger.info(f"代币 {token_address} 价格: ${price:.6f}")
            return price
        
        logger.warning(f"无法获取代币价格: {token_address}")
        return None
    
    def batch_get_token_prices(self, token_addresses: list) -> Dict[str, Optional[float]]:
        """
        批量获取多个代币的价格
        
        参数:
            token_addresses: 代币地址列表
            
        返回:
            代币地址到价格的映射字典
        """
        result = {}
        for address in token_addresses:
            price = self.get_token_usd_price(address)
            result[address] = price
        
        return result


# 用法示例
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # 从.env文件加载环境变量
    load_dotenv()
    
    # 从环境变量中获取API密钥
    api_key = os.getenv("MORALIS_API_KEY")
    if not api_key:
        logger.error("未设置MORALIS_API_KEY环境变量，请在.env文件中添加")
        exit(1)
    
    # 创建API客户端
    moralis = MoralisAPI(api_key)
    
    # 获取SOL价格
    sol_price = moralis.get_sol_usd_price()
    print(f"SOL USD价格: ${sol_price if sol_price else 'N/A'}")
    
    # 更新缓存
    if sol_price:
        MoralisAPI.update_sol_price_cache(sol_price)
        
    # 获取缓存的价格
    cached_price, timestamp = MoralisAPI.get_cached_sol_price()
    print(f"缓存的SOL价格: ${cached_price:.2f} @ {timestamp}")
    
    # 获取其他代币价格
    tokens = [
        "So11111111111111111111111111111111111111112",  # SOL
        "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"   # USDC
    ]
    
    prices = moralis.batch_get_token_prices(tokens)
    for token, price in prices.items():
        print(f"代币 {token}: ${price if price else 'N/A'}") 