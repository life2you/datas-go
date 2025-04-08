#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
HTTP客户端工具
支持代理配置和开关控制
"""

import logging
import requests
import json
from typing import Dict, Any, Optional, Union, List
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

class HttpClient:
    """
    HTTP客户端工具类
    支持代理配置和开关控制
    """
    
    def __init__(self, 
                 base_url: str = "",
                 proxy: str = None,
                 proxy_auth: Any = None,
                 proxy_enabled: bool = False,
                 timeout: int = 30,
                 verify_ssl: bool = True,
                 headers: Dict[str, str] = None):
        """
        初始化HTTP客户端
        
        参数:
            base_url: 基础URL，所有请求都将基于此URL
            proxy: 代理URL，格式为 "http://proxy:port" 或 "https://proxy:port"
            proxy_auth: 代理认证信息
            proxy_enabled: 是否启用代理
            timeout: 请求超时时间（秒）
            verify_ssl: 是否验证SSL证书
            headers: 默认请求头
        """
        self.base_url = base_url
        self.proxy = proxy
        self.proxy_auth = proxy_auth
        self.proxy_enabled = proxy_enabled
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.headers = headers or {"Content-Type": "application/json"}
        self.session = requests.Session()
    
    def enable_proxy(self) -> None:
        """启用代理"""
        self.proxy_enabled = True
        logger.info("已启用HTTP代理")
    
    def disable_proxy(self) -> None:
        """禁用代理"""
        self.proxy_enabled = False
        logger.info("已禁用HTTP代理")
    
    def set_proxy(self, proxy_url: str, proxy_auth: Any = None) -> None:
        """
        设置代理
        
        参数:
            proxy_url: 代理服务器URL
            proxy_auth: 代理认证信息
        """
        self.proxy = proxy_url
        self.proxy_auth = proxy_auth
        logger.info(f"已设置代理: {self.proxy}")
    
    def clear_proxy(self) -> None:
        """清除所有代理设置"""
        self.proxy = None
        self.proxy_auth = None
        logger.info("已清除所有代理设置")
    
    def set_header(self, key: str, value: str) -> None:
        """
        设置请求头
        
        参数:
            key: 请求头名称
            value: 请求头值
        """
        self.headers[key] = value
    
    def set_headers(self, headers: Dict[str, str]) -> None:
        """
        批量设置请求头
        
        参数:
            headers: 请求头字典
        """
        self.headers.update(headers)
    
    def _prepare_request(self, 
                         url: str, 
                         params: Dict[str, Any] = None, 
                         headers: Dict[str, str] = None,
                         **kwargs) -> Dict[str, Any]:
        """
        准备请求参数
        
        参数:
            url: 请求URL
            params: URL参数
            headers: 请求头
            **kwargs: 其他参数
            
        返回:
            准备好的请求参数字典
        """
        # 合并基础URL和请求URL
        if self.base_url and not url.startswith(('http://', 'https://')):
            url = urljoin(self.base_url, url)
        
        # 合并默认请求头和自定义请求头
        request_headers = self.headers.copy()
        if headers:
            request_headers.update(headers)
        
        # 设置代理
        request_proxies = None
        if self.proxy_enabled and self.proxy:
            request_proxies = {
                "http": self.proxy,
                "https": self.proxy
            }
        
        request_params = {
            "url": url,
            "params": params,
            "headers": request_headers,
            "timeout": kwargs.get("timeout", self.timeout),
            "verify": kwargs.get("verify", self.verify_ssl),
            "proxies": request_proxies
        }
        
        # 移除None值
        return {k: v for k, v in request_params.items() if v is not None}
    
    def request(self, 
                method: str, 
                url: str, 
                params: Dict[str, Any] = None, 
                data: Any = None,
                json_data: Dict[str, Any] = None,
                headers: Dict[str, str] = None, 
                **kwargs) -> requests.Response:
        """
        发送HTTP请求
        
        参数:
            method: HTTP方法，如 "GET", "POST" 等
            url: 请求URL
            params: URL参数
            data: 请求体数据
            json_data: JSON请求体数据
            headers: 请求头
            **kwargs: 其他参数
            
        返回:
            requests.Response对象
        """
        request_params = self._prepare_request(url, params, headers, **kwargs)
        
        # 添加data和json参数
        if data is not None:
            request_params["data"] = data
        if json_data is not None:
            request_params["json"] = json_data
        
        try:
            logger.debug(f"发送{method}请求: {url}")
            if self.proxy_enabled:
                logger.debug(f"使用代理: {self.proxy}")
            
            response = self.session.request(method, **request_params)
            response.raise_for_status()  # 抛出HTTP错误
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"请求失败: {str(e)}")
            raise
    
    def get(self, 
            url: str, 
            params: Dict[str, Any] = None, 
            headers: Dict[str, str] = None, 
            **kwargs) -> requests.Response:
        """
        发送GET请求
        
        参数:
            url: 请求URL
            params: URL参数
            headers: 请求头
            **kwargs: 其他参数
            
        返回:
            requests.Response对象
        """
        return self.request("GET", url, params=params, headers=headers, **kwargs)
    
    def post(self, 
             url: str, 
             data: Any = None,
             json_data: Dict[str, Any] = None,
             params: Dict[str, Any] = None, 
             headers: Dict[str, str] = None, 
             **kwargs) -> requests.Response:
        """
        发送POST请求
        
        参数:
            url: 请求URL
            data: 请求体数据
            json_data: JSON请求体数据
            params: URL参数
            headers: 请求头
            **kwargs: 其他参数
            
        返回:
            requests.Response对象
        """
        return self.request("POST", url, params=params, data=data, json_data=json_data, headers=headers, **kwargs)
    
    def put(self, 
            url: str, 
            data: Any = None,
            json_data: Dict[str, Any] = None,
            params: Dict[str, Any] = None, 
            headers: Dict[str, str] = None, 
            **kwargs) -> requests.Response:
        """
        发送PUT请求
        
        参数:
            url: 请求URL
            data: 请求体数据
            json_data: JSON请求体数据
            params: URL参数
            headers: 请求头
            **kwargs: 其他参数
            
        返回:
            requests.Response对象
        """
        return self.request("PUT", url, params=params, data=data, json_data=json_data, headers=headers, **kwargs)
    
    def delete(self, 
               url: str, 
               params: Dict[str, Any] = None, 
               headers: Dict[str, str] = None, 
               **kwargs) -> requests.Response:
        """
        发送DELETE请求
        
        参数:
            url: 请求URL
            params: URL参数
            headers: 请求头
            **kwargs: 其他参数
            
        返回:
            requests.Response对象
        """
        return self.request("DELETE", url, params=params, headers=headers, **kwargs)
    
    def patch(self, 
              url: str, 
              data: Any = None,
              json_data: Dict[str, Any] = None,
              params: Dict[str, Any] = None, 
              headers: Dict[str, str] = None, 
              **kwargs) -> requests.Response:
        """
        发送PATCH请求
        
        参数:
            url: 请求URL
            data: 请求体数据
            json_data: JSON请求体数据
            params: URL参数
            headers: 请求头
            **kwargs: 其他参数
            
        返回:
            requests.Response对象
        """
        return self.request("PATCH", url, params=params, data=data, json_data=json_data, headers=headers, **kwargs)
    
    def get_json(self, 
                 url: str, 
                 params: Dict[str, Any] = None, 
                 headers: Dict[str, str] = None, 
                 **kwargs) -> Dict[str, Any]:
        """
        发送GET请求并解析JSON响应
        
        参数:
            url: 请求URL
            params: URL参数
            headers: 请求头
            **kwargs: 其他参数
            
        返回:
            解析后的JSON数据
        """
        response = self.get(url, params=params, headers=headers, **kwargs)
        return response.json()
    
    def post_json(self, 
                  url: str, 
                  json_data: Dict[str, Any] = None,
                  params: Dict[str, Any] = None, 
                  headers: Dict[str, str] = None, 
                  **kwargs) -> Dict[str, Any]:
        """
        发送POST请求并解析JSON响应
        
        参数:
            url: 请求URL
            json_data: JSON请求体数据
            params: URL参数
            headers: 请求头
            **kwargs: 其他参数
            
        返回:
            解析后的JSON数据
        """
        response = self.post(url, json_data=json_data, params=params, headers=headers, **kwargs)
        return response.json()
    
    def close(self) -> None:
        """关闭会话"""
        self.session.close()
        logger.debug("已关闭HTTP会话")
    
    def __enter__(self):
        """支持上下文管理器"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """支持上下文管理器，自动关闭会话"""
        self.close() 