#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
配置管理模块
"""

import os
import yaml
from typing import Dict, Any


def load_config(config_path: str = None) -> Dict[str, Any]:
    """
    加载配置文件
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        Dict[str, Any]: 配置字典
    """
    # 默认配置
    default_config = {
        # 检测器配置
        'detector': {
            'timeout': 30,
            'max_retries': 3,
            'max_workers': 10,
            'cache_ttl': 3600,
        },
        
        # 网页爬虫配置
        'scraper': {
            'timeout': 30,
            'max_retries': 3,
            'retry_delay': 1,
            'user_agents': [
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            ]
        },
        
        # Selenium配置
        'selenium': {
            'headless': True,
            'timeout': 30,
            'window_size': (1920, 1080),
            'chrome_options': [
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-images',
                '--disable-javascript',
            ]
        },
        
        # API配置
        'api': {
            'host': '0.0.0.0',
            'port': 8080,
            'debug': False,
            'cors_enabled': True,
        },
        
        # 缓存配置
        'cache': {
            'type': 'memory',  # memory, redis, disk
            'ttl': 3600,
            'max_size': 1000,
        },
        
        # 通知配置
        'notifications': {
            'enabled': True,
            'channels': {
                'slack': {
                    'enabled': False,
                    'webhook_url': '',
                },
                'email': {
                    'enabled': False,
                    'smtp_server': '',
                    'smtp_port': 587,
                    'username': '',
                    'password': '',
                },
                'dingtalk': {
                    'enabled': False,
                    'webhook_url': '',
                    'secret': '',
                }
            }
        },
        
        # 日志配置
        'logging': {
            'level': 'INFO',
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'file': 'logs/app.log',
            'max_size': '10MB',
            'backup_count': 5,
        },
        
        # 版本服务配置
        'version_service': {
            'auto_update': False,
            'update_interval': 3600,
            'batch_size': 50,
            'max_history_per_software': 100,
        },
        
        # 策略配置
        'strategies': {
            'github': {
                'priority': 90,
                'api_token': '',  # GitHub API token for higher rate limits
            },
            'chrome': {
                'priority': 85,
            },
            'microsoft': {
                'priority': 80,
            },
            'generic': {
                'priority': 1,
            }
        }
    }
    
    # 如果指定了配置文件，加载并合并
    if config_path and os.path.exists(config_path):
        try:
            if config_path.endswith('.yaml') or config_path.endswith('.yml'):
                with open(config_path, 'r', encoding='utf-8') as f:
                    file_config = yaml.safe_load(f)
            elif config_path.endswith('.py'):
                # 动态导入Python配置文件
                import importlib.util
                spec = importlib.util.spec_from_file_location("config", config_path)
                config_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(config_module)
                file_config = getattr(config_module, 'CONFIG', {})
            else:
                raise ValueError(f"不支持的配置文件格式: {config_path}")
            
            # 递归合并配置
            default_config = _merge_config(default_config, file_config)
            
        except Exception as e:
            print(f"警告: 加载配置文件失败 {config_path}: {str(e)}")
    
    # 从环境变量覆盖配置
    default_config = _load_env_config(default_config)
    
    return default_config


def _merge_config(base_config: Dict, override_config: Dict) -> Dict:
    """
    递归合并配置字典
    
    Args:
        base_config: 基础配置
        override_config: 覆盖配置
        
    Returns:
        Dict: 合并后的配置
    """
    result = base_config.copy()
    
    for key, value in override_config.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _merge_config(result[key], value)
        else:
            result[key] = value
    
    return result


def _load_env_config(config: Dict) -> Dict:
    """
    从环境变量加载配置
    
    Args:
        config: 基础配置
        
    Returns:
        Dict: 更新后的配置
    """
    # 定义环境变量映射
    env_mappings = {
        'TRACKER_API_HOST': ['api', 'host'],
        'TRACKER_API_PORT': ['api', 'port'],
        'TRACKER_API_DEBUG': ['api', 'debug'],
        'TRACKER_CACHE_TYPE': ['cache', 'type'],
        'TRACKER_CACHE_TTL': ['cache', 'ttl'],
        'TRACKER_LOG_LEVEL': ['logging', 'level'],
        'TRACKER_SELENIUM_HEADLESS': ['selenium', 'headless'],
        'TRACKER_GITHUB_TOKEN': ['strategies', 'github', 'api_token'],
        'TRACKER_SLACK_WEBHOOK': ['notifications', 'channels', 'slack', 'webhook_url'],
        'TRACKER_EMAIL_SMTP_SERVER': ['notifications', 'channels', 'email', 'smtp_server'],
        'TRACKER_EMAIL_USERNAME': ['notifications', 'channels', 'email', 'username'],
        'TRACKER_EMAIL_PASSWORD': ['notifications', 'channels', 'email', 'password'],
    }
    
    for env_var, config_path in env_mappings.items():
        env_value = os.getenv(env_var)
        if env_value is not None:
            # 设置嵌套配置值
            current = config
            for key in config_path[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]
            
            # 类型转换
            final_key = config_path[-1]
            if final_key in ['port', 'ttl', 'max_size', 'backup_count', 'update_interval']:
                current[final_key] = int(env_value)
            elif final_key in ['debug', 'headless', 'enabled', 'auto_update']:
                current[final_key] = env_value.lower() in ('true', '1', 'yes', 'on')
            else:
                current[final_key] = env_value
    
    return config


# 示例配置文件内容（可以保存为config.yaml）
EXAMPLE_CONFIG_YAML = """
# Mac软件版本追踪器配置文件

detector:
  timeout: 30
  max_retries: 3
  max_workers: 10

scraper:
  timeout: 30
  max_retries: 3

selenium:
  headless: true
  timeout: 30

api:
  host: "0.0.0.0"
  port: 8080
  debug: false

cache:
  type: "memory"  # memory, redis, disk
  ttl: 3600

notifications:
  enabled: true
  channels:
    slack:
      enabled: false
      webhook_url: ""
    email:
      enabled: false
      smtp_server: ""
      username: ""
      password: ""

logging:
  level: "INFO"
  file: "logs/app.log"

strategies:
  github:
    api_token: ""  # GitHub API token
"""