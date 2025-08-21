#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据验证模块
"""

import re
from typing import Optional
from urllib.parse import urlparse


def validate_software_info(software_info) -> bool:
    """
    验证软件信息是否有效
    
    Args:
        software_info: 软件信息对象
        
    Returns:
        bool: 是否有效
    """
    # 检查必要字段
    if not hasattr(software_info, 'name') or not software_info.name:
        return False
    
    if not hasattr(software_info, 'url') or not software_info.url:
        return False
    
    # 验证软件名称
    if not validate_software_name(software_info.name):
        return False
    
    # 验证URL
    if not validate_url(software_info.url):
        return False
    
    return True


def validate_software_name(name: str) -> bool:
    """
    验证软件名称
    
    Args:
        name: 软件名称
        
    Returns:
        bool: 是否有效
    """
    if not name or not isinstance(name, str):
        return False
    
    # 去除空白字符
    name = name.strip()
    
    # 检查长度
    if len(name) < 1 or len(name) > 100:
        return False
    
    # 检查是否包含有效字符
    if not re.match(r'^[a-zA-Z0-9\s\-_\.\+\(\)]+$', name):
        return False
    
    return True


def validate_url(url: str) -> bool:
    """
    验证URL格式
    
    Args:
        url: URL字符串
        
    Returns:
        bool: 是否有效
    """
    if not url or not isinstance(url, str):
        return False
    
    try:
        # 如果没有协议，添加https
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        parsed = urlparse(url)
        
        # 检查基本组件
        if not parsed.netloc:
            return False
        
        # 检查域名格式
        if not re.match(r'^[a-zA-Z0-9\-\.]+$', parsed.netloc):
            return False
        
        return True
        
    except Exception:
        return False


def validate_version(version: str) -> bool:
    """
    验证版本号格式
    
    Args:
        version: 版本号字符串
        
    Returns:
        bool: 是否有效
    """
    if not version or not isinstance(version, str):
        return False
    
    # 常见版本号格式
    version_patterns = [
        r'^\d+\.\d+\.\d+(\.\d+)?$',  # 1.2.3 或 1.2.3.4
        r'^\d{4}\.\d+\.\d+$',        # 2024.1.0
        r'^v?\d+\.\d+$',             # v1.2 或 1.2
        r'^\d+$',                    # 纯数字
    ]
    
    for pattern in version_patterns:
        if re.match(pattern, version.strip()):
            return True
    
    return False


def validate_email(email: str) -> bool:
    """
    验证邮箱格式
    
    Args:
        email: 邮箱地址
        
    Returns:
        bool: 是否有效
    """
    if not email or not isinstance(email, str):
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def sanitize_filename(filename: str) -> str:
    """
    清理文件名，移除不安全字符
    
    Args:
        filename: 原始文件名
        
    Returns:
        str: 清理后的文件名
    """
    if not filename:
        return "unnamed"
    
    # 移除不安全字符
    safe_filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # 移除控制字符
    safe_filename = re.sub(r'[\x00-\x1f\x7f]', '', safe_filename)
    
    # 限制长度
    if len(safe_filename) > 255:
        safe_filename = safe_filename[:255]
    
    # 确保不为空
    if not safe_filename.strip():
        safe_filename = "unnamed"
    
    return safe_filename.strip()


def validate_config(config: dict) -> tuple[bool, Optional[str]]:
    """
    验证配置字典
    
    Args:
        config: 配置字典
        
    Returns:
        tuple[bool, Optional[str]]: (是否有效, 错误信息)
    """
    try:
        # 检查必要的配置项
        required_sections = ['detector', 'scraper', 'api']
        
        for section in required_sections:
            if section not in config:
                return False, f"缺少必要的配置节: {section}"
        
        # 检查API配置
        api_config = config.get('api', {})
        if 'port' in api_config:
            port = api_config['port']
            if not isinstance(port, int) or port < 1 or port > 65535:
                return False, f"无效的端口号: {port}"
        
        # 检查超时配置
        for section in ['detector', 'scraper']:
            section_config = config.get(section, {})
            if 'timeout' in section_config:
                timeout = section_config['timeout']
                if not isinstance(timeout, (int, float)) or timeout <= 0:
                    return False, f"无效的超时设置 {section}.timeout: {timeout}"
        
        return True, None
        
    except Exception as e:
        return False, f"配置验证异常: {str(e)}"