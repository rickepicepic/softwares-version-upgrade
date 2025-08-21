#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Microsoft策略 - 专门处理Microsoft产品的版本检测
"""

import re
from typing import Dict, List
from .base_strategy import BaseStrategy


class MicrosoftStrategy(BaseStrategy):
    """Microsoft产品版本检测策略"""
    
    def __init__(self):
        super().__init__("microsoft")
        self.supported_domains = [
            'microsoft.com',
            'office.com',
            'visualstudio.com'
        ]
    
    def can_handle(self, software_info) -> bool:
        """判断是否为Microsoft相关URL"""
        url = software_info.url.lower()
        return any(domain in url for domain in self.supported_domains)
    
    def get_priority(self, software_info) -> int:
        """Microsoft策略优先级"""
        return 80
    
    def detect(self, software_info, adapters: Dict) -> Dict:
        """检测Microsoft产品版本"""
        try:
            # 根据产品类型选择检测方法
            if 'office' in software_info.url.lower() or 'microsoft-365' in software_info.url.lower():
                result = self._detect_office_version(software_info.url, adapters['web_scraper'])
            elif 'visualstudio' in software_info.url.lower():
                result = self._detect_vs_version(software_info.url, adapters['web_scraper'])
            else:
                result = self._detect_generic_microsoft(software_info.url, adapters['web_scraper'])
            
            if result['success']:
                self.record_success()
            else:
                self.record_failure()
            
            return result
            
        except Exception as e:
            self.record_failure()
            self.logger.error(f"Microsoft策略检测失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _detect_office_version(self, url: str, web_scraper) -> Dict:
        """检测Office版本"""
        try:
            soup = web_scraper.get_soup(url)
            if not soup:
                return {
                    'success': False,
                    'error': '无法获取Office页面'
                }
            
            # 查找版本信息的常见模式
            version_patterns = [
                r'Office\s+(\d{4})',  # Office 2021
                r'Microsoft\s+365',   # Microsoft 365
                r'版本\s+(\d+\.\d+)',  # 版本 16.0
            ]
            
            page_text = soup.get_text()
            
            # 特殊处理Microsoft 365
            if 'microsoft 365' in page_text.lower() or 'office 365' in page_text.lower():
                return {
                    'success': True,
                    'version': 'Microsoft 365',
                    'download_url': url,
                    'release_date': None,
                    'file_size': None,
                    'checksum': None,
                    'source': 'microsoft_office'
                }
            
            # 查找具体版本号
            for pattern in version_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    version = match.group(1) if match.groups() else match.group(0)
                    return {
                        'success': True,
                        'version': version,
                        'download_url': url,
                        'release_date': None,
                        'file_size': None,
                        'checksum': None,
                        'source': 'microsoft_office'
                    }
            
            return {
                'success': False,
                'error': '未找到Office版本信息'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _detect_vs_version(self, url: str, web_scraper) -> Dict:
        """检测Visual Studio版本"""
        try:
            soup = web_scraper.get_soup(url)
            if not soup:
                return {
                    'success': False,
                    'error': '无法获取Visual Studio页面'
                }
            
            # Visual Studio版本模式
            version_patterns = [
                r'Visual\s+Studio\s+(\d{4})',  # Visual Studio 2022
                r'VS\s+(\d{4})',               # VS 2022
                r'版本\s+(\d+\.\d+\.\d+)',      # 版本 17.0.0
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
                        'source': 'microsoft_vs'
                    }
            
            return {
                'success': False,
                'error': '未找到Visual Studio版本信息'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _detect_generic_microsoft(self, url: str, web_scraper) -> Dict:
        """检测通用Microsoft产品版本"""
        try:
            soup = web_scraper.get_soup(url)
            if not soup:
                return {
                    'success': False,
                    'error': '无法获取Microsoft页面'
                }
            
            # 通用版本模式
            version_patterns = [
                r'(\d+\.\d+\.\d+\.\d+)',  # 完整版本号
                r'(\d+\.\d+\.\d+)',       # 三段版本号
                r'(\d{4})',               # 年份版本
                r'版本\s+(\d+\.\d+)',      # 中文版本
            ]
            
            page_text = soup.get_text()
            
            for pattern in version_patterns:
                matches = re.findall(pattern, page_text)
                if matches:
                    # 选择最可能的版本号（最长的）
                    version = max(matches, key=len)
                    return {
                        'success': True,
                        'version': version,
                        'download_url': url,
                        'release_date': None,
                        'file_size': None,
                        'checksum': None,
                        'source': 'microsoft_generic'
                    }
            
            return {
                'success': False,
                'error': '未找到Microsoft产品版本信息'
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
                'name': 'Microsoft Office',
                'url': 'https://www.microsoft.com/microsoft-365',
                'description': 'Microsoft Office办公套件'
            },
            {
                'name': 'Visual Studio',
                'url': 'https://visualstudio.microsoft.com/',
                'description': 'Visual Studio开发环境'
            },
            {
                'name': 'Visual Studio Code',
                'url': 'https://code.visualstudio.com',
                'description': 'Visual Studio Code编辑器'
            }
        ]