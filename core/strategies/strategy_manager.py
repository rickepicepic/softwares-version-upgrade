#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
策略管理器 - 负责选择和管理各种检测策略
"""

import re
import logging
from typing import Dict, List, Optional
from urllib.parse import urlparse

from .base_strategy import BaseStrategy
from .github_strategy import GitHubStrategy
from .chrome_strategy import ChromeStrategy
from .microsoft_strategy import MicrosoftStrategy
from .adobe_strategy import AdobeStrategy
from .jetbrains_strategy import JetBrainsStrategy
from .vscode_strategy import VSCodeStrategy
from .zoom_strategy import ZoomStrategy
from .firefox_strategy import FirefoxStrategy
from .generic_strategy import GenericStrategy
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from utils.logger import get_logger


class StrategyManager:
    """策略管理器"""
    
    def __init__(self, config: Dict = None):
        """
        初始化策略管理器
        
        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.logger = get_logger(__name__)
        self.strategies: List[BaseStrategy] = []
        self.custom_strategies: Dict[str, BaseStrategy] = {}
        
        # 初始化内置策略
        self._initialize_builtin_strategies()
        
        # 加载自定义策略配置
        self._load_custom_strategies()
        
        self.logger.info(f"策略管理器初始化完成，共加载 {len(self.strategies)} 个策略")
    
    def _initialize_builtin_strategies(self):
        """初始化内置策略"""
        builtin_strategies = [
            GitHubStrategy(),
            ChromeStrategy(),
            MicrosoftStrategy(),
            AdobeStrategy(),
            JetBrainsStrategy(),
            VSCodeStrategy(),
            ZoomStrategy(),
            FirefoxStrategy(),
            GenericStrategy()  # 通用策略放在最后
        ]
        
        for strategy in builtin_strategies:
            self.strategies.append(strategy)
            self.logger.debug(f"加载内置策略: {strategy.name}")
    
    def _load_custom_strategies(self):
        """加载自定义策略配置"""
        custom_config = self.config.get('custom_strategies', {})
        
        for name, config in custom_config.items():
            try:
                # 动态加载自定义策略
                module_path = config.get('module')
                class_name = config.get('class')
                
                if module_path and class_name:
                    module = __import__(module_path, fromlist=[class_name])
                    strategy_class = getattr(module, class_name)
                    strategy = strategy_class(name, config.get('params', {}))
                    
                    self.register_strategy(name, strategy)
                    self.logger.info(f"加载自定义策略: {name}")
                    
            except Exception as e:
                self.logger.error(f"加载自定义策略失败 {name}: {str(e)}")
    
    def select_strategy(self, software_info) -> BaseStrategy:
        """
        选择最适合的策略
        
        Args:
            software_info: 软件信息
            
        Returns:
            BaseStrategy: 选中的策略
        """
        # 如果指定了策略提示，优先使用
        if hasattr(software_info, 'strategy_hint') and software_info.strategy_hint:
            strategy = self.custom_strategies.get(software_info.strategy_hint)
            if strategy and strategy.can_handle(software_info):
                self.logger.debug(f"使用指定策略: {strategy.name}")
                return strategy
        
        # 找到所有能处理的策略
        capable_strategies = []
        for strategy in self.strategies:
            if strategy.can_handle(software_info):
                priority = strategy.get_priority(software_info)
                capable_strategies.append((strategy, priority))
        
        if not capable_strategies:
            # 如果没有策略能处理，使用通用策略
            generic_strategy = next((s for s in self.strategies if s.name == 'generic'), None)
            if generic_strategy:
                self.logger.warning(f"没有专用策略，使用通用策略: {software_info.name}")
                return generic_strategy
            else:
                raise Exception(f"没有可用的策略处理: {software_info.name}")
        
        # 按优先级排序，选择优先级最高的策略
        capable_strategies.sort(key=lambda x: x[1], reverse=True)
        selected_strategy = capable_strategies[0][0]
        
        self.logger.debug(f"选择策略: {selected_strategy.name} for {software_info.name}")
        return selected_strategy
    
    def register_strategy(self, name: str, strategy: BaseStrategy):
        """
        注册自定义策略
        
        Args:
            name: 策略名称
            strategy: 策略实例
        """
        self.custom_strategies[name] = strategy
        
        # 如果不在主策略列表中，添加进去
        if strategy not in self.strategies:
            # 插入到通用策略之前
            generic_index = next((i for i, s in enumerate(self.strategies) if s.name == 'generic'), len(self.strategies))
            self.strategies.insert(generic_index, strategy)
        
        self.logger.info(f"注册策略: {name}")
    
    def get_strategy_by_name(self, name: str) -> Optional[BaseStrategy]:
        """
        根据名称获取策略
        
        Args:
            name: 策略名称
            
        Returns:
            Optional[BaseStrategy]: 策略实例
        """
        # 先查找自定义策略
        if name in self.custom_strategies:
            return self.custom_strategies[name]
        
        # 再查找内置策略
        for strategy in self.strategies:
            if strategy.name == name:
                return strategy
        
        return None
    
    def get_supported_software(self) -> List[Dict]:
        """
        获取所有策略支持的软件列表
        
        Returns:
            List[Dict]: 支持的软件信息
        """
        supported_software = []
        
        for strategy in self.strategies:
            if hasattr(strategy, 'get_supported_software'):
                software_list = strategy.get_supported_software()
                for software in software_list:
                    software['strategy'] = strategy.name
                    supported_software.append(software)
        
        return supported_software
    
    def get_stats(self) -> Dict:
        """
        获取所有策略的统计信息
        
        Returns:
            Dict: 统计信息
        """
        stats = {
            'total_strategies': len(self.strategies),
            'custom_strategies': len(self.custom_strategies),
            'strategy_details': []
        }
        
        for strategy in self.strategies:
            stats['strategy_details'].append(strategy.get_stats())
        
        return stats
    
    def test_strategy(self, strategy_name: str, software_info) -> Dict:
        """
        测试特定策略
        
        Args:
            strategy_name: 策略名称
            software_info: 软件信息
            
        Returns:
            Dict: 测试结果
        """
        strategy = self.get_strategy_by_name(strategy_name)
        if not strategy:
            return {
                'success': False,
                'error': f'策略不存在: {strategy_name}'
            }
        
        try:
            can_handle = strategy.can_handle(software_info)
            if not can_handle:
                return {
                    'success': False,
                    'error': f'策略无法处理该软件: {software_info.name}'
                }
            
            # 这里需要传入适配器，但在测试模式下可以传入模拟对象
            result = {
                'success': True,
                'strategy': strategy_name,
                'can_handle': can_handle,
                'priority': strategy.get_priority(software_info)
            }
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }


class StrategySelector:
    """策略选择器 - 提供更高级的策略选择逻辑"""
    
    def __init__(self, strategy_manager: StrategyManager):
        self.strategy_manager = strategy_manager
        self.logger = get_logger(__name__)
        
        # 域名到策略的映射
        self.domain_mappings = {
            'github.com': 'github',
            'google.com': 'chrome',
            'microsoft.com': 'microsoft',
            'office.com': 'microsoft',
            'adobe.com': 'adobe',
            'jetbrains.com': 'jetbrains',
            'code.visualstudio.com': 'vscode',
            'zoom.us': 'zoom',
            'mozilla.org': 'firefox',
        }
        
        # 软件名称到策略的映射
        self.name_mappings = {
            'chrome': 'chrome',
            'firefox': 'firefox',
            'vscode': 'vscode',
            'visual studio code': 'vscode',
            'zoom': 'zoom',
            'photoshop': 'adobe',
            'illustrator': 'adobe',
            'pycharm': 'jetbrains',
            'intellij': 'jetbrains',
            'office': 'microsoft',
            'word': 'microsoft',
            'excel': 'microsoft',
        }
    
    def auto_select_strategy(self, software_info) -> Optional[str]:
        """
        自动选择策略
        
        Args:
            software_info: 软件信息
            
        Returns:
            Optional[str]: 策略名称
        """
        # 1. 检查域名映射
        try:
            domain = urlparse(software_info.url).netloc.lower()
            for domain_pattern, strategy_name in self.domain_mappings.items():
                if domain_pattern in domain:
                    self.logger.debug(f"根据域名选择策略: {domain} -> {strategy_name}")
                    return strategy_name
        except Exception as e:
            self.logger.warning(f"解析URL失败: {software_info.url} - {str(e)}")
        
        # 2. 检查软件名称映射
        software_name_lower = software_info.name.lower()
        for name_pattern, strategy_name in self.name_mappings.items():
            if name_pattern in software_name_lower:
                self.logger.debug(f"根据软件名称选择策略: {software_info.name} -> {strategy_name}")
                return strategy_name
        
        # 3. 使用机器学习模型预测（可选）
        # predicted_strategy = self._ml_predict_strategy(software_info)
        # if predicted_strategy:
        #     return predicted_strategy
        
        return None
    
    def _ml_predict_strategy(self, software_info) -> Optional[str]:
        """
        使用机器学习模型预测策略（占位符）
        
        Args:
            software_info: 软件信息
            
        Returns:
            Optional[str]: 预测的策略名称
        """
        # TODO: 实现机器学习策略预测
        # 可以基于历史成功率、软件特征等进行预测
        return None