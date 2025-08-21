#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
通知服务 - 提供多种通知方式
"""

import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional
import requests
import hashlib
import hmac
import base64
import time

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from utils.logger import get_logger


class NotificationChannel:
    """通知渠道基类"""
    
    def __init__(self, name: str, config: Dict):
        self.name = name
        self.config = config
        self.enabled = config.get('enabled', False)
        self.logger = get_logger(f"notification.{name}")
    
    def send(self, message: str, title: str = None, **kwargs) -> bool:
        """发送通知"""
        if not self.enabled:
            return True
        
        try:
            return self._send_impl(message, title, **kwargs)
        except Exception as e:
            self.logger.error(f"发送通知失败: {str(e)}")
            return False
    
    def _send_impl(self, message: str, title: str = None, **kwargs) -> bool:
        """具体的发送实现"""
        raise NotImplementedError


class SlackChannel(NotificationChannel):
    """Slack通知渠道"""
    
    def _send_impl(self, message: str, title: str = None, **kwargs) -> bool:
        webhook_url = self.config.get('webhook_url')
        if not webhook_url:
            self.logger.error("Slack webhook URL未配置")
            return False
        
        # 构建消息
        payload = {
            "text": title or "Mac软件版本追踪器通知",
            "attachments": [
                {
                    "color": kwargs.get('color', 'good'),
                    "text": message,
                    "ts": int(time.time())
                }
            ]
        }
        
        # 发送请求
        response = requests.post(
            webhook_url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 200:
            self.logger.info("Slack通知发送成功")
            return True
        else:
            self.logger.error(f"Slack通知发送失败: {response.status_code}")
            return False


class EmailChannel(NotificationChannel):
    """邮件通知渠道"""
    
    def _send_impl(self, message: str, title: str = None, **kwargs) -> bool:
        smtp_server = self.config.get('smtp_server')
        smtp_port = self.config.get('smtp_port', 587)
        username = self.config.get('username')
        password = self.config.get('password')
        to_emails = self.config.get('to_emails', [])
        
        if not all([smtp_server, username, password, to_emails]):
            self.logger.error("邮件配置不完整")
            return False
        
        try:
            # 创建邮件
            msg = MIMEMultipart()
            msg['From'] = username
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = title or "Mac软件版本追踪器通知"
            
            # 添加邮件内容
            msg.attach(MIMEText(message, 'plain', 'utf-8'))
            
            # 发送邮件
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(username, password)
                server.send_message(msg)
            
            self.logger.info("邮件通知发送成功")
            return True
            
        except Exception as e:
            self.logger.error(f"邮件发送失败: {str(e)}")
            return False


class DingTalkChannel(NotificationChannel):
    """钉钉通知渠道"""
    
    def _send_impl(self, message: str, title: str = None, **kwargs) -> bool:
        webhook_url = self.config.get('webhook_url')
        secret = self.config.get('secret')
        
        if not webhook_url:
            self.logger.error("钉钉webhook URL未配置")
            return False
        
        # 如果配置了密钥，计算签名
        if secret:
            timestamp = str(round(time.time() * 1000))
            string_to_sign = f'{timestamp}\n{secret}'
            hmac_code = hmac.new(
                secret.encode('utf-8'),
                string_to_sign.encode('utf-8'),
                digestmod=hashlib.sha256
            ).digest()
            sign = base64.b64encode(hmac_code).decode('utf-8')
            webhook_url += f'&timestamp={timestamp}&sign={sign}'
        
        # 构建消息
        payload = {
            "msgtype": "text",
            "text": {
                "content": f"{title or 'Mac软件版本追踪器通知'}\n\n{message}"
            }
        }
        
        # 发送请求
        response = requests.post(
            webhook_url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('errcode') == 0:
                self.logger.info("钉钉通知发送成功")
                return True
            else:
                self.logger.error(f"钉钉通知发送失败: {result.get('errmsg')}")
                return False
        else:
            self.logger.error(f"钉钉通知发送失败: {response.status_code}")
            return False


class NotificationService:
    """通知服务"""
    
    def __init__(self, config: Dict = None):
        """
        初始化通知服务
        
        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.logger = get_logger(__name__)
        
        self.enabled = self.config.get('enabled', True)
        self.channels: Dict[str, NotificationChannel] = {}
        
        # 初始化通知渠道
        self._initialize_channels()
        
        # 统计信息
        self.sent_count = 0
        self.failed_count = 0
        
        self.logger.info(f"通知服务初始化完成，启用渠道: {list(self.channels.keys())}")
    
    def _initialize_channels(self):
        """初始化通知渠道"""
        channels_config = self.config.get('channels', {})
        
        # Slack渠道
        if 'slack' in channels_config:
            slack_config = channels_config['slack']
            self.channels['slack'] = SlackChannel('slack', slack_config)
        
        # 邮件渠道
        if 'email' in channels_config:
            email_config = channels_config['email']
            self.channels['email'] = EmailChannel('email', email_config)
        
        # 钉钉渠道
        if 'dingtalk' in channels_config:
            dingtalk_config = channels_config['dingtalk']
            self.channels['dingtalk'] = DingTalkChannel('dingtalk', dingtalk_config)
    
    def send_notification(self, message: str, title: str = None, 
                         channels: List[str] = None, **kwargs) -> bool:
        """
        发送通知
        
        Args:
            message: 通知消息
            title: 通知标题
            channels: 指定的通知渠道列表
            **kwargs: 额外参数
            
        Returns:
            bool: 是否至少有一个渠道发送成功
        """
        if not self.enabled:
            return True
        
        # 如果没有指定渠道，使用所有启用的渠道
        if channels is None:
            channels = list(self.channels.keys())
        
        success_count = 0
        
        for channel_name in channels:
            if channel_name in self.channels:
                channel = self.channels[channel_name]
                if channel.send(message, title, **kwargs):
                    success_count += 1
                else:
                    self.failed_count += 1
            else:
                self.logger.warning(f"未知的通知渠道: {channel_name}")
        
        if success_count > 0:
            self.sent_count += 1
            return True
        else:
            return False
    
    def notify_version_detected(self, result) -> bool:
        """
        通知版本检测完成
        
        Args:
            result: 检测结果
            
        Returns:
            bool: 是否发送成功
        """
        if not result.success:
            return True  # 不通知失败的检测
        
        message = f"""
软件版本检测完成

软件名称: {result.name}
版本号: {result.version}
下载地址: {result.download_url or '未获取到'}
检测时间: {result.detection_time}
使用策略: {result.strategy_used or '未知'}
        """.strip()
        
        return self.send_notification(
            message=message,
            title="软件版本检测完成",
            color="good"
        )
    
    def notify_version_updated(self, update_info: Dict) -> bool:
        """
        通知版本更新
        
        Args:
            update_info: 更新信息
            
        Returns:
            bool: 是否发送成功
        """
        message = f"""
发现软件版本更新！

软件名称: {update_info['software_name']}
当前版本: {update_info['previous_version']}
新版本: {update_info['new_version']}
下载地址: {update_info.get('download_url', '未获取到')}
检测时间: {update_info['detection_time']}
        """.strip()
        
        return self.send_notification(
            message=message,
            title="软件版本更新通知",
            color="warning"
        )
    
    def notify_updates_available(self, updates: List[Dict]) -> bool:
        """
        通知有多个软件更新
        
        Args:
            updates: 更新列表
            
        Returns:
            bool: 是否发送成功
        """
        if not updates:
            return True
        
        message_lines = [f"发现 {len(updates)} 个软件更新：\n"]
        
        for update in updates:
            message_lines.append(
                f"• {update['software_name']}: {update['current_version']} → {update['new_version']}"
            )
        
        message = "\n".join(message_lines)
        
        return self.send_notification(
            message=message,
            title="批量软件更新通知",
            color="warning"
        )
    
    def notify_detection_failed(self, result) -> bool:
        """
        通知检测失败
        
        Args:
            result: 检测结果
            
        Returns:
            bool: 是否发送成功
        """
        message = f"""
软件版本检测失败

软件名称: {result.name}
错误信息: {result.error_message}
检测时间: {result.detection_time}
使用策略: {result.strategy_used or '未知'}
        """.strip()
        
        return self.send_notification(
            message=message,
            title="软件版本检测失败",
            color="danger"
        )
    
    def notify_system_error(self, error_message: str) -> bool:
        """
        通知系统错误
        
        Args:
            error_message: 错误消息
            
        Returns:
            bool: 是否发送成功
        """
        message = f"""
系统错误通知

错误信息: {error_message}
发生时间: {time.strftime('%Y-%m-%d %H:%M:%S')}
        """.strip()
        
        return self.send_notification(
            message=message,
            title="系统错误通知",
            color="danger"
        )
    
    def configure(self, config: Dict):
        """
        重新配置通知服务
        
        Args:
            config: 新的配置
        """
        self.config = config
        self.enabled = config.get('enabled', True)
        self.channels.clear()
        self._initialize_channels()
        
        self.logger.info("通知服务重新配置完成")
    
    def get_stats(self) -> Dict:
        """
        获取统计信息
        
        Returns:
            Dict: 统计信息
        """
        return {
            'enabled': self.enabled,
            'channels': list(self.channels.keys()),
            'sent_count': self.sent_count,
            'failed_count': self.failed_count,
            'channel_status': {
                name: channel.enabled 
                for name, channel in self.channels.items()
            }
        }
    
    def test_channels(self) -> Dict[str, bool]:
        """
        测试所有通知渠道
        
        Returns:
            Dict[str, bool]: 各渠道测试结果
        """
        results = {}
        test_message = "这是一条测试消息，用于验证通知渠道是否正常工作。"
        
        for name, channel in self.channels.items():
            if channel.enabled:
                results[name] = channel.send(test_message, "通知渠道测试")
            else:
                results[name] = False
        
        return results