#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
快速启动脚本 - 演示系统核心功能
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def demo_single_detection():
    """演示单个软件检测"""
    print("🔍 演示单个软件检测")
    print("-" * 40)
    
    try:
        from config.settings import load_config
        from utils.logger import setup_logging
        from adapters.web_scraper import WebScraper
        from adapters.api_client import APIClient
        from core.strategies.github_strategy import GitHubStrategy
        from core.strategies.chrome_strategy import ChromeStrategy
        from core.strategies.generic_strategy import GenericStrategy
        
        # 设置日志
        setup_logging(level='INFO')
        
        # 加载配置
        config = load_config()
        
        # 创建适配器
        web_scraper = WebScraper(config.get('scraper', {}))
        api_client = APIClient(config.get('api', {}))
        
        adapters = {
            'web_scraper': web_scraper,
            'api_client': api_client,
            'selenium_driver': None  # 简化演示，不使用Selenium
        }
        
        # 测试软件列表
        test_cases = [
            {
                'name': 'Homebrew',
                'url': 'https://github.com/Homebrew/brew',
                'strategy': GitHubStrategy()
            },
            {
                'name': 'Chrome',
                'url': 'https://www.google.com/chrome/',
                'strategy': ChromeStrategy()
            }
        ]
        
        for test_case in test_cases:
            print(f"\n检测软件: {test_case['name']}")
            print(f"URL: {test_case['url']}")
            print(f"策略: {test_case['strategy'].name}")
            
            # 创建软件信息对象
            class SoftwareInfo:
                def __init__(self, name, url):
                    self.name = name
                    self.url = url
            
            software_info = SoftwareInfo(test_case['name'], test_case['url'])
            
            # 检查策略是否能处理
            if test_case['strategy'].can_handle(software_info):
                print("✓ 策略匹配")
                
                # 执行检测（简化版本，仅演示）
                try:
                    result = test_case['strategy'].detect(software_info, adapters)
                    
                    if result.get('success'):
                        print(f"✓ 检测成功")
                        print(f"  版本: {result.get('version', '未知')}")
                        print(f"  来源: {result.get('source', '未知')}")
                    else:
                        print(f"✗ 检测失败: {result.get('error', '未知错误')}")
                        
                except Exception as e:
                    print(f"✗ 检测异常: {str(e)}")
            else:
                print("✗ 策略不匹配")
        
        print(f"\n演示完成！")
        return True
        
    except Exception as e:
        print(f"✗ 演示失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def demo_cache_system():
    """演示缓存系统"""
    print("\n💾 演示缓存系统")
    print("-" * 40)
    
    try:
        from services.cache_service import CacheService
        
        # 创建缓存服务
        cache_service = CacheService({'type': 'memory', 'ttl': 60})
        
        # 测试缓存操作
        print("设置缓存...")
        cache_service.set('test_software', {
            'name': 'Test Software',
            'version': '1.0.0',
            'url': 'https://example.com'
        })
        
        print("获取缓存...")
        cached_data = cache_service.get('test_software')
        
        if cached_data:
            print(f"✓ 缓存命中: {cached_data['name']} v{cached_data['version']}")
        else:
            print("✗ 缓存未命中")
        
        # 显示统计信息
        stats = cache_service.get_stats()
        print(f"缓存统计: 命中率 {stats['hit_rate']}%")
        
        return True
        
    except Exception as e:
        print(f"✗ 缓存演示失败: {str(e)}")
        return False


def demo_version_parser():
    """演示版本解析器"""
    print("\n🔢 演示版本解析器")
    print("-" * 40)
    
    try:
        from core.parsers.version_parser import VersionParser
        
        parser = VersionParser()
        
        # 测试版本号
        test_versions = [
            "1.2.3",
            "v2.0.0-beta.1",
            "2024.1.0",
            "Build 123",
            "Chrome 120.0.6099.109",
            "Office 2021"
        ]
        
        print("解析版本号:")
        for version_str in test_versions:
            version_info = parser.parse(version_str)
            if version_info:
                print(f"  {version_str:20} -> {version_info.major}.{version_info.minor}.{version_info.patch}")
            else:
                print(f"  {version_str:20} -> 解析失败")
        
        # 测试版本比较
        print(f"\n版本比较:")
        print(f"  1.2.3 vs 1.2.4: {'新版本' if parser.is_newer('1.2.4', '1.2.3') else '旧版本'}")
        print(f"  2024.1.0 vs 2023.12.0: {'新版本' if parser.is_newer('2024.1.0', '2023.12.0') else '旧版本'}")
        
        return True
        
    except Exception as e:
        print(f"✗ 版本解析演示失败: {str(e)}")
        return False


def main():
    """主函数"""
    print("🚀 Mac软件版本追踪器 - 快速演示")
    print("=" * 50)
    
    success_count = 0
    total_demos = 3
    
    # 演示单个检测
    if demo_single_detection():
        success_count += 1
    
    # 演示缓存系统
    if demo_cache_system():
        success_count += 1
    
    # 演示版本解析
    if demo_version_parser():
        success_count += 1
    
    print("\n" + "=" * 50)
    print(f"演示完成: {success_count}/{total_demos} 成功")
    
    if success_count == total_demos:
        print("🎉 所有演示成功！系统核心功能正常。")
        print("\n📚 更多功能请参考:")
        print("  - README.md: 详细文档")
        print("  - PROJECT_SUMMARY.md: 项目总结")
        print("  - example_software.xlsx: 示例软件列表")
        print("\n🔧 命令行工具:")
        print("  python3 main.py --help")
    else:
        print("❌ 部分演示失败，请检查错误信息。")


if __name__ == "__main__":
    main()