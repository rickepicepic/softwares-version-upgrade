#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
网页爬虫适配器 - 提供统一的网页爬取接口
"""

import requests
from bs4 import BeautifulSoup
import time
import random
from typing import Dict, Optional, List
from urllib.parse import urljoin, urlparse
import logging

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from utils.logger import get_logger


class WebScraper:
    """网页爬虫适配器"""
    
    def __init__(self, config: Dict = None):
        """
        初始化网页爬虫
        
        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.logger = get_logger(__name__)
        
        # 基础配置
        self.timeout = self.config.get('timeout', 30)
        self.max_retries = self.config.get('max_retries', 3)
        self.retry_delay = self.config.get('retry_delay', 1)
        
        # User-Agent池
        self.user_agents = self.config.get('user_agents', [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/120.0'
        ])
        
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
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
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
    
    def get_page(self, url: str, **kwargs) -> Optional[requests.Response]:
        """
        获取页面响应
        
        Args:
            url: 目标URL
            **kwargs: 额外的请求参数
            
        Returns:
            Optional[requests.Response]: 响应对象
        """
        self.request_count += 1
        
        try:
            # 随机选择User-Agent
            headers = kwargs.get('headers', {})
            if 'User-Agent' not in headers:
                headers['User-Agent'] = random.choice(self.user_agents)
            kwargs['headers'] = headers
            
            # 设置超时
            kwargs.setdefault('timeout', self.timeout)
            
            # 发送请求
            self.logger.debug(f"请求页面: {url}")
            response = self.session.get(url, **kwargs)
            response.raise_for_status()
            
            # 设置编码
            if response.encoding == 'ISO-8859-1':
                response.encoding = response.apparent_encoding or 'utf-8'
            
            self.success_count += 1
            self.logger.debug(f"成功获取页面: {url} (状态码: {response.status_code})")
            
            return response
            
        except requests.exceptions.RequestException as e:
            self.failure_count += 1
            self.logger.error(f"请求失败: {url} - {str(e)}")
            return None
        except Exception as e:
            self.failure_count += 1
            self.logger.error(f"未知错误: {url} - {str(e)}")
            return None
    
    def get_soup(self, url: str, parser: str = 'html.parser', **kwargs) -> Optional[BeautifulSoup]:
        """
        获取BeautifulSoup对象
        
        Args:
            url: 目标URL
            parser: 解析器类型
            **kwargs: 额外的请求参数
            
        Returns:
            Optional[BeautifulSoup]: BeautifulSoup对象
        """
        response = self.get_page(url, **kwargs)
        if not response:
            return None
        
        try:
            soup = BeautifulSoup(response.text, parser)
            return soup
        except Exception as e:
            self.logger.error(f"解析HTML失败: {url} - {str(e)}")
            return None
    
    def get_json(self, url: str, **kwargs) -> Optional[Dict]:
        """
        获取JSON数据
        
        Args:
            url: 目标URL
            **kwargs: 额外的请求参数
            
        Returns:
            Optional[Dict]: JSON数据
        """
        response = self.get_page(url, **kwargs)
        if not response:
            return None
        
        try:
            return response.json()
        except Exception as e:
            self.logger.error(f"解析JSON失败: {url} - {str(e)}")
            return None
    
    def download_file(self, url: str, local_path: str, chunk_size: int = 8192) -> bool:
        """
        下载文件
        
        Args:
            url: 文件URL
            local_path: 本地保存路径
            chunk_size: 块大小
            
        Returns:
            bool: 是否成功
        """
        try:
            self.logger.info(f"开始下载文件: {url}")
            
            response = self.session.get(url, stream=True, timeout=self.timeout)
            response.raise_for_status()
            
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
            
            self.logger.info(f"文件下载完成: {local_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"文件下载失败: {url} - {str(e)}")
            return False
    
    def get_page_with_retry(self, url: str, max_retries: int = None, **kwargs) -> Optional[requests.Response]:
        """
        带重试的页面获取
        
        Args:
            url: 目标URL
            max_retries: 最大重试次数
            **kwargs: 额外的请求参数
            
        Returns:
            Optional[requests.Response]: 响应对象
        """
        max_retries = max_retries or self.max_retries
        
        for attempt in range(max_retries):
            response = self.get_page(url, **kwargs)
            if response:
                return response
            
            if attempt < max_retries - 1:
                delay = self.retry_delay * (2 ** attempt)  # 指数退避
                self.logger.warning(f"重试 {attempt + 1}/{max_retries} 在 {delay}s 后: {url}")
                time.sleep(delay)
        
        return None
    
    def check_url_accessibility(self, url: str) -> bool:
        """
        检查URL是否可访问
        
        Args:
            url: 目标URL
            
        Returns:
            bool: 是否可访问
        """
        try:
            response = self.session.head(url, timeout=10)
            return response.status_code < 400
        except:
            return False
    
    def extract_links(self, soup: BeautifulSoup, base_url: str, 
                     filter_func=None) -> List[str]:
        """
        提取页面中的链接
        
        Args:
            soup: BeautifulSoup对象
            base_url: 基础URL
            filter_func: 过滤函数
            
        Returns:
            List[str]: 链接列表
        """
        links = []
        
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if href:
                # 转换为绝对URL
                absolute_url = urljoin(base_url, href)
                
                # 应用过滤函数
                if filter_func is None or filter_func(absolute_url, link):
                    links.append(absolute_url)
        
        return links
    
    def extract_images(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """
        提取页面中的图片链接
        
        Args:
            soup: BeautifulSoup对象
            base_url: 基础URL
            
        Returns:
            List[str]: 图片链接列表
        """
        images = []
        
        for img in soup.find_all('img', src=True):
            src = img.get('src')
            if src:
                absolute_url = urljoin(base_url, src)
                images.append(absolute_url)
        
        return images
    
    def get_page_metadata(self, soup: BeautifulSoup) -> Dict:
        """
        提取页面元数据
        
        Args:
            soup: BeautifulSoup对象
            
        Returns:
            Dict: 元数据字典
        """
        metadata = {}
        
        # 标题
        title = soup.find('title')
        if title:
            metadata['title'] = title.get_text().strip()
        
        # Meta标签
        meta_tags = soup.find_all('meta')
        for meta in meta_tags:
            name = meta.get('name') or meta.get('property')
            content = meta.get('content')
            if name and content:
                metadata[name] = content
        
        return metadata
    
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