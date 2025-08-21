#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
系统测试脚本
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from core.detector import SoftwareVersionDetector, SoftwareInfo
from config.settings import load_config
from utils.logger import setup_logging


def test_single_detection():
    """测试单个软件检测"""
    print("=" * 50)
    print("测试单个软件检测")
    print("=" * 50)
    
    # 设置日志
    setup_logging(level='INFO')
    
    # 加载配置
    config = load_config()
    
    # 创建检测器
    detector = SoftwareVersionDetector(config)
    
    # 测试软件列表
    test_software = [
        SoftwareInfo(
            name="VS Code",
            url="https://code.visualstudio.com",
            strategy_hint="vscode"
        ),
        SoftwareInfo(
            name="Chrome",
            url="https://www.google.com/chrome/",
            strategy_hint="chrome"
        ),
        SoftwareInfo(
            name="Homebrew",
            url="https://github.com/Homebrew/brew",
            strategy_hint="github"
        )
    ]
    
    for software in test_software:
        print(f"\n检测软件: {software.name}")
        print(f"URL: {software.url}")
        
        try:
            result = detector.detect_version(software)
            
            if result.success:
                print(f"✓ 检测成功")
                print(f"  版本: {result.version}")
                print(f"  下载地址: {result.download_url}")
                print(f"  策略: {result.strategy_used}")
            else:
                print(f"✗ 检测失败: {result.error_message}")
                
        except Exception as e:
            print(f"✗ 异常: {str(e)}")


def test_batch_detection():
    """测试批量检测"""
    print("\n" + "=" * 50)
    print("测试批量检测")
    print("=" * 50)
    
    # 设置日志
    setup_logging(level='INFO')
    
    # 加载配置
    config = load_config()
    
    # 创建检测器
    detector = SoftwareVersionDetector(config)
    
    # 测试软件列表
    software_list = [
        SoftwareInfo(name="Chrome", url="https://www.google.com/chrome/"),
        SoftwareInfo(name="Firefox", url="https://www.mozilla.org/firefox/"),
        SoftwareInfo(name="VS Code", url="https://code.visualstudio.com"),
    ]
    
    print(f"批量检测 {len(software_list)} 个软件...")
    
    try:
        results = detector.batch_detect(software_list, concurrent=True)
        
        success_count = sum(1 for r in results if r.success)
        print(f"\n批量检测完成:")
        print(f"  总数: {len(results)}")
        print(f"  成功: {success_count}")
        print(f"  失败: {len(results) - success_count}")
        
        print(f"\n详细结果:")
        for result in results:
            status = "✓" if result.success else "✗"
            print(f"  {status} {result.name}: {result.version if result.success else result.error_message}")
            
    except Exception as e:
        print(f"✗ 批量检测异常: {str(e)}")


def test_strategy_selection():
    """测试策略选择"""
    print("\n" + "=" * 50)
    print("测试策略选择")
    print("=" * 50)
    
    # 设置日志
    setup_logging(level='INFO')
    
    # 加载配置
    config = load_config()
    
    # 创建检测器
    detector = SoftwareVersionDetector(config)
    
    # 获取支持的软件列表
    supported_software = detector.get_supported_software()
    
    print(f"支持的软件策略:")
    strategies = {}
    for software in supported_software:
        strategy = software.get('strategy', 'unknown')
        if strategy not in strategies:
            strategies[strategy] = []
        strategies[strategy].append(software['name'])
    
    for strategy_name, software_names in strategies.items():
        print(f"\n{strategy_name}:")
        for name in software_names:
            print(f"  - {name}")


def test_configuration():
    """测试配置加载"""
    print("\n" + "=" * 50)
    print("测试配置加载")
    print("=" * 50)
    
    try:
        config = load_config()
        print("✓ 配置加载成功")
        
        # 显示主要配置项
        print(f"  检测器超时: {config.get('detector', {}).get('timeout', 'N/A')}秒")
        print(f"  最大工作线程: {config.get('detector', {}).get('max_workers', 'N/A')}")
        print(f"  API端口: {config.get('api', {}).get('port', 'N/A')}")
        print(f"  缓存类型: {config.get('cache', {}).get('type', 'N/A')}")
        
    except Exception as e:
        print(f"✗ 配置加载失败: {str(e)}")


def main():
    """主函数"""
    print("Mac软件版本追踪器 - 系统测试")
    print("=" * 60)
    
    try:
        # 测试配置
        test_configuration()
        
        # 测试策略选择
        test_strategy_selection()
        
        # 测试单个检测
        test_single_detection()
        
        # 测试批量检测
        test_batch_detection()
        
        print("\n" + "=" * 60)
        print("系统测试完成")
        
    except KeyboardInterrupt:
        print("\n用户中断测试")
    except Exception as e:
        print(f"\n系统测试异常: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()