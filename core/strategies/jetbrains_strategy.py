#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
JetBrains策略 - 专门处理JetBrains产品的版本检测
"""

import re
from typing import Dict, List
from .base_strategy import BaseStrategy


class JetBrainsStrategy(BaseStrategy):
    """JetBrains产品版本检测策略"""
    
    def __init__(self):
        super().__init__("jetbrains")
        self.supported_domains = ['jetbrains.com']
    
    def can_handle(self, software_info) -> bool:
        """判断是否为JetBrains相关URL"""
        return 'jetbrains.com' in software_info.url.lower()
    
    def get_priority(self, software_info) -> int:
        """JetBrains策略优先级"""
        return 75
    
    def detect(self, software_info, adapters: Dict) -> Dict:
        """检测JetBrains产品版本"""
        try:
            result = self._detect_via_web(software_info.url, adapters['web_scraper'])
            
            if result['success']:
                self.record_success()
            else:
                self.record_failure()
            
            return result
            
        except Exception as e:
            self.record_failure()
            self.logger.error(f"JetBrains策略检测失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _detect_via_web(self, url: str, web_scraper) -> Dict:
        """通过网页检测JetBrains产品版本"""
        try:
            soup = web_scraper.get_soup(url)
            if not soup:
                return {
                    'success': False,
                    'error': '无法获取JetBrains页面'
                }
            
            # JetBrains版本模式
            version_patterns = [
                r'(\d{4}\.\d+\.\d+)',  # 2024.1.0
                r'(\d{4}\.\d+)',       # 2024.1
                r'版本\s+(\d+\.\d+)',   # 版本 2024.1
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
                        'source': 'jetbrains_web'
                    }
            
            return {
                'success': False,
                'error': '未找到JetBrains产品版本信息'
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
                'name': 'PyCharm',
                'url': 'https://www.jetbrains.com/pycharm/',
                'description': 'JetBrains PyCharm Python IDE'
            },
            {
                'name': 'IntelliJ IDEA',
                'url': 'https://www.jetbrains.com/idea/',
                'description': 'JetBrains IntelliJ IDEA Java IDE'
            }
        ]