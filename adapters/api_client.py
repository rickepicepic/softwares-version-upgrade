#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
API客户端适配器 - 提供统一的API调用接口
"""

import requests
import time
from typing import Dict, Optional, Any
import json

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from utils.logger import get_logger


class APIClient:
    """API客户端适配器"""
    
    def __init__(self, config: Dict = None):
        """
        初始化API客户端
        
        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.logger = get_logger(__name__)
        
        # 基础配置
        self.timeout = self.config.get('timeout', 30)
        self.max_retries = self.config.get('max_retries', 3)
        self.retry_delay = self.config.get('retry_delay', 1)
        
        # 创建会话
        self.session = requests.Session()
        self._setup_session()
        
        # 统计信息
        self.request_count = 0
        self.success_count = 0
        self.failure_count = 0
    
    def _setup_session(self):
        """设置会话配置"""
        # 设置默认headers
        self.session.headers.update({
            'User-Agent': 'MacSoftwareVersionTracker/1.0',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
        })
        
        # 设置重试策略
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def get(self, url: str, **kwargs) -> Optional[requests.Response]:
        """
        发送GET请求
        
        Args:
            url: 请求URL
            **kwargs: 额外的请求参数
            
        Returns:
            Optional[requests.Response]: 响应对象
        """
        return self._request('GET', url, **kwargs)
    
    def post(self, url: str, **kwargs) -> Optional[requests.Response]:
        """
        发送POST请求
        
        Args:
            url: 请求URL
            **kwargs: 额外的请求参数
            
        Returns:
            Optional[requests.Response]: 响应对象
        """
        return self._request('POST', url, **kwargs)
    
    def put(self, url: str, **kwargs) -> Optional[requests.Response]:
        """
        发送PUT请求
        
        Args:
            url: 请求URL
            **kwargs: 额外的请求参数
            
        Returns:
            Optional[requests.Response]: 响应对象
        """
        return self._request('PUT', url, **kwargs)
    
    def delete(self, url: str, **kwargs) -> Optional[requests.Response]:
        """
        发送DELETE请求
        
        Args:
            url: 请求URL
            **kwargs: 额外的请求参数
            
        Returns:
            Optional[requests.Response]: 响应对象
        """
        return self._request('DELETE', url, **kwargs)
    
    def _request(self, method: str, url: str, **kwargs) -> Optional[requests.Response]:
        """
        发送HTTP请求
        
        Args:
            method: HTTP方法
            url: 请求URL
            **kwargs: 额外的请求参数
            
        Returns:
            Optional[requests.Response]: 响应对象
        """
        self.request_count += 1
        
        try:
            # 设置超时
            kwargs.setdefault('timeout', self.timeout)
            
            # 发送请求
            self.logger.debug(f"API请求: {method} {url}")
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            
            self.success_count += 1
            self.logger.debug(f"API请求成功: {method} {url} (状态码: {response.status_code})")
            
            return response
            
        except requests.exceptions.RequestException as e:
            self.failure_count += 1
            self.logger.error(f"API请求失败: {method} {url} - {str(e)}")
            return None
        except Exception as e:
            self.failure_count += 1
            self.logger.error(f"API请求异常: {method} {url} - {str(e)}")
            return None
    
    def get_json(self, url: str, **kwargs) -> Optional[Dict]:
        """
        获取JSON数据
        
        Args:
            url: 请求URL
            **kwargs: 额外的请求参数
            
        Returns:
            Optional[Dict]: JSON数据
        """
        response = self.get(url, **kwargs)
        if not response:
            return None
        
        try:
            return response.json()
        except Exception as e:
            self.logger.error(f"解析JSON失败: {url} - {str(e)}")
            return None
    
    def post_json(self, url: str, data: Dict, **kwargs) -> Optional[Dict]:
        """
        发送JSON数据并获取JSON响应
        
        Args:
            url: 请求URL
            data: 要发送的数据
            **kwargs: 额外的请求参数
            
        Returns:
            Optional[Dict]: JSON响应
        """
        # 设置JSON headers
        headers = kwargs.get('headers', {})
        headers['Content-Type'] = 'application/json'
        kwargs['headers'] = headers
        kwargs['data'] = json.dumps(data)
        
        response = self.post(url, **kwargs)
        if not response:
            return None
        
        try:
            return response.json()
        except Exception as e:
            self.logger.error(f"解析JSON响应失败: {url} - {str(e)}")
            return None
    
    def check_api_availability(self, url: str) -> bool:
        """
        检查API是否可用
        
        Args:
            url: API URL
            
        Returns:
            bool: 是否可用
        """
        try:
            response = self.session.head(url, timeout=10)
            return response.status_code < 400
        except:
            return False
    
    def set_auth_token(self, token: str, token_type: str = 'Bearer'):
        """
        设置认证令牌
        
        Args:
            token: 令牌
            token_type: 令牌类型
        """
        self.session.headers['Authorization'] = f'{token_type} {token}'
    
    def set_api_key(self, api_key: str, header_name: str = 'X-API-Key'):
        """
        设置API密钥
        
        Args:
            api_key: API密钥
            header_name: 头部名称
        """
        self.session.headers[header_name] = api_key
    
    def get_stats(self) -> Dict:
        """
        获取统计信息
        
        Returns:
            Dict: 统计信息
        """
        total_requests = self.request_count
        success_rate = (self.success_count / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'total_requests': total_requests,
            'success_count': self.success_count,
            'failure_count': self.failure_count,
            'success_rate': round(success_rate, 2)
        }
    
    def reset_stats(self):
        """重置统计信息"""
        self.request_count = 0
        self.success_count = 0
        self.failure_count = 0
    
    def close(self):
        """关闭会话"""
        if self.session:
            self.session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()