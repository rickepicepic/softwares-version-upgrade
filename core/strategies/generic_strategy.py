#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
通用策略 - 处理没有专门策略的软件
"""

import re
from typing import Dict, List
from urllib.parse import urljoin, urlparse

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from core.strategies.base_strategy import BaseStrategy


class GenericStrategy(BaseStrategy):
    """通用版本检测策略"""
    
    def __init__(self):
        super().__init__("generic")
        
        # 版本号匹配模式
        self.version_patterns = [
            r'v?(\d+\.\d+\.\d+(?:\.\d+)?)',  # 标准版本号 1.2.3 或 1.2.3.4
            r'(\d{4}\.\d+\.\d+)',           # 年份版本 2024.1.0
            r'版本\s*[：:]\s*(\d+\.\d+\.\d+)',  # 中文版本
            r'version\s*[：:]\s*(\d+\.\d+\.\d+)',  # 英文版本
            r'(\d+\.\d+)',                  # 简化版本 1.2
            r'Build\s+(\d+\.\d+)',          # Build版本
            r'Release\s+(\d+\.\d+)',        # Release版本
        ]
        
        # 下载关键词
        self.download_keywords = [
            'download', 'Download', 'DOWNLOAD',
            '下载', '立即下载', 'Mac下载', '免费下载',
            'dmg', 'pkg', 'zip', 'installer',
            'get', 'Get', 'GET',
            'install', 'Install', 'INSTALL',
        ]
        
        # Mac相关关键词
        self.mac_keywords = [
            'mac', 'macos', 'osx', 'darwin',
            'apple', 'macintosh',
            '.dmg', '.pkg', '.app'
        ]
    
    def can_handle(self, software_info) -> bool:
        """通用策略可以处理任何软件"""
        return True
    
    def get_priority(self, software_info) -> int:
        """通用策略优先级最低"""
        return 1
    
    def detect(self, software_info, adapters: Dict) -> Dict:
        """通用版本检测逻辑"""
        try:
            # 首先尝试静态页面爬取
            static_result = self._detect_static_page(software_info, adapters['web_scraper'])
            if static_result['success']:
                self.record_success()
                return static_result
            
            # 静态爬取失败，尝试动态页面
            dynamic_result = self._detect_dynamic_page(software_info, adapters['selenium_driver'])
            if dynamic_result['success']:
                self.record_success()
                return dynamic_result
            
            self.record_failure()
            return {
                'success': False,
                'error': '静态和动态检测都失败'
            }
            
        except Exception as e:
            self.record_failure()
            self.logger.error(f"通用策略检测失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _detect_static_page(self, software_info, web_scraper) -> Dict:
        """静态页面检测"""
        try:
            # 获取页面内容
            soup = web_scraper.get_soup(software_info.url)
            if not soup:
                return {
                    'success': False,
                    'error': '无法获取页面内容'
                }
            
            # 提取版本号
            version = self._extract_version_from_page(soup)
            
            # 提取下载链接
            download_url = self._extract_download_url(soup, software_info.url)
            
            if version and version != "未找到版本信息":
                return {
                    'success': True,
                    'version': version,
                    'download_url': download_url or software_info.url,
                    'release_date': None,
                    'file_size': None,
                    'checksum': None,
                    'source': 'static_page'
                }
            else:
                return {
                    'success': False,
                    'error': '未找到版本信息'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _detect_dynamic_page(self, software_info, selenium_driver) -> Dict:
        """动态页面检测"""
        try:
            # 使用Selenium获取页面
            page_source = selenium_driver.get_page_source(software_info.url)
            if not page_source:
                return {
                    'success': False,
                    'error': '无法获取动态页面内容'
                }
            
            # 解析页面内容
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # 提取版本号
            version = self._extract_version_from_page(soup)
            
            # 提取下载链接
            download_url = self._extract_download_url(soup, software_info.url)
            
            if version and version != "未找到版本信息":
                return {
                    'success': True,
                    'version': version,
                    'download_url': download_url or software_info.url,
                    'release_date': None,
                    'file_size': None,
                    'checksum': None,
                    'source': 'dynamic_page'
                }
            else:
                return {
                    'success': False,
                    'error': '未找到版本信息'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _extract_version_from_page(self, soup) -> str:
        """从页面中提取版本号"""
        # 获取页面所有文本
        page_text = soup.get_text()
        
        # 尝试各种版本号模式
        for pattern in self.version_patterns:
            matches = re.findall(pattern, page_text, re.IGNORECASE)
            if matches:
                # 返回最可能的版本号（通常是最长的或最新的）
                if isinstance(matches[0], tuple):
                    version = matches[0][0] if matches[0] else None
                else:
                    version = max(matches, key=len)
                
                if version and self._is_valid_version(version):
                    self.logger.info(f"找到版本号: {version}")
                    return version
        
        # 从特定元素中查找版本号
        version_elements = soup.find_all(text=re.compile(r'\d+\.\d+'))
        for element in version_elements:
            for pattern in self.version_patterns:
                match = re.search(pattern, element, re.IGNORECASE)
                if match:
                    version = match.group(1)
                    if self._is_valid_version(version):
                        self.logger.info(f"从元素找到版本号: {version}")
                        return version
        
        # 从下载链接中查找版本号
        download_links = soup.find_all('a', href=True)
        for link in download_links:
            href = link.get('href', '')
            for pattern in self.version_patterns:
                match = re.search(pattern, href, re.IGNORECASE)
                if match:
                    version = match.group(1)
                    if self._is_valid_version(version):
                        self.logger.info(f"从下载链接找到版本号: {version}")
                        return version
        
        return "未找到版本信息"
    
    def _extract_download_url(self, soup, base_url: str) -> str:
        """提取下载链接"""
        # 查找包含下载关键词的链接
        for keyword in self.download_keywords:
            # 查找文本包含关键词的链接
            links = soup.find_all('a', href=True, string=re.compile(keyword, re.I))
            if links:
                href = links[0].get('href')
                return urljoin(base_url, href)
            
            # 查找href包含关键词的链接
            links = soup.find_all('a', href=re.compile(keyword, re.I))
            if links:
                href = links[0].get('href')
                return urljoin(base_url, href)
        
        # 查找Mac相关的下载链接
        mac_links = soup.find_all('a', href=True)
        for link in mac_links:
            href = link.get('href', '').lower()
            text = link.get_text().lower()
            
            # 检查是否包含Mac关键词和文件扩展名
            if any(keyword in (href + text) for keyword in self.mac_keywords):
                return urljoin(base_url, link.get('href'))
        
        # 查找任何可能的下载链接
        download_links = soup.find_all('a', href=True)
        for link in download_links:
            href = link.get('href', '').lower()
            if any(ext in href for ext in ['.dmg', '.pkg', '.zip', '.tar.gz']):
                return urljoin(base_url, link.get('href'))
        
        return None
    
    def _is_valid_version(self, version: str) -> bool:
        """检查版本号是否有效"""
        if not version:
            return False
        
        # 基本格式检查
        if re.match(r'^\d+(\.\d+)*$', version):
            return True
        
        # 年份格式检查
        if re.match(r'^\d{4}\.\d+(\.\d+)*$', version):
            return True
        
        # 检查是否过于简单（如单个数字）
        if re.match(r'^\d+$', version) and len(version) < 2:
            return False
        
        return True
    
    def _find_download_page(self, base_url: str, web_scraper) -> str:
        """查找下载页面"""
        try:
            soup = web_scraper.get_soup(base_url)
            if not soup:
                return base_url
            
            # 查找下载页面链接
            for keyword in self.download_keywords:
                download_links = soup.find_all('a', href=True, string=re.compile(keyword, re.I))
                for link in download_links:
                    full_url = urljoin(base_url, link['href'])
                    self.logger.info(f"找到潜在下载页面: {full_url}")
                    return full_url
            
            return base_url
            
        except Exception as e:
            self.logger.error(f"查找下载页面失败: {str(e)}")
            return base_url
    
    def get_supported_software(self) -> List[Dict]:
        """通用策略支持所有软件"""
        return [
            {
                'name': '通用软件',
                'url': 'https://example.com',
                'description': '通用策略可以处理任何软件网站'
            }
        ]