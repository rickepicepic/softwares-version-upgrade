#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
软件版本检测器核心模块
提供统一的版本检测接口和策略管理
"""

import asyncio
import logging
from typing import List, Dict, Optional, Union
from dataclasses import dataclass
from datetime import datetime
import concurrent.futures
from urllib.parse import urlparse

from .strategies.strategy_manager import StrategyManager
from .parsers.version_parser import VersionParser
from ..adapters.web_scraper import WebScraper
from ..adapters.api_client import APIClient
from ..adapters.selenium_driver import SeleniumDriver
from ..services.cache_service import CacheService
from ..services.notification_service import NotificationService
from ..utils.logger import get_logger
from ..utils.validators import validate_software_info


@dataclass
class SoftwareInfo:
    """软件信息数据类"""
    name: str
    url: str
    strategy_hint: Optional[str] = None
    metadata: Optional[Dict] = None


@dataclass
class DetectionResult:
    """检测结果数据类"""
    name: str
    version: Optional[str]
    download_url: Optional[str]
    release_date: Optional[datetime]
    file_size: Optional[str]
    checksum: Optional[str]
    success: bool
    error_message: Optional[str] = None
    detection_time: datetime = None
    strategy_used: Optional[str] = None
    
    def __post_init__(self):
        if self.detection_time is None:
            self.detection_time = datetime.now()


class SoftwareVersionDetector:
    """软件版本检测器主类"""
    
    def __init__(self, config: Dict = None):
        """
        初始化检测器
        
        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.logger = get_logger(__name__)
        
        # 初始化组件
        self.strategy_manager = StrategyManager(self.config.get('strategies', {}))
        self.version_parser = VersionParser(self.config.get('version_patterns', []))
        self.cache_service = CacheService(self.config.get('cache', {}))
        self.notification_service = NotificationService(self.config.get('notifications', {}))
        
        # 初始化适配器
        self.web_scraper = WebScraper(self.config.get('scraper', {}))
        self.api_client = APIClient(self.config.get('api', {}))
        self.selenium_driver = SeleniumDriver(self.config.get('selenium', {}))
        
        # 性能配置
        self.max_workers = self.config.get('max_workers', 10)
        self.timeout = self.config.get('timeout', 30)
        self.max_retries = self.config.get('max_retries', 3)
        
        self.logger.info("软件版本检测器初始化完成")
    
    def detect_version(self, software_info: Union[SoftwareInfo, Dict]) -> DetectionResult:
        """
        检测单个软件版本
        
        Args:
            software_info: 软件信息
            
        Returns:
            DetectionResult: 检测结果
        """
        # 数据验证和转换
        if isinstance(software_info, dict):
            software_info = SoftwareInfo(**software_info)
        
        if not validate_software_info(software_info):
            return DetectionResult(
                name=software_info.name,
                version=None,
                download_url=None,
                release_date=None,
                file_size=None,
                checksum=None,
                success=False,
                error_message="无效的软件信息"
            )
        
        self.logger.info(f"开始检测软件版本: {software_info.name}")
        
        # 检查缓存
        cache_key = f"version:{software_info.name}:{hash(software_info.url)}"
        cached_result = self.cache_service.get(cache_key)
        if cached_result:
            self.logger.info(f"从缓存获取结果: {software_info.name}")
            return cached_result
        
        # 执行检测
        result = self._execute_detection(software_info)
        
        # 缓存结果
        if result.success:
            self.cache_service.set(cache_key, result)
        
        # 发送通知
        if result.success:
            self.notification_service.notify_version_detected(result)
        else:
            self.notification_service.notify_detection_failed(result)
        
        self.logger.info(f"检测完成: {software_info.name} - {result.version if result.success else '失败'}")
        return result
    
    def batch_detect(self, software_list: List[Union[SoftwareInfo, Dict]], 
                    concurrent: bool = True) -> List[DetectionResult]:
        """
        批量检测软件版本
        
        Args:
            software_list: 软件信息列表
            concurrent: 是否并发执行
            
        Returns:
            List[DetectionResult]: 检测结果列表
        """
        self.logger.info(f"开始批量检测 {len(software_list)} 个软件")
        
        if not concurrent:
            # 串行执行
            results = []
            for software_info in software_list:
                result = self.detect_version(software_info)
                results.append(result)
            return results
        
        # 并发执行
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_software = {
                executor.submit(self.detect_version, software_info): software_info
                for software_info in software_list
            }
            
            results = []
            for future in concurrent.futures.as_completed(future_to_software):
                try:
                    result = future.result(timeout=self.timeout)
                    results.append(result)
                except Exception as e:
                    software_info = future_to_software[future]
                    name = software_info.name if hasattr(software_info, 'name') else software_info.get('name', 'Unknown')
                    self.logger.error(f"检测失败: {name} - {str(e)}")
                    results.append(DetectionResult(
                        name=name,
                        version=None,
                        download_url=None,
                        release_date=None,
                        file_size=None,
                        checksum=None,
                        success=False,
                        error_message=str(e)
                    ))
        
        success_count = sum(1 for r in results if r.success)
        self.logger.info(f"批量检测完成: {success_count}/{len(results)} 成功")
        return results
    
    async def async_detect_version(self, software_info: Union[SoftwareInfo, Dict]) -> DetectionResult:
        """
        异步检测单个软件版本
        
        Args:
            software_info: 软件信息
            
        Returns:
            DetectionResult: 检测结果
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.detect_version, software_info)
    
    async def async_batch_detect(self, software_list: List[Union[SoftwareInfo, Dict]]) -> List[DetectionResult]:
        """
        异步批量检测软件版本
        
        Args:
            software_list: 软件信息列表
            
        Returns:
            List[DetectionResult]: 检测结果列表
        """
        tasks = [self.async_detect_version(software_info) for software_info in software_list]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                software_info = software_list[i]
                name = software_info.name if hasattr(software_info, 'name') else software_info.get('name', 'Unknown')
                processed_results.append(DetectionResult(
                    name=name,
                    version=None,
                    download_url=None,
                    release_date=None,
                    file_size=None,
                    checksum=None,
                    success=False,
                    error_message=str(result)
                ))
            else:
                processed_results.append(result)
        
        return processed_results
    
    def _execute_detection(self, software_info: SoftwareInfo) -> DetectionResult:
        """
        执行具体的检测逻辑
        
        Args:
            software_info: 软件信息
            
        Returns:
            DetectionResult: 检测结果
        """
        for attempt in range(self.max_retries):
            try:
                # 选择检测策略
                strategy = self.strategy_manager.select_strategy(software_info)
                self.logger.debug(f"使用策略: {strategy.name} for {software_info.name}")
                
                # 执行检测
                raw_result = strategy.detect(software_info, {
                    'web_scraper': self.web_scraper,
                    'api_client': self.api_client,
                    'selenium_driver': self.selenium_driver,
                    'version_parser': self.version_parser
                })
                
                # 解析结果
                if raw_result and raw_result.get('success'):
                    return DetectionResult(
                        name=software_info.name,
                        version=raw_result.get('version'),
                        download_url=raw_result.get('download_url'),
                        release_date=raw_result.get('release_date'),
                        file_size=raw_result.get('file_size'),
                        checksum=raw_result.get('checksum'),
                        success=True,
                        strategy_used=strategy.name
                    )
                else:
                    error_msg = raw_result.get('error', '检测失败') if raw_result else '无返回结果'
                    if attempt < self.max_retries - 1:
                        self.logger.warning(f"检测失败，尝试重试 ({attempt + 1}/{self.max_retries}): {error_msg}")
                        continue
                    else:
                        return DetectionResult(
                            name=software_info.name,
                            version=None,
                            download_url=None,
                            release_date=None,
                            file_size=None,
                            checksum=None,
                            success=False,
                            error_message=error_msg,
                            strategy_used=strategy.name
                        )
                        
            except Exception as e:
                error_msg = str(e)
                if attempt < self.max_retries - 1:
                    self.logger.warning(f"检测异常，尝试重试 ({attempt + 1}/{self.max_retries}): {error_msg}")
                    continue
                else:
                    self.logger.error(f"检测失败: {software_info.name} - {error_msg}")
                    return DetectionResult(
                        name=software_info.name,
                        version=None,
                        download_url=None,
                        release_date=None,
                        file_size=None,
                        checksum=None,
                        success=False,
                        error_message=error_msg
                    )
        
        # 不应该到达这里
        return DetectionResult(
            name=software_info.name,
            version=None,
            download_url=None,
            release_date=None,
            file_size=None,
            checksum=None,
            success=False,
            error_message="未知错误"
        )
    
    def get_supported_software(self) -> List[Dict]:
        """
        获取支持的软件列表
        
        Returns:
            List[Dict]: 支持的软件信息列表
        """
        return self.strategy_manager.get_supported_software()
    
    def register_strategy(self, name: str, strategy):
        """
        注册自定义策略
        
        Args:
            name: 策略名称
            strategy: 策略实例
        """
        self.strategy_manager.register_strategy(name, strategy)
        self.logger.info(f"注册自定义策略: {name}")
    
    def configure_notification(self, config: Dict):
        """
        配置通知服务
        
        Args:
            config: 通知配置
        """
        self.notification_service.configure(config)
    
    def get_statistics(self) -> Dict:
        """
        获取检测统计信息
        
        Returns:
            Dict: 统计信息
        """
        return {
            'cache_stats': self.cache_service.get_stats(),
            'strategy_stats': self.strategy_manager.get_stats(),
            'notification_stats': self.notification_service.get_stats()
        }