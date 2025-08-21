#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Chrome策略 - 专门处理Chrome浏览器的版本检测
"""

import re
from typing import Dict, List
from .base_strategy import BaseStrategy


class ChromeStrategy(BaseStrategy):
    """Chrome浏览器版本检测策略"""
    
    def __init__(self):
        super().__init__("chrome")
        self.supported_domains = [
            'google.com/chrome',
            'chrome.google.com'
        ]
    
    def can_handle(self, software_info) -> bool:
        """判断是否为Chrome相关URL"""
        url = software_info.url.lower()
        return any(domain in url for domain in self.supported_domains)
    
    def get_priority(self, software_info) -> int:
        """Chrome策略优先级"""
        return 85
    
    def detect(self, software_info, adapters: Dict) -> Dict:
        """检测Chrome版本"""
        try:
            # Chrome版本检测API
            api_url = "https://versionhistory.googleapis.com/v1/chrome/platforms/mac/channels/stable/versions"
            
            # 尝试API方式
            api_result = self._detect_via_api(api_url, adapters['api_client'])
            if api_result['success']:
                self.record_success()
                return api_result
            
            # API失败时使用网页爬取
            web_result = self._detect_via_web(software_info.url, adapters['web_scraper'])
            if web_result['success']:
                self.record_success()
                return web_result
            
            self.record_failure()
            return {
                'success': False,
                'error': 'API和网页检测都失败'
            }
            
        except Exception as e:
            self.record_failure()
            self.logger.error(f"Chrome策略检测失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _detect_via_api(self, api_url: str, api_client) -> Dict:
        """通过API检测Chrome版本"""
        try:
            response = api_client.get(api_url)
            
            if response.status_code == 200:
                data = response.json()
                versions = data.get('versions', [])
                
                if versions:
                    latest_version = versions[0]
                    version = latest_version.get('version', '')
                    
                    return {
                        'success': True,
                        'version': version,
                        'download_url': 'https://www.google.com/chrome/',
                        'release_date': None,
                        'file_size': None,
                        'checksum': None,
                        'source': 'chrome_api'
                    }
            
            return {
                'success': False,
                'error': f'Chrome API请求失败: {response.status_code}'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _detect_via_web(self, url: str, web_scraper) -> Dict:
        """通过网页检测Chrome版本"""
        try:
            soup = web_scraper.get_soup(url)
            if not soup:
                return {
                    'success': False,
                    'error': '无法获取Chrome页面'
                }
            
            # 查找版本信息
            version_patterns = [
                r'Chrome\s+(\d+\.\d+\.\d+\.\d+)',
                r'版本\s+(\d+\.\d+\.\d+\.\d+)',
                r'Version\s+(\d+\.\d+\.\d+\.\d+)',
            ]
            
            page_text = soup.get_text()
            for pattern in version_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    version = match.group(1)
                    return {
                        'success': True,
                        'version': version,
                        'download_url': url,
                        'release_date': None,
                        'file_size': None,
                        'checksum': None,
                        'source': 'chrome_web'
                    }
            
            return {
                'success': False,
                'error': '未找到Chrome版本信息'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_supported_software(self) -> List[Dict]:
        """获取支持的软件列表"""
        return [
            {
                'name': 'Google Chrome',
                'url': 'https://www.google.com/chrome/',
                'description': 'Google Chrome浏览器'
            }
        ]