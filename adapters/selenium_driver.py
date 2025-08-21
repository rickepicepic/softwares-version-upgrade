#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Selenium驱动适配器 - 提供浏览器自动化接口
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from typing import Dict, Optional, List
import time

from ..utils.logger import get_logger


class SeleniumDriver:
    """Selenium浏览器驱动适配器"""
    
    def __init__(self, config: Dict = None):
        """
        初始化Selenium驱动
        
        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.logger = get_logger(__name__)
        
        # 基础配置
        self.headless = self.config.get('headless', True)
        self.timeout = self.config.get('timeout', 30)
        self.window_size = self.config.get('window_size', (1920, 1080))
        self.chrome_options_list = self.config.get('chrome_options', [
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--disable-images',
        ])
        
        # 驱动实例
        self.driver = None
        self.wait = None
        
        # 统计信息
        self.page_load_count = 0
        self.success_count = 0
        self.failure_count = 0
    
    def _create_driver(self) -> webdriver.Chrome:
        """创建Chrome驱动实例"""
        try:
            # 配置Chrome选项
            chrome_options = Options()
            
            if self.headless:
                chrome_options.add_argument('--headless')
            
            # 添加自定义选项
            for option in self.chrome_options_list:
                chrome_options.add_argument(option)
            
            # 设置窗口大小
            chrome_options.add_argument(f'--window-size={self.window_size[0]},{self.window_size[1]}')
            
            # 禁用日志
            chrome_options.add_argument('--log-level=3')
            chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # 创建服务
            service = Service(ChromeDriverManager().install())
            
            # 创建驱动
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.set_page_load_timeout(self.timeout)
            
            # 创建等待对象
            self.wait = WebDriverWait(driver, self.timeout)
            
            self.logger.info("Chrome驱动创建成功")
            return driver
            
        except Exception as e:
            self.logger.error(f"创建Chrome驱动失败: {str(e)}")
            raise
    
    def get_driver(self) -> webdriver.Chrome:
        """获取驱动实例"""
        if self.driver is None:
            self.driver = self._create_driver()
        return self.driver
    
    def get_page_source(self, url: str) -> Optional[str]:
        """
        获取页面源码
        
        Args:
            url: 目标URL
            
        Returns:
            Optional[str]: 页面源码
        """
        self.page_load_count += 1
        
        try:
            driver = self.get_driver()
            
            self.logger.debug(f"加载页面: {url}")
            driver.get(url)
            
            # 等待页面加载完成
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            # 等待一段时间让动态内容加载
            time.sleep(2)
            
            page_source = driver.page_source
            self.success_count += 1
            
            self.logger.debug(f"页面加载成功: {url}")
            return page_source
            
        except TimeoutException:
            self.failure_count += 1
            self.logger.error(f"页面加载超时: {url}")
            return None
        except WebDriverException as e:
            self.failure_count += 1
            self.logger.error(f"WebDriver异常: {url} - {str(e)}")
            return None
        except Exception as e:
            self.failure_count += 1
            self.logger.error(f"页面加载失败: {url} - {str(e)}")
            return None
    
    def find_element_text(self, url: str, selector: str, by: By = By.CSS_SELECTOR) -> Optional[str]:
        """
        查找元素文本
        
        Args:
            url: 目标URL
            selector: 选择器
            by: 选择器类型
            
        Returns:
            Optional[str]: 元素文本
        """
        try:
            driver = self.get_driver()
            driver.get(url)
            
            element = self.wait.until(EC.presence_of_element_located((by, selector)))
            return element.text
            
        except Exception as e:
            self.logger.error(f"查找元素失败: {url} - {str(e)}")
            return None
    
    def find_elements_text(self, url: str, selector: str, by: By = By.CSS_SELECTOR) -> List[str]:
        """
        查找多个元素文本
        
        Args:
            url: 目标URL
            selector: 选择器
            by: 选择器类型
            
        Returns:
            List[str]: 元素文本列表
        """
        try:
            driver = self.get_driver()
            driver.get(url)
            
            elements = self.wait.until(EC.presence_of_all_elements_located((by, selector)))
            return [element.text for element in elements]
            
        except Exception as e:
            self.logger.error(f"查找元素列表失败: {url} - {str(e)}")
            return []
    
    def click_element(self, selector: str, by: By = By.CSS_SELECTOR) -> bool:
        """
        点击元素
        
        Args:
            selector: 选择器
            by: 选择器类型
            
        Returns:
            bool: 是否成功
        """
        try:
            driver = self.get_driver()
            element = self.wait.until(EC.element_to_be_clickable((by, selector)))
            element.click()
            return True
            
        except Exception as e:
            self.logger.error(f"点击元素失败: {selector} - {str(e)}")
            return False
    
    def scroll_to_bottom(self):
        """滚动到页面底部"""
        try:
            driver = self.get_driver()
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            
        except Exception as e:
            self.logger.error(f"滚动失败: {str(e)}")
    
    def wait_for_element(self, selector: str, by: By = By.CSS_SELECTOR, timeout: int = None) -> bool:
        """
        等待元素出现
        
        Args:
            selector: 选择器
            by: 选择器类型
            timeout: 超时时间
            
        Returns:
            bool: 是否找到元素
        """
        try:
            wait_timeout = timeout or self.timeout
            wait = WebDriverWait(self.get_driver(), wait_timeout)
            wait.until(EC.presence_of_element_located((by, selector)))
            return True
            
        except TimeoutException:
            return False
        except Exception as e:
            self.logger.error(f"等待元素失败: {selector} - {str(e)}")
            return False
    
    def execute_script(self, script: str) -> any:
        """
        执行JavaScript脚本
        
        Args:
            script: JavaScript代码
            
        Returns:
            any: 脚本返回值
        """
        try:
            driver = self.get_driver()
            return driver.execute_script(script)
            
        except Exception as e:
            self.logger.error(f"执行脚本失败: {str(e)}")
            return None
    
    def take_screenshot(self, filename: str) -> bool:
        """
        截图
        
        Args:
            filename: 文件名
            
        Returns:
            bool: 是否成功
        """
        try:
            driver = self.get_driver()
            return driver.save_screenshot(filename)
            
        except Exception as e:
            self.logger.error(f"截图失败: {str(e)}")
            return False
    
    def get_stats(self) -> Dict:
        """
        获取统计信息
        
        Returns:
            Dict: 统计信息
        """
        total_loads = self.page_load_count
        success_rate = (self.success_count / total_loads * 100) if total_loads > 0 else 0
        
        return {
            'total_page_loads': total_loads,
            'success_count': self.success_count,
            'failure_count': self.failure_count,
            'success_rate': round(success_rate, 2),
            'driver_active': self.driver is not None
        }
    
    def reset_stats(self):
        """重置统计信息"""
        self.page_load_count = 0
        self.success_count = 0
        self.failure_count = 0
    
    def close(self):
        """关闭驱动"""
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info("Chrome驱动已关闭")
            except Exception as e:
                self.logger.error(f"关闭驱动失败: {str(e)}")
            finally:
                self.driver = None
                self.wait = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()