#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
日志管理模块
"""

import os
import logging
import logging.handlers
from typing import Optional


def setup_logging(level: str = 'INFO', 
                 log_file: str = None,
                 format_string: str = None,
                 max_size: str = '10MB',
                 backup_count: int = 5):
    """
    设置全局日志配置
    
    Args:
        level: 日志级别
        log_file: 日志文件路径
        format_string: 日志格式
        max_size: 日志文件最大大小
        backup_count: 备份文件数量
    """
    # 创建日志目录
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
    
    # 设置日志级别
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # 设置日志格式
    if not format_string:
        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    formatter = logging.Formatter(format_string)
    
    # 获取根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # 清除现有的处理器
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # 文件处理器（如果指定了日志文件）
    if log_file:
        # 解析文件大小
        max_bytes = _parse_size(max_size)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """
    获取指定名称的日志器
    
    Args:
        name: 日志器名称
        
    Returns:
        logging.Logger: 日志器实例
    """
    return logging.getLogger(name)


def _parse_size(size_str: str) -> int:
    """
    解析大小字符串为字节数
    
    Args:
        size_str: 大小字符串，如 "10MB", "1GB"
        
    Returns:
        int: 字节数
    """
    size_str = size_str.upper().strip()
    
    if size_str.endswith('KB'):
        return int(size_str[:-2]) * 1024
    elif size_str.endswith('MB'):
        return int(size_str[:-2]) * 1024 * 1024
    elif size_str.endswith('GB'):
        return int(size_str[:-2]) * 1024 * 1024 * 1024
    else:
        # 假设是字节数
        return int(size_str)


class StructuredLogger:
    """结构化日志器"""
    
    def __init__(self, name: str):
        self.logger = get_logger(name)
        self.name = name
    
    def info(self, message: str, **kwargs):
        """记录信息日志"""
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """记录警告日志"""
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """记录错误日志"""
        self._log(logging.ERROR, message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """记录调试日志"""
        self._log(logging.DEBUG, message, **kwargs)
    
    def _log(self, level: int, message: str, **kwargs):
        """内部日志记录方法"""
        if kwargs:
            # 构建结构化消息
            extra_info = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
            full_message = f"{message} | {extra_info}"
        else:
            full_message = message
        
        self.logger.log(level, full_message)


# 预定义的日志器
app_logger = StructuredLogger('app')
detector_logger = StructuredLogger('detector')
strategy_logger = StructuredLogger('strategy')
api_logger = StructuredLogger('api')