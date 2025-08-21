#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
简化测试脚本
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_imports():
    """测试基本导入"""
    print("测试基本导入...")
    
    try:
        from config.settings import load_config
        print("✓ 配置模块导入成功")
        
        config = load_config()
        print("✓ 配置加载成功")
        
        from utils.logger import setup_logging, get_logger
        print("✓ 日志模块导入成功")
        
        setup_logging(level='INFO')
        logger = get_logger(__name__)
        logger.info("日志系统测试")
        print("✓ 日志系统工作正常")
        
        from utils.validators import validate_software_name, validate_url
        print("✓ 验证器模块导入成功")
        
        # 测试验证器
        assert validate_software_name("Chrome") == True
        assert validate_url("https://www.google.com/chrome/") == True
        print("✓ 验证器功能正常")
        
        from adapters.web_scraper import WebScraper
        print("✓ 网页爬虫模块导入成功")
        
        from adapters.api_client import APIClient
        print("✓ API客户端模块导入成功")
        
        from services.cache_service import CacheService
        print("✓ 缓存服务模块导入成功")
        
        from services.notification_service import NotificationService
        print("✓ 通知服务模块导入成功")
        
        print("\n所有基础模块导入测试通过！")
        return True
        
    except Exception as e:
        print(f"✗ 导入测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_basic_functionality():
    """测试基本功能"""
    print("\n测试基本功能...")
    
    try:
        from config.settings import load_config
        from adapters.web_scraper import WebScraper
        from services.cache_service import CacheService
        
        # 测试配置
        config = load_config()
        print("✓ 配置系统正常")
        
        # 测试缓存
        cache_service = CacheService(config.get('cache', {}))
        cache_service.set('test_key', 'test_value')
        value = cache_service.get('test_key')
        assert value == 'test_value'
        print("✓ 缓存系统正常")
        
        # 测试网页爬虫
        scraper = WebScraper(config.get('scraper', {}))
        print("✓ 网页爬虫初始化正常")
        
        print("\n基本功能测试通过！")
        return True
        
    except Exception as e:
        print(f"✗ 功能测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_excel_loading():
    """测试Excel文件加载"""
    print("\n测试Excel文件加载...")
    
    try:
        import pandas as pd
        
        # 检查示例文件是否存在
        if os.path.exists('example_software.xlsx'):
            df = pd.read_excel('example_software.xlsx')
            print(f"✓ Excel文件加载成功，包含 {len(df)} 行数据")
            
            # 检查必要的列
            required_columns = ['软件名称', '官网地址']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if not missing_columns:
                print("✓ Excel文件格式正确")
                
                # 显示前几行数据
                print("\n示例数据:")
                for i, row in df.head(3).iterrows():
                    print(f"  {row['软件名称']}: {row['官网地址']}")
                
                return True
            else:
                print(f"✗ Excel文件缺少必要的列: {missing_columns}")
                return False
        else:
            print("✗ 示例Excel文件不存在")
            return False
            
    except Exception as e:
        print(f"✗ Excel加载测试失败: {str(e)}")
        return False


def main():
    """主函数"""
    print("Mac软件版本追踪器 - 简化测试")
    print("=" * 50)
    
    success_count = 0
    total_tests = 3
    
    # 测试导入
    if test_imports():
        success_count += 1
    
    # 测试基本功能
    if test_basic_functionality():
        success_count += 1
    
    # 测试Excel加载
    if test_excel_loading():
        success_count += 1
    
    print("\n" + "=" * 50)
    print(f"测试完成: {success_count}/{total_tests} 通过")
    
    if success_count == total_tests:
        print("🎉 所有测试通过！系统基础功能正常。")
        print("\n下一步可以尝试:")
        print("1. 运行 python3 main.py detect-single --name 'Chrome' --url 'https://www.google.com/chrome/'")
        print("2. 运行 python3 main.py detect-batch --input example_software.xlsx")
        print("3. 运行 python3 main.py start-service --software-list example_software.xlsx")
    else:
        print("❌ 部分测试失败，请检查错误信息。")


if __name__ == "__main__":
    main()