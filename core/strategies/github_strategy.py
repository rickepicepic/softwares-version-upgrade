#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GitHub策略 - 专门处理GitHub项目的版本检测
"""

import re
import json
from typing import Dict, List
from urllib.parse import urlparse, urljoin
from datetime import datetime

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from core.strategies.base_strategy import BaseStrategy


class GitHubStrategy(BaseStrategy):
    """GitHub项目版本检测策略"""
    
    def __init__(self):
        super().__init__("github")
        self.api_base = "https://api.github.com"
        self.supported_patterns = [
            r'github\.com/([^/]+)/([^/]+)',
            r'github\.io'
        ]
    
    def can_handle(self, software_info) -> bool:
        """判断是否为GitHub项目"""
        url = software_info.url.lower()
        
        # 检查是否包含github.com
        if 'github.com' in url:
            return True
        
        # 检查是否为github.io域名
        if 'github.io' in url:
            return True
        
        return False
    
    def get_priority(self, software_info) -> int:
        """GitHub策略优先级较高"""
        if 'github.com' in software_info.url.lower():
            return 90
        elif 'github.io' in software_info.url.lower():
            return 70
        return 0
    
    def detect(self, software_info, adapters: Dict) -> Dict:
        """检测GitHub项目版本"""
        try:
            # 解析GitHub仓库信息
            repo_info = self._parse_github_url(software_info.url)
            if not repo_info:
                return {
                    'success': False,
                    'error': '无法解析GitHub URL'
                }
            
            # 优先使用API方式
            api_result = self._detect_via_api(repo_info, adapters['api_client'])
            if api_result['success']:
                self.record_success()
                return api_result
            
            # API失败时使用网页爬取
            web_result = self._detect_via_web(repo_info, software_info.url, adapters['web_scraper'])
            if web_result['success']:
                self.record_success()
                return web_result
            
            self.record_failure()
            return {
                'success': False,
                'error': 'API和网页爬取都失败'
            }
            
        except Exception as e:
            self.record_failure()
            self.logger.error(f"GitHub策略检测失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _parse_github_url(self, url: str) -> Dict:
        """解析GitHub URL获取仓库信息"""
        try:
            # 标准化URL
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            parsed = urlparse(url)
            
            # 处理github.com URL
            if 'github.com' in parsed.netloc:
                path_parts = parsed.path.strip('/').split('/')
                if len(path_parts) >= 2:
                    return {
                        'owner': path_parts[0],
                        'repo': path_parts[1],
                        'type': 'repository'
                    }
            
            # 处理github.io URL
            elif 'github.io' in parsed.netloc:
                # 从域名提取用户名
                subdomain = parsed.netloc.split('.')[0]
                return {
                    'owner': subdomain,
                    'repo': subdomain + '.github.io',
                    'type': 'pages'
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"解析GitHub URL失败: {str(e)}")
            return None
    
    def _detect_via_api(self, repo_info: Dict, api_client) -> Dict:
        """通过GitHub API检测版本"""
        try:
            # 构建API URL
            api_url = f"{self.api_base}/repos/{repo_info['owner']}/{repo_info['repo']}/releases/latest"
            
            # 发送API请求
            response = api_client.get(api_url, headers={
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'MacSoftwareVersionTracker/1.0'
            })
            
            if response.status_code == 200:
                data = response.json()
                
                # 解析版本信息
                version = self._extract_version_from_tag(data.get('tag_name', ''))
                download_url = self._find_mac_download_url(data.get('assets', []))
                
                # 解析发布日期
                release_date = None
                if data.get('published_at'):
                    release_date = datetime.fromisoformat(data['published_at'].replace('Z', '+00:00'))
                
                return {
                    'success': True,
                    'version': version,
                    'download_url': download_url or data.get('html_url'),
                    'release_date': release_date,
                    'file_size': self._get_asset_size(data.get('assets', [])),
                    'checksum': None,  # GitHub API不直接提供
                    'source': 'github_api'
                }
            
            elif response.status_code == 404:
                # 没有releases，尝试获取tags
                return self._detect_via_tags_api(repo_info, api_client)
            
            else:
                return {
                    'success': False,
                    'error': f'GitHub API请求失败: {response.status_code}'
                }
                
        except Exception as e:
            self.logger.error(f"GitHub API检测失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _detect_via_tags_api(self, repo_info: Dict, api_client) -> Dict:
        """通过GitHub Tags API检测版本"""
        try:
            api_url = f"{self.api_base}/repos/{repo_info['owner']}/{repo_info['repo']}/tags"
            
            response = api_client.get(api_url, headers={
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'MacSoftwareVersionTracker/1.0'
            })
            
            if response.status_code == 200:
                tags = response.json()
                if tags:
                    # 获取最新的tag
                    latest_tag = tags[0]
                    version = self._extract_version_from_tag(latest_tag.get('name', ''))
                    
                    return {
                        'success': True,
                        'version': version,
                        'download_url': f"https://github.com/{repo_info['owner']}/{repo_info['repo']}/archive/{latest_tag['name']}.zip",
                        'release_date': None,
                        'file_size': None,
                        'checksum': None,
                        'source': 'github_tags_api'
                    }
            
            return {
                'success': False,
                'error': '没有找到tags'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _detect_via_web(self, repo_info: Dict, original_url: str, web_scraper) -> Dict:
        """通过网页爬取检测版本"""
        try:
            # 构建releases页面URL
            releases_url = f"https://github.com/{repo_info['owner']}/{repo_info['repo']}/releases"
            
            soup = web_scraper.get_soup(releases_url)
            if not soup:
                return {
                    'success': False,
                    'error': '无法获取releases页面'
                }
            
            # 查找最新release
            release_header = soup.find('h1', {'data-test-selector': 'release-header'})
            if not release_header:
                # 尝试其他选择器
                release_header = soup.find('h2', class_='sr-only')
                if not release_header:
                    return {
                        'success': False,
                        'error': '无法找到release信息'
                    }
            
            # 提取版本号
            version_text = release_header.get_text().strip()
            version = self._extract_version_from_tag(version_text)
            
            # 查找下载链接
            download_url = self._find_download_link_in_page(soup, repo_info)
            
            return {
                'success': True,
                'version': version,
                'download_url': download_url or releases_url,
                'release_date': None,
                'file_size': None,
                'checksum': None,
                'source': 'github_web'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _extract_version_from_tag(self, tag_name: str) -> str:
        """从tag名称中提取版本号"""
        if not tag_name:
            return "未知版本"
        
        # 移除常见前缀
        tag_name = re.sub(r'^(v|version|release|r)', '', tag_name, flags=re.IGNORECASE)
        
        # 匹配版本号模式
        version_patterns = [
            r'(\d+\.\d+\.\d+(?:\.\d+)?)',  # 标准版本号
            r'(\d+\.\d+)',                 # 简化版本号
            r'(\d{4}\.\d+\.\d+)',         # 年份版本
            r'(\d+)',                      # 纯数字版本
        ]
        
        for pattern in version_patterns:
            match = re.search(pattern, tag_name)
            if match:
                return match.group(1)
        
        # 如果没有匹配到标准格式，返回原始tag名
        return tag_name.strip()
    
    def _find_mac_download_url(self, assets: List[Dict]) -> str:
        """从assets中查找Mac下载链接"""
        mac_keywords = ['mac', 'macos', 'darwin', 'osx', '.dmg', '.pkg']
        
        for asset in assets:
            name = asset.get('name', '').lower()
            if any(keyword in name for keyword in mac_keywords):
                return asset.get('browser_download_url')
        
        # 如果没有找到Mac专用的，返回第一个asset
        if assets:
            return assets[0].get('browser_download_url')
        
        return None
    
    def _get_asset_size(self, assets: List[Dict]) -> str:
        """获取资源文件大小"""
        for asset in assets:
            name = asset.get('name', '').lower()
            if any(keyword in name for keyword in ['mac', 'macos', 'darwin', '.dmg', '.pkg']):
                size = asset.get('size', 0)
                if size > 0:
                    return self._format_file_size(size)
        
        return None
    
    def _format_file_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def _find_download_link_in_page(self, soup, repo_info: Dict) -> str:
        """在页面中查找下载链接"""
        # 查找asset链接
        asset_links = soup.find_all('a', href=re.compile(r'/releases/download/'))
        
        for link in asset_links:
            href = link.get('href', '')
            if any(keyword in href.lower() for keyword in ['.dmg', '.pkg', 'mac', 'macos']):
                return urljoin('https://github.com', href)
        
        # 如果没有找到asset，返回源码下载链接
        if asset_links:
            return urljoin('https://github.com', asset_links[0].get('href', ''))
        
        return None
    
    def get_supported_software(self) -> List[Dict]:
        """获取支持的软件列表"""
        return [
            {
                'name': 'VS Code',
                'url': 'https://github.com/microsoft/vscode',
                'description': 'Visual Studio Code编辑器'
            },
            {
                'name': 'Atom',
                'url': 'https://github.com/atom/atom',
                'description': 'Atom编辑器'
            },
            {
                'name': 'Homebrew',
                'url': 'https://github.com/Homebrew/brew',
                'description': 'macOS包管理器'
            },
            {
                'name': 'Docker Desktop',
                'url': 'https://github.com/docker/desktop',
                'description': 'Docker桌面版'
            }
        ]