#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
VS Code策略 - 专门处理Visual Studio Code的版本检测
"""

import re
from typing import Dict, List
from .base_strategy import BaseStrategy


class VSCodeStrategy(BaseStrategy):
    """VS Code版本检测策略"""
    
    def __init__(self):
        super().__init__("vscode")
        self.supported_domains = ['code.visualstudio.com']
    
    def can_handle(self, software_info) -> bool:
        """判断是否为VS Code相关URL"""
        return 'code.visualstudio.com' in software_info.url.lower()
    
    def get_priority(self, software_info) -> int:
        """VS Code策略优先级"""
        return 85
    
    def detect(self, software_info, adapters: Dict) -> Dict:
        """检测VS Code版本"""
        try:
            result = self._detect_via_web(software_info.url, adapters['web_scraper'])
            
            if result['success']:
                self.record_success()
            else:
                self.record_failure()
            
            return result
            
        except Exception as e:
            self.record_failure()
            self.logger.error(f"VS Code策略检测失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _detect_via_web(self, url: str, web_scraper) -> Dict:
        """通过网页检测VS Code版本"""
        try:
            soup = web_scraper.get_soup(url)
            if not soup:
                return {
                    'success': False,
                    'error': '无法获取VS Code页面'
                }
            
            # VS Code版本模式
            version_patterns = [
                r'(\d+\.\d+\.\d+)',  # 1.85.0
                r'Version\s+(\d+\.\d+)',  # Version 1.85
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
                        'source': 'vscode_web'
                    }
            
            return {
                'success': False,
                'error': '未找到VS Code版本信息'
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
                'name': 'Visual Studio Code',
                'url': 'https://code.visualstudio.com',
                'description': 'Microsoft Visual Studio Code编辑器'
            }
        ]