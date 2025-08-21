#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
版本检测服务 - 提供高级的版本检测和管理功能
"""

import asyncio
import json
from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import asdict
import threading
import schedule
import time

from ..core.detector import SoftwareVersionDetector, SoftwareInfo, DetectionResult
from ..services.cache_service import CacheService
from ..services.notification_service import NotificationService
from ..utils.logger import get_logger


class VersionService:
    """版本检测服务"""
    
    def __init__(self, config: Dict = None):
        """
        初始化版本服务
        
        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.logger = get_logger(__name__)
        
        # 初始化核心组件
        self.detector = SoftwareVersionDetector(self.config.get('detector', {}))
        self.cache_service = CacheService(self.config.get('cache', {}))
        self.notification_service = NotificationService(self.config.get('notifications', {}))
        
        # 服务配置
        self.auto_update_enabled = self.config.get('auto_update', False)
        self.update_interval = self.config.get('update_interval', 3600)  # 1小时
        self.batch_size = self.config.get('batch_size', 50)
        
        # 软件库
        self.software_registry: Dict[str, SoftwareInfo] = {}
        self.version_history: Dict[str, List[DetectionResult]] = {}
        
        # 回调函数
        self.version_update_callbacks: List[Callable] = []
        self.detection_complete_callbacks: List[Callable] = []
        
        # 调度器
        self.scheduler_thread = None
        self.scheduler_running = False
        
        self.logger.info("版本检测服务初始化完成")
    
    def register_software(self, software_info: SoftwareInfo) -> bool:
        """
        注册软件到服务中
        
        Args:
            software_info: 软件信息
            
        Returns:
            bool: 是否成功注册
        """
        try:
            key = self._generate_software_key(software_info)
            self.software_registry[key] = software_info
            
            # 初始化版本历史
            if key not in self.version_history:
                self.version_history[key] = []
            
            self.logger.info(f"注册软件: {software_info.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"注册软件失败: {str(e)}")
            return False
    
    def register_software_batch(self, software_list: List[SoftwareInfo]) -> int:
        """
        批量注册软件
        
        Args:
            software_list: 软件信息列表
            
        Returns:
            int: 成功注册的数量
        """
        success_count = 0
        
        for software_info in software_list:
            if self.register_software(software_info):
                success_count += 1
        
        self.logger.info(f"批量注册完成: {success_count}/{len(software_list)}")
        return success_count
    
    def unregister_software(self, software_name: str) -> bool:
        """
        取消注册软件
        
        Args:
            software_name: 软件名称
            
        Returns:
            bool: 是否成功
        """
        try:
            key = self._find_software_key(software_name)
            if key:
                del self.software_registry[key]
                self.logger.info(f"取消注册软件: {software_name}")
                return True
            else:
                self.logger.warning(f"未找到软件: {software_name}")
                return False
                
        except Exception as e:
            self.logger.error(f"取消注册软件失败: {str(e)}")
            return False
    
    def detect_single_version(self, software_name: str) -> Optional[DetectionResult]:
        """
        检测单个软件版本
        
        Args:
            software_name: 软件名称
            
        Returns:
            Optional[DetectionResult]: 检测结果
        """
        key = self._find_software_key(software_name)
        if not key:
            self.logger.error(f"未找到软件: {software_name}")
            return None
        
        software_info = self.software_registry[key]
        result = self.detector.detect_version(software_info)
        
        # 保存结果到历史记录
        self._save_detection_result(key, result)
        
        # 检查版本更新
        self._check_version_update(key, result)
        
        # 触发回调
        for callback in self.detection_complete_callbacks:
            try:
                callback(result)
            except Exception as e:
                self.logger.error(f"回调函数执行失败: {str(e)}")
        
        return result
    
    def detect_all_versions(self, concurrent: bool = True) -> List[DetectionResult]:
        """
        检测所有注册软件的版本
        
        Args:
            concurrent: 是否并发执行
            
        Returns:
            List[DetectionResult]: 检测结果列表
        """
        self.logger.info(f"开始检测所有软件版本 (共{len(self.software_registry)}个)")
        
        software_list = list(self.software_registry.values())
        results = self.detector.batch_detect(software_list, concurrent=concurrent)
        
        # 保存结果
        for i, result in enumerate(results):
            software_info = software_list[i]
            key = self._generate_software_key(software_info)
            self._save_detection_result(key, result)
            self._check_version_update(key, result)
        
        self.logger.info(f"检测完成: {len(results)}个结果")
        return results
    
    async def detect_all_versions_async(self) -> List[DetectionResult]:
        """
        异步检测所有软件版本
        
        Returns:
            List[DetectionResult]: 检测结果列表
        """
        software_list = list(self.software_registry.values())
        results = await self.detector.async_batch_detect(software_list)
        
        # 保存结果
        for i, result in enumerate(results):
            software_info = software_list[i]
            key = self._generate_software_key(software_info)
            self._save_detection_result(key, result)
            self._check_version_update(key, result)
        
        return results
    
    def get_software_list(self) -> List[Dict]:
        """
        获取注册的软件列表
        
        Returns:
            List[Dict]: 软件信息列表
        """
        software_list = []
        
        for key, software_info in self.software_registry.items():
            # 获取最新版本信息
            latest_result = self.get_latest_version(software_info.name)
            
            software_dict = asdict(software_info)
            if latest_result:
                software_dict.update({
                    'latest_version': latest_result.version,
                    'last_check_time': latest_result.detection_time.isoformat() if latest_result.detection_time else None,
                    'detection_success': latest_result.success
                })
            
            software_list.append(software_dict)
        
        return software_list
    
    def get_latest_version(self, software_name: str) -> Optional[DetectionResult]:
        """
        获取软件的最新版本信息
        
        Args:
            software_name: 软件名称
            
        Returns:
            Optional[DetectionResult]: 最新版本信息
        """
        key = self._find_software_key(software_name)
        if not key or key not in self.version_history:
            return None
        
        history = self.version_history[key]
        if not history:
            return None
        
        # 返回最新的成功检测结果
        for result in reversed(history):
            if result.success:
                return result
        
        # 如果没有成功的结果，返回最新的结果
        return history[-1] if history else None
    
    def get_version_history(self, software_name: str, limit: int = 10) -> List[DetectionResult]:
        """
        获取软件的版本历史
        
        Args:
            software_name: 软件名称
            limit: 返回记录数量限制
            
        Returns:
            List[DetectionResult]: 版本历史列表
        """
        key = self._find_software_key(software_name)
        if not key or key not in self.version_history:
            return []
        
        history = self.version_history[key]
        return history[-limit:] if limit > 0 else history
    
    def check_for_updates(self) -> List[Dict]:
        """
        检查所有软件的更新
        
        Returns:
            List[Dict]: 有更新的软件列表
        """
        updates = []
        
        for key, software_info in self.software_registry.items():
            # 获取当前版本
            current_result = self.get_latest_version(software_info.name)
            if not current_result or not current_result.success:
                continue
            
            # 检测新版本
            new_result = self.detector.detect_version(software_info)
            
            # 比较版本
            if (new_result.success and 
                new_result.version != current_result.version and
                self._is_newer_version(new_result.version, current_result.version)):
                
                updates.append({
                    'software_name': software_info.name,
                    'current_version': current_result.version,
                    'new_version': new_result.version,
                    'download_url': new_result.download_url,
                    'detection_time': new_result.detection_time
                })
                
                # 保存新结果
                self._save_detection_result(key, new_result)
        
        if updates:
            self.logger.info(f"发现 {len(updates)} 个软件更新")
            
            # 发送更新通知
            self.notification_service.notify_updates_available(updates)
        
        return updates
    
    def start_auto_update_scheduler(self):
        """启动自动更新调度器"""
        if self.scheduler_running:
            self.logger.warning("调度器已在运行")
            return
        
        self.scheduler_running = True
        
        # 配置调度任务
        schedule.every(self.update_interval).seconds.do(self._scheduled_update)
        
        # 启动调度器线程
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        self.logger.info(f"自动更新调度器已启动 (间隔: {self.update_interval}秒)")
    
    def stop_auto_update_scheduler(self):
        """停止自动更新调度器"""
        self.scheduler_running = False
        schedule.clear()
        
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        
        self.logger.info("自动更新调度器已停止")
    
    def add_version_update_callback(self, callback: Callable):
        """
        添加版本更新回调函数
        
        Args:
            callback: 回调函数
        """
        self.version_update_callbacks.append(callback)
    
    def add_detection_complete_callback(self, callback: Callable):
        """
        添加检测完成回调函数
        
        Args:
            callback: 回调函数
        """
        self.detection_complete_callbacks.append(callback)
    
    def export_data(self, format: str = 'json') -> str:
        """
        导出数据
        
        Args:
            format: 导出格式 (json, csv)
            
        Returns:
            str: 导出的数据
        """
        data = {
            'software_registry': {k: asdict(v) for k, v in self.software_registry.items()},
            'version_history': {k: [asdict(r) for r in v] for k, v in self.version_history.items()},
            'export_time': datetime.now().isoformat()
        }
        
        if format.lower() == 'json':
            return json.dumps(data, indent=2, default=str)
        elif format.lower() == 'csv':
            # TODO: 实现CSV导出
            pass
        
        return json.dumps(data, default=str)
    
    def import_data(self, data: str, format: str = 'json') -> bool:
        """
        导入数据
        
        Args:
            data: 数据字符串
            format: 数据格式
            
        Returns:
            bool: 是否成功
        """
        try:
            if format.lower() == 'json':
                imported_data = json.loads(data)
                
                # 导入软件注册表
                for key, software_dict in imported_data.get('software_registry', {}).items():
                    software_info = SoftwareInfo(**software_dict)
                    self.software_registry[key] = software_info
                
                # 导入版本历史
                for key, history_list in imported_data.get('version_history', {}).items():
                    history = []
                    for result_dict in history_list:
                        # 转换日期时间字段
                        if 'detection_time' in result_dict and result_dict['detection_time']:
                            result_dict['detection_time'] = datetime.fromisoformat(result_dict['detection_time'])
                        if 'release_date' in result_dict and result_dict['release_date']:
                            result_dict['release_date'] = datetime.fromisoformat(result_dict['release_date'])
                        
                        result = DetectionResult(**result_dict)
                        history.append(result)
                    
                    self.version_history[key] = history
                
                self.logger.info("数据导入成功")
                return True
            
        except Exception as e:
            self.logger.error(f"数据导入失败: {str(e)}")
            return False
        
        return False
    
    def get_statistics(self) -> Dict:
        """
        获取服务统计信息
        
        Returns:
            Dict: 统计信息
        """
        total_software = len(self.software_registry)
        total_detections = sum(len(history) for history in self.version_history.values())
        
        # 计算成功率
        successful_detections = 0
        for history in self.version_history.values():
            successful_detections += sum(1 for result in history if result.success)
        
        success_rate = (successful_detections / total_detections * 100) if total_detections > 0 else 0
        
        return {
            'total_software': total_software,
            'total_detections': total_detections,
            'successful_detections': successful_detections,
            'success_rate': round(success_rate, 2),
            'auto_update_enabled': self.auto_update_enabled,
            'scheduler_running': self.scheduler_running,
            'detector_stats': self.detector.get_statistics()
        }
    
    def _generate_software_key(self, software_info: SoftwareInfo) -> str:
        """生成软件唯一键"""
        return f"{software_info.name}:{hash(software_info.url)}"
    
    def _find_software_key(self, software_name: str) -> Optional[str]:
        """根据软件名称查找键"""
        for key, software_info in self.software_registry.items():
            if software_info.name == software_name:
                return key
        return None
    
    def _save_detection_result(self, key: str, result: DetectionResult):
        """保存检测结果到历史记录"""
        if key not in self.version_history:
            self.version_history[key] = []
        
        self.version_history[key].append(result)
        
        # 限制历史记录数量
        max_history = self.config.get('max_history_per_software', 100)
        if len(self.version_history[key]) > max_history:
            self.version_history[key] = self.version_history[key][-max_history:]
    
    def _check_version_update(self, key: str, new_result: DetectionResult):
        """检查是否有版本更新"""
        if not new_result.success:
            return
        
        history = self.version_history[key]
        if len(history) < 2:
            return
        
        # 获取上一个成功的结果
        previous_result = None
        for result in reversed(history[:-1]):
            if result.success:
                previous_result = result
                break
        
        if (previous_result and 
            new_result.version != previous_result.version and
            self._is_newer_version(new_result.version, previous_result.version)):
            
            # 触发版本更新回调
            update_info = {
                'software_name': self.software_registry[key].name,
                'previous_version': previous_result.version,
                'new_version': new_result.version,
                'download_url': new_result.download_url,
                'detection_time': new_result.detection_time
            }
            
            for callback in self.version_update_callbacks:
                try:
                    callback(update_info)
                except Exception as e:
                    self.logger.error(f"版本更新回调执行失败: {str(e)}")
            
            # 发送通知
            self.notification_service.notify_version_updated(update_info)
    
    def _is_newer_version(self, version1: str, version2: str) -> bool:
        """比较版本号大小"""
        try:
            # 简单的版本号比较
            v1_parts = [int(x) for x in version1.split('.')]
            v2_parts = [int(x) for x in version2.split('.')]
            
            # 补齐长度
            max_len = max(len(v1_parts), len(v2_parts))
            v1_parts.extend([0] * (max_len - len(v1_parts)))
            v2_parts.extend([0] * (max_len - len(v2_parts)))
            
            return v1_parts > v2_parts
            
        except:
            # 如果无法比较，认为是新版本
            return version1 != version2
    
    def _scheduled_update(self):
        """调度的更新任务"""
        try:
            self.logger.info("执行调度的版本检查")
            self.check_for_updates()
        except Exception as e:
            self.logger.error(f"调度更新失败: {str(e)}")
    
    def _run_scheduler(self):
        """运行调度器"""
        while self.scheduler_running:
            schedule.run_pending()
            time.sleep(1)