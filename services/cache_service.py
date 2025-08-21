#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
缓存服务 - 提供多种缓存实现
"""

import time
import pickle
import hashlib
from typing import Any, Optional, Dict
from abc import ABC, abstractmethod
import threading

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from utils.logger import get_logger


class CacheBackend(ABC):
    """缓存后端抽象基类"""
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """设置缓存值"""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """删除缓存值"""
        pass
    
    @abstractmethod
    def clear(self) -> bool:
        """清空缓存"""
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        pass


class MemoryCacheBackend(CacheBackend):
    """内存缓存后端"""
    
    def __init__(self, max_size: int = 1000):
        self.cache = {}
        self.access_times = {}
        self.max_size = max_size
        self.lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Any]:
        with self.lock:
            if key in self.cache:
                value, expire_time = self.cache[key]
                
                # 检查是否过期
                if expire_time and time.time() > expire_time:
                    del self.cache[key]
                    if key in self.access_times:
                        del self.access_times[key]
                    return None
                
                # 更新访问时间
                self.access_times[key] = time.time()
                return value
            
            return None
    
    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        with self.lock:
            # 计算过期时间
            expire_time = time.time() + ttl if ttl else None
            
            # 如果缓存已满，删除最久未访问的项
            if len(self.cache) >= self.max_size and key not in self.cache:
                self._evict_lru()
            
            self.cache[key] = (value, expire_time)
            self.access_times[key] = time.time()
            return True
    
    def delete(self, key: str) -> bool:
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                if key in self.access_times:
                    del self.access_times[key]
                return True
            return False
    
    def clear(self) -> bool:
        with self.lock:
            self.cache.clear()
            self.access_times.clear()
            return True
    
    def exists(self, key: str) -> bool:
        return self.get(key) is not None
    
    def _evict_lru(self):
        """删除最久未访问的项"""
        if not self.access_times:
            return
        
        # 找到最久未访问的键
        lru_key = min(self.access_times, key=self.access_times.get)
        self.delete(lru_key)


class DiskCacheBackend(CacheBackend):
    """磁盘缓存后端"""
    
    def __init__(self, cache_dir: str = ".cache"):
        import os
        self.cache_dir = cache_dir
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        self.lock = threading.RLock()
    
    def _get_file_path(self, key: str) -> str:
        """获取缓存文件路径"""
        import os
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{key_hash}.cache")
    
    def get(self, key: str) -> Optional[Any]:
        import os
        
        with self.lock:
            file_path = self._get_file_path(key)
            
            if not os.path.exists(file_path):
                return None
            
            try:
                with open(file_path, 'rb') as f:
                    data = pickle.load(f)
                    value, expire_time = data['value'], data['expire_time']
                    
                    # 检查是否过期
                    if expire_time and time.time() > expire_time:
                        os.remove(file_path)
                        return None
                    
                    return value
                    
            except Exception:
                # 文件损坏，删除
                try:
                    os.remove(file_path)
                except:
                    pass
                return None
    
    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        with self.lock:
            file_path = self._get_file_path(key)
            expire_time = time.time() + ttl if ttl else None
            
            try:
                data = {
                    'value': value,
                    'expire_time': expire_time,
                    'created_time': time.time()
                }
                
                with open(file_path, 'wb') as f:
                    pickle.dump(data, f)
                
                return True
                
            except Exception:
                return False
    
    def delete(self, key: str) -> bool:
        import os
        
        with self.lock:
            file_path = self._get_file_path(key)
            
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    return True
                return False
                
            except Exception:
                return False
    
    def clear(self) -> bool:
        import os
        import glob
        
        with self.lock:
            try:
                cache_files = glob.glob(os.path.join(self.cache_dir, "*.cache"))
                for file_path in cache_files:
                    os.remove(file_path)
                return True
                
            except Exception:
                return False
    
    def exists(self, key: str) -> bool:
        return self.get(key) is not None


class CacheService:
    """缓存服务"""
    
    def __init__(self, config: Dict = None):
        """
        初始化缓存服务
        
        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.logger = get_logger(__name__)
        
        # 配置参数
        cache_type = self.config.get('type', 'memory')
        self.default_ttl = self.config.get('ttl', 3600)
        
        # 创建缓存后端
        if cache_type == 'memory':
            max_size = self.config.get('max_size', 1000)
            self.backend = MemoryCacheBackend(max_size)
        elif cache_type == 'disk':
            cache_dir = self.config.get('cache_dir', '.cache')
            self.backend = DiskCacheBackend(cache_dir)
        elif cache_type == 'redis':
            # TODO: 实现Redis缓存
            self.logger.warning("Redis缓存暂未实现，使用内存缓存")
            self.backend = MemoryCacheBackend()
        else:
            self.logger.warning(f"未知缓存类型: {cache_type}，使用内存缓存")
            self.backend = MemoryCacheBackend()
        
        # 统计信息
        self.hit_count = 0
        self.miss_count = 0
        self.set_count = 0
        
        self.logger.info(f"缓存服务初始化完成，类型: {cache_type}")
    
    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            Optional[Any]: 缓存值
        """
        try:
            value = self.backend.get(key)
            
            if value is not None:
                self.hit_count += 1
                self.logger.debug(f"缓存命中: {key}")
            else:
                self.miss_count += 1
                self.logger.debug(f"缓存未命中: {key}")
            
            return value
            
        except Exception as e:
            self.logger.error(f"获取缓存失败: {key} - {str(e)}")
            self.miss_count += 1
            return None
    
    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 生存时间（秒）
            
        Returns:
            bool: 是否成功
        """
        try:
            ttl = ttl or self.default_ttl
            success = self.backend.set(key, value, ttl)
            
            if success:
                self.set_count += 1
                self.logger.debug(f"设置缓存成功: {key}")
            else:
                self.logger.warning(f"设置缓存失败: {key}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"设置缓存异常: {key} - {str(e)}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        删除缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            bool: 是否成功
        """
        try:
            success = self.backend.delete(key)
            
            if success:
                self.logger.debug(f"删除缓存成功: {key}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"删除缓存异常: {key} - {str(e)}")
            return False
    
    def clear(self) -> bool:
        """
        清空所有缓存
        
        Returns:
            bool: 是否成功
        """
        try:
            success = self.backend.clear()
            
            if success:
                self.logger.info("清空缓存成功")
                # 重置统计信息
                self.hit_count = 0
                self.miss_count = 0
                self.set_count = 0
            
            return success
            
        except Exception as e:
            self.logger.error(f"清空缓存异常: {str(e)}")
            return False
    
    def exists(self, key: str) -> bool:
        """
        检查缓存键是否存在
        
        Args:
            key: 缓存键
            
        Returns:
            bool: 是否存在
        """
        try:
            return self.backend.exists(key)
        except Exception as e:
            self.logger.error(f"检查缓存存在性异常: {key} - {str(e)}")
            return False
    
    def get_or_set(self, key: str, factory_func, ttl: int = None) -> Any:
        """
        获取缓存值，如果不存在则通过工厂函数创建
        
        Args:
            key: 缓存键
            factory_func: 工厂函数
            ttl: 生存时间
            
        Returns:
            Any: 缓存值
        """
        value = self.get(key)
        
        if value is None:
            try:
                value = factory_func()
                if value is not None:
                    self.set(key, value, ttl)
            except Exception as e:
                self.logger.error(f"工厂函数执行失败: {key} - {str(e)}")
                return None
        
        return value
    
    def get_stats(self) -> Dict:
        """
        获取缓存统计信息
        
        Returns:
            Dict: 统计信息
        """
        total_requests = self.hit_count + self.miss_count
        hit_rate = (self.hit_count / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'hit_count': self.hit_count,
            'miss_count': self.miss_count,
            'set_count': self.set_count,
            'total_requests': total_requests,
            'hit_rate': round(hit_rate, 2),
            'backend_type': type(self.backend).__name__
        }
    
    def reset_stats(self):
        """重置统计信息"""
        self.hit_count = 0
        self.miss_count = 0
        self.set_count = 0