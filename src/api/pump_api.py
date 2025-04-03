#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Pump API客户端
封装对pump.fun API的访问，提供多种API方法
"""

import logging
import json
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

from src.utils.http_client import HttpClient
from src.config.config import HTTP_CONFIG

logger = logging.getLogger(__name__)


class PumpApiClient:
    """
    Pump API客户端类
    封装对pump.fun API的访问，提供各种API方法
    """
    
    # API基础URL
    BASE_URL = "https://frontend-api-v3.pump.fun"
    
    # 默认请求头
    DEFAULT_HEADERS = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "User-Agent": "PumpApiClient/1.0"
    }
    
    def __init__(self, cookie: str = "", use_proxy: bool = False):
        """
        初始化Pump API客户端
        
        参数:
            cookie: 可选的Cookie字符串，用于身份验证
            use_proxy: 是否使用代理
        """
        self.cookie = cookie
        
        # 创建HTTP客户端
        self.http_client = HttpClient(
            base_url=self.BASE_URL,
            proxies=HTTP_CONFIG["proxies"],
            proxy_enabled=use_proxy and HTTP_CONFIG["proxy_enabled"],
            timeout=HTTP_CONFIG["timeout"],
            verify_ssl=HTTP_CONFIG["verify_ssl"],
            headers=self.DEFAULT_HEADERS.copy()
        )
        
        # 如果提供了Cookie，添加到请求头
        if cookie:
            self.http_client.set_header("Cookie", cookie)
    
    def set_cookie(self, cookie: str) -> None:
        """
        设置Cookie
        
        参数:
            cookie: Cookie字符串
        """
        self.cookie = cookie
        self.http_client.set_header("Cookie", cookie)
    
    def update_cookie(self, cookie: str) -> None:
        """
        更新Cookie，与set_cookie功能相同，但更语义化
        
        参数:
            cookie: 新的Cookie字符串
        """
        if cookie != self.cookie:
            logger.debug("更新API客户端Cookie")
            self.set_cookie(cookie)
    
    def enable_proxy(self) -> None:
        """启用代理"""
        self.http_client.enable_proxy()
    
    def disable_proxy(self) -> None:
        """禁用代理"""
        self.http_client.disable_proxy()
    
    def get_token_replies(self, 
                          token_mint: str, 
                          limit: int = 1000, 
                          offset: int = 0) -> Dict[str, Any]:
        """
        获取代币的回复列表
        
        参数:
            token_mint: 代币的mint地址
            limit: 返回的最大回复数量
            offset: 偏移量，用于分页
            
        返回:
            包含回复列表和分页信息的字典
        """
        # 构建API路径
        path = f"/replies/{token_mint}"
        
        # 设置查询参数
        params = {
            "limit": limit,
            "offset": offset
        }
        
        # 发送请求
        try:
            logger.info(f"获取代币 {token_mint} 的回复列表，limit={limit}, offset={offset}")
            response = self.http_client.get(path, params=params)
            
            # 解析JSON响应
            data = response.json()
            
            # 记录结果
            if 'replies' in data:
                logger.info(f"成功获取 {len(data['replies'])} 条回复")
            
            return data
        except Exception as e:
            logger.error(f"获取代币回复失败: {str(e)}")
            raise
    
    def get_token_info(self, token_mint: str) -> Dict[str, Any]:
        """
        获取代币信息
        
        参数:
            token_mint: 代币的mint地址
            
        返回:
            代币信息字典
        """
        # 构建API路径
        path = f"/token/{token_mint}"
        
        # 发送请求
        try:
            logger.info(f"获取代币 {token_mint} 的信息")
            response = self.http_client.get(path)
            
            # 解析JSON响应
            data = response.json()
            
            # 记录结果
            logger.info(f"成功获取代币 {token_mint} 的信息")
            
            return data
        except Exception as e:
            logger.error(f"获取代币信息失败: {str(e)}")
            raise
    
    def search_tokens(self, 
                      query: str, 
                      limit: int = 25) -> List[Dict[str, Any]]:
        """
        搜索代币
        
        参数:
            query: 搜索关键词
            limit: 返回的最大代币数量
            
        返回:
            代币列表
        """
        # 构建API路径
        path = "/search"
        
        # 设置查询参数
        params = {
            "q": query,
            "limit": limit
        }
        
        # 发送请求
        try:
            logger.info(f"搜索代币，关键词='{query}'，limit={limit}")
            response = self.http_client.get(path, params=params)
            
            # 解析JSON响应
            data = response.json()
            
            # 记录结果
            if isinstance(data, list):
                logger.info(f"搜索到 {len(data)} 个代币")
            
            return data
        except Exception as e:
            logger.error(f"搜索代币失败: {str(e)}")
            raise
    
    def get_user_tokens(self, 
                        user_address: str, 
                        limit: int = 100, 
                        offset: int = 0) -> Dict[str, Any]:
        """
        获取用户持有的代币列表
        
        参数:
            user_address: 用户的钱包地址
            limit: 返回的最大代币数量
            offset: 偏移量，用于分页
            
        返回:
            包含代币列表和分页信息的字典
        """
        # 构建API路径
        path = f"/user/{user_address}/tokens"
        
        # 设置查询参数
        params = {
            "limit": limit,
            "offset": offset
        }
        
        # 发送请求
        try:
            logger.info(f"获取用户 {user_address} 的代币列表，limit={limit}, offset={offset}")
            response = self.http_client.get(path, params=params)
            
            # 解析JSON响应
            data = response.json()
            
            # 记录结果
            logger.info(f"成功获取用户 {user_address} 的代币列表")
            
            return data
        except Exception as e:
            logger.error(f"获取用户代币列表失败: {str(e)}")
            raise
    
    def get_trending_tokens(self, 
                            limit: int = 100, 
                            offset: int = 0) -> Dict[str, Any]:
        """
        获取热门代币列表
        
        参数:
            limit: 返回的最大代币数量
            offset: 偏移量，用于分页
            
        返回:
            包含热门代币列表和分页信息的字典
        """
        # 构建API路径
        path = "/trending"
        
        # 设置查询参数
        params = {
            "limit": limit,
            "offset": offset
        }
        
        # 发送请求
        try:
            logger.info(f"获取热门代币列表，limit={limit}, offset={offset}")
            response = self.http_client.get(path, params=params)
            
            # 解析JSON响应
            data = response.json()
            
            # 记录结果
            logger.info(f"成功获取热门代币列表")
            
            return data
        except Exception as e:
            logger.error(f"获取热门代币列表失败: {str(e)}")
            raise
    
    def save_response_to_file(self, 
                              data: Dict[str, Any], 
                              filename: str) -> bool:
        """
        将API响应保存到文件
        
        参数:
            data: API响应数据
            filename: 文件名
            
        返回:
            是否成功保存
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"数据已保存到文件 {filename}")
            return True
        except Exception as e:
            logger.error(f"保存数据到文件失败: {str(e)}")
            return False
    
    def close(self) -> None:
        """关闭HTTP客户端连接"""
        self.http_client.close()
    
    def __enter__(self):
        """支持上下文管理器"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """支持上下文管理器，自动关闭连接"""
        self.close() 