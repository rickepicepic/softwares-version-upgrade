#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Zoom策略 - 专门处理Zoom的版本检测
"""

import re
from typing import Dict, List
from .base_strategy import BaseStrategy


class ZoomStrategy(BaseStrategy):
    """Zoom版本检测策略"""
    
    def __init__(self):
        super().__init__("zoom")
        self.supported_domains = ['zoom.us']
    
    def can_handle(self, software_info) -> bool:
        """判断是否为Zoom相关URL"""
        return 'zoom.us' in software_info.url.lower()
    
    def get_priority(self, software_info) -> int:
        """Zoom策略优先级"""
        return 75
    
    def detect(self, software_info, adapters: Dict) -> Dict:
        """检测Zoom版本"""
        try:
            result = self._detect_via_web(software_info.url, adapters['web_scraper'])
            
            if result['success']:
                self.record_success()
            else:
                self.record_failure()
            
            return result
            
        except Exception as e:
            self.record_failure()
            self.logger.error(f"Zoom策略检测失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _detect_via_web(self, url: str, web_scraper) -> Dict:
        """通过网页检测Zoom版本"""
        try:
            soup = web_scraper.get_soup(url)
            if not soup:
                return {
                    'success': False,
                    'error': '无法获取Zoom页面'
                }
            
            # Zoom版本模式
            version_patterns = [
                r'(\d+\.\d+\.\d+)',  # 5.16.10
                r'Version\s+(\d+\.\d+)',  # Version 5.16
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
                        'source': 'zoom_web'
                    }
            
            return {
                'success': False,
                'error': '未找到Zoom版本信息'
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
                'name': 'Zoom',
                'url': 'https://zoom.us',
                'description': 'Zoom视频会议软件'
            }
        ]