#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
版本号解析器 - 提供统一的版本号解析和比较功能
"""

import re
from typing import List, Optional, Tuple
from dataclasses import dataclass

from ...utils.logger import get_logger


@dataclass
class VersionInfo:
    """版本信息数据类"""
    raw: str  # 原始版本字符串
    major: int = 0
    minor: int = 0
    patch: int = 0
    build: int = 0
    pre_release: str = ""
    metadata: str = ""
    
    def __str__(self):
        return self.raw
    
    def to_tuple(self) -> Tuple[int, int, int, int]:
        """转换为元组用于比较"""
        return (self.major, self.minor, self.patch, self.build)


class VersionParser:
    """版本号解析器"""
    
    def __init__(self, custom_patterns: List[str] = None):
        """
        初始化版本解析器
        
        Args:
            custom_patterns: 自定义版本号模式
        """
        self.logger = get_logger(__name__)
        
        # 内置版本号模式
        self.builtin_patterns = [
            # 标准语义化版本 (1.2.3, 1.2.3-alpha.1+build.123)
            r'v?(\d+)\.(\d+)\.(\d+)(?:\.(\d+))?(?:-([a-zA-Z0-9\-\.]+))?(?:\+([a-zA-Z0-9\-\.]+))?',
            
            # 年份版本 (2024.1.0, 2024.03.15)
            r'(\d{4})\.(\d{1,2})\.(\d{1,2})(?:\.(\d+))?',
            
            # 简化版本 (1.2, 2.0)
            r'v?(\d+)\.(\d+)(?:\.(\d+))?(?:\.(\d+))?',
            
            # Build版本 (Build 123, Build 1.2.3)
            r'[Bb]uild\s+(\d+)(?:\.(\d+))?(?:\.(\d+))?(?:\.(\d+))?',
            
            # Release版本 (Release 1.0, R1.2.3)
            r'[Rr]elease\s+(\d+)(?:\.(\d+))?(?:\.(\d+))?(?:\.(\d+))?',
            
            # 版本号前缀 (Version 1.2.3, Ver 1.0)
            r'[Vv]er(?:sion)?\s+(\d+)(?:\.(\d+))?(?:\.(\d+))?(?:\.(\d+))?',
            
            # 纯数字版本 (123, 2024)
            r'^(\d+)$',
            
            # Chrome风格版本 (120.0.6099.109)
            r'(\d+)\.(\d+)\.(\d+)\.(\d+)',
            
            # 日期版本 (20240315, 2024-03-15)
            r'(\d{4})-?(\d{2})-?(\d{2})',
            
            # 特殊格式 (1.0-SNAPSHOT, 2.0.0.RELEASE)
            r'(\d+)\.(\d+)(?:\.(\d+))?(?:\.(\d+))?[-\.]([A-Z]+)',
        ]
        
        # 合并自定义模式
        self.patterns = self.builtin_patterns[:]
        if custom_patterns:
            self.patterns.extend(custom_patterns)
        
        # 编译正则表达式
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.patterns]
        
        self.logger.info(f"版本解析器初始化完成，共 {len(self.patterns)} 个模式")
    
    def parse(self, version_string: str) -> Optional[VersionInfo]:
        """
        解析版本字符串
        
        Args:
            version_string: 版本字符串
            
        Returns:
            Optional[VersionInfo]: 解析后的版本信息
        """
        if not version_string:
            return None
        
        # 清理版本字符串
        cleaned_version = self._clean_version_string(version_string)
        
        # 尝试各种模式
        for pattern in self.compiled_patterns:
            match = pattern.search(cleaned_version)
            if match:
                try:
                    version_info = self._extract_version_info(match, cleaned_version)
                    if version_info:
                        self.logger.debug(f"成功解析版本: {version_string} -> {version_info}")
                        return version_info
                except Exception as e:
                    self.logger.debug(f"解析版本失败: {version_string} - {str(e)}")
                    continue
        
        # 如果所有模式都失败，返回原始字符串
        self.logger.warning(f"无法解析版本号: {version_string}")
        return VersionInfo(raw=cleaned_version)
    
    def _clean_version_string(self, version_string: str) -> str:
        """清理版本字符串"""
        # 移除多余的空白字符
        cleaned = version_string.strip()
        
        # 移除常见的前缀和后缀
        prefixes_to_remove = [
            'version', 'ver', 'v', 'release', 'rel', 'r',
            'build', 'b', '版本', '发布', '构建'
        ]
        
        for prefix in prefixes_to_remove:
            pattern = rf'^{re.escape(prefix)}\s*[:\-]?\s*'
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        # 移除括号内容（如果不包含数字）
        cleaned = re.sub(r'\([^)]*\)', lambda m: m.group() if re.search(r'\d', m.group()) else '', cleaned)
        
        # 移除多余的标点符号
        cleaned = re.sub(r'[^\w\.\-\+]', ' ', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned
    
    def _extract_version_info(self, match, original: str) -> Optional[VersionInfo]:
        """从正则匹配中提取版本信息"""
        groups = match.groups()
        
        # 过滤None值
        groups = [g for g in groups if g is not None]
        
        if not groups:
            return None
        
        version_info = VersionInfo(raw=original)
        
        try:
            # 提取主要版本号组件
            if len(groups) >= 1 and groups[0].isdigit():
                version_info.major = int(groups[0])
            
            if len(groups) >= 2 and groups[1].isdigit():
                version_info.minor = int(groups[1])
            
            if len(groups) >= 3 and groups[2].isdigit():
                version_info.patch = int(groups[2])
            
            if len(groups) >= 4 and groups[3].isdigit():
                version_info.build = int(groups[3])
            
            # 提取预发布信息
            if len(groups) >= 5 and groups[4] and not groups[4].isdigit():
                version_info.pre_release = groups[4]
            
            # 提取元数据
            if len(groups) >= 6 and groups[5]:
                version_info.metadata = groups[5]
            
            return version_info
            
        except (ValueError, IndexError) as e:
            self.logger.debug(f"提取版本信息失败: {str(e)}")
            return None
    
    def compare(self, version1: str, version2: str) -> int:
        """
        比较两个版本号
        
        Args:
            version1: 版本号1
            version2: 版本号2
            
        Returns:
            int: -1 (version1 < version2), 0 (相等), 1 (version1 > version2)
        """
        v1 = self.parse(version1)
        v2 = self.parse(version2)
        
        if not v1 or not v2:
            # 如果无法解析，进行字符串比较
            if version1 < version2:
                return -1
            elif version1 > version2:
                return 1
            else:
                return 0
        
        # 比较版本号组件
        t1 = v1.to_tuple()
        t2 = v2.to_tuple()
        
        if t1 < t2:
            return -1
        elif t1 > t2:
            return 1
        else:
            # 主版本号相同，比较预发布版本
            if v1.pre_release and not v2.pre_release:
                return -1  # 预发布版本小于正式版本
            elif not v1.pre_release and v2.pre_release:
                return 1
            elif v1.pre_release and v2.pre_release:
                if v1.pre_release < v2.pre_release:
                    return -1
                elif v1.pre_release > v2.pre_release:
                    return 1
            
            return 0
    
    def is_newer(self, version1: str, version2: str) -> bool:
        """
        判断version1是否比version2更新
        
        Args:
            version1: 版本号1
            version2: 版本号2
            
        Returns:
            bool: 是否更新
        """
        return self.compare(version1, version2) > 0
    
    def is_valid_version(self, version_string: str) -> bool:
        """
        检查版本字符串是否有效
        
        Args:
            version_string: 版本字符串
            
        Returns:
            bool: 是否有效
        """
        if not version_string:
            return False
        
        version_info = self.parse(version_string)
        return version_info is not None and (
            version_info.major > 0 or 
            version_info.minor > 0 or 
            version_info.patch > 0 or
            version_info.build > 0
        )
    
    def normalize_version(self, version_string: str) -> str:
        """
        标准化版本字符串
        
        Args:
            version_string: 原始版本字符串
            
        Returns:
            str: 标准化后的版本字符串
        """
        version_info = self.parse(version_string)
        if not version_info:
            return version_string
        
        # 构建标准化版本字符串
        parts = [str(version_info.major)]
        
        if version_info.minor > 0 or version_info.patch > 0 or version_info.build > 0:
            parts.append(str(version_info.minor))
        
        if version_info.patch > 0 or version_info.build > 0:
            parts.append(str(version_info.patch))
        
        if version_info.build > 0:
            parts.append(str(version_info.build))
        
        normalized = '.'.join(parts)
        
        # 添加预发布信息
        if version_info.pre_release:
            normalized += f'-{version_info.pre_release}'
        
        # 添加元数据
        if version_info.metadata:
            normalized += f'+{version_info.metadata}'
        
        return normalized
    
    def extract_versions_from_text(self, text: str) -> List[str]:
        """
        从文本中提取所有可能的版本号
        
        Args:
            text: 文本内容
            
        Returns:
            List[str]: 版本号列表
        """
        versions = []
        
        for pattern in self.compiled_patterns:
            matches = pattern.findall(text)
            for match in matches:
                if isinstance(match, tuple):
                    # 重构完整的版本字符串
                    version_parts = [str(part) for part in match if part and str(part).isdigit()]
                    if version_parts:
                        version = '.'.join(version_parts)
                        if self.is_valid_version(version):
                            versions.append(version)
                else:
                    if self.is_valid_version(match):
                        versions.append(match)
        
        # 去重并排序
        unique_versions = list(set(versions))
        unique_versions.sort(key=lambda v: self.parse(v).to_tuple() if self.parse(v) else (0, 0, 0, 0), reverse=True)
        
        return unique_versions
    
    def get_latest_version(self, versions: List[str]) -> Optional[str]:
        """
        从版本列表中获取最新版本
        
        Args:
            versions: 版本列表
            
        Returns:
            Optional[str]: 最新版本
        """
        if not versions:
            return None
        
        if len(versions) == 1:
            return versions[0]
        
        latest = versions[0]
        for version in versions[1:]:
            if self.is_newer(version, latest):
                latest = version
        
        return latest