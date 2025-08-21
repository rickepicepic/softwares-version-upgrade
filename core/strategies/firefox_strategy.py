#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Firefox策略 - 专门处理Firefox浏览器的版本检测
"""

import re
from typing import Dict, List
from .base_strategy import BaseStrategy


class FirefoxStrategy(BaseStrategy):
    """Firefox浏览器版本检测策略"""
    
    def __init__(self):
        super().__init__("firefox")
        self.supported_domains = ['mozilla.org']
    
    def can_handle(self, software_info) -> bool:
        """判断是否为Firefox相关URL"""
        url = software_info.url.lower()
        return 'mozilla.org' in url and 'firefox' in url
    
    def get_priority(self, software_info) -> int:
        """Firefox策略优先级"""
        return 85
    
    def detect(self, software_info, adapters: Dict) -> Dict:
        """检测Firefox版本"""
        try:
            result = self._detect_via_web(software_info.url, adapters['web_scraper'])
            
            if result['success']:
                self.record_success()
            else:
                self.record_failure()
            
            return result
            
        except Exception as e:
            self.record_failure()
            self.logger.error(f"Firefox策略检测失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _detect_via_web(self, url: str, web_scraper) -> Dict:
        """通过网页检测Firefox版本"""
        try:
            soup = web_scraper.get_soup(url)
            if not soup:
                return {
                    'success': False,
                    'error': '无法获取Firefox页面'
                }
            
            # Firefox版本模式
            version_patterns = [
                r'Firefox\s+(\d+\.\d+)',  # Firefox 121.0
                r'(\d+\.\d+\.\d+)',       # 121.0.1
            ]
            
            page_text = soup.get_text()
            
            for pattern in version_patterns:
                match = re.search(pattern, page_text)
                if match:
                    version = match.group(1)
                    return {
                        'success': True,
                        'version': version,
                        'download_url': url,
                        'release_date': None,
                        'file_size': None,
                        'checksum': None,
                        'source': 'firefox_web'
                    }
            
            return {
                'success': False,
                'error': '未找到Firefox版本信息'
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
                'name': 'Mozilla Firefox',
                'url': 'https://www.mozilla.org/firefox/',
                'description': 'Mozilla Firefox浏览器'
            }
        ]