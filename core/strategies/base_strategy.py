#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
策略基类
"""

from abc import ABC, abstractmethod
from typing import Dict

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from utils.logger import get_logger


class BaseStrategy(ABC):
    """策略基类"""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = get_logger(f"strategy.{name}")
        self.success_count = 0
        self.failure_count = 0
    
    @abstractmethod
    def can_handle(self, software_info) -> bool:
        """
        判断是否能处理该软件
        
        Args:
            software_info: 软件信息
            
        Returns:
            bool: 是否能处理
        """
        pass
    
    @abstractmethod
    def detect(self, software_info, adapters: Dict) -> Dict:
        """
        执行版本检测
        
        Args:
            software_info: 软件信息
            adapters: 适配器字典
            
        Returns:
            Dict: 检测结果
        """
        pass
    
    def get_priority(self, software_info) -> int:
        """
        获取策略优先级（数字越大优先级越高）
        
        Args:
            software_info: 软件信息
            
        Returns:
            int: 优先级
        """
        return 0
    
    def record_success(self):
        """记录成功"""
        self.success_count += 1
    
    def record_failure(self):
        """记录失败"""
        self.failure_count += 1
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        total = self.success_count + self.failure_count
        success_rate = (self.success_count / total * 100) if total > 0 else 0
        
        return {
            'name': self.name,
            'success_count': self.success_count,
            'failure_count': self.failure_count,
            'success_rate': round(success_rate, 2)
        }