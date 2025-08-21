#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Adobe策略 - 专门处理Adobe产品的版本检测
"""

import re
from typing import Dict, List
from .base_strategy import BaseStrategy


class AdobeStrategy(BaseStrategy):
    """Adobe产品版本检测策略"""
    
    def __init__(self):
        super().__init__("adobe")
        self.supported_domains = ['adobe.com']
    
    def can_handle(self, software_info) -> bool:
        """判断是否为Adobe相关URL"""
        return 'adobe.com' in software_info.url.lower()
    
    def get_priority(self, software_info) -> int:
        """Adobe策略优先级"""
        return 75
    
    def detect(self, software_info, adapters: Dict) -> Dict:
        """检测Adobe产品版本"""
        try:
            result = self._detect_via_web(software_info.url, adapters['web_scraper'])
            
            if result['success']:
                self.record_success()
            else:
                self.record_failure()
            
            return result
            
        except Exception as e:
            self.record_failure()
            self.logger.error(f"Adobe策略检测失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _detect_via_web(self, url: str, web_scraper) -> Dict:
        """通过网页检测Adobe产品版本"""
        try:
            soup = web_scraper.get_soup(url)
            if not soup:
                return {
                    'success': False,
                    'error': '无法获取Adobe页面'
                }
            
            # Adobe产品通常使用年份版本
            version_patterns = [
                r'(\d{4})',  # 年份版本如2024
                r'CC\s+(\d{4})',  # Creative Cloud 2024
                r'(\d+\.\d+)',  # 版本号如24.0
            ]
            
            page_text = soup.get_text()
            
            # 特殊处理Creative Cloud
            if 'creative cloud' in page_text.lower():
                # 查找年份
                year_match = re.search(r'20(\d{2})', page_text)
                if year_match:
                    year = f"20{year_match.group(1)}"
                    return {
                        'success': True,
                        'version': f"CC {year}",
                        'download_url': url,
                        'release_date': None,
                        'file_size': None,
                        'checksum': None,
                        'source': 'adobe_cc'
                    }
            
            # 查找版本号
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
                        'source': 'adobe_web'
                    }
            
            return {
                'success': False,
                'error': '未找到Adobe产品版本信息'
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
                'name': 'Adobe Photoshop',
                'url': 'https://www.adobe.com/products/photoshop.html',
                'description': 'Adobe Photoshop图像编辑软件'
            },
            {
                'name': 'Adobe Illustrator',
                'url': 'https://www.adobe.com/products/illustrator.html',
                'description': 'Adobe Illustrator矢量图形软件'
            }
        ]