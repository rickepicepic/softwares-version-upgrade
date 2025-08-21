#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Mac软件版本追踪器 - 主程序入口
"""

import os
import sys
import argparse
import json
from typing import List, Dict
import pandas as pd

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from core.detector import SoftwareVersionDetector, SoftwareInfo
from services.version_service import VersionService
from api.rest_api import create_app
from config.settings import load_config
from utils.logger import setup_logging, get_logger


def load_software_from_excel(file_path: str) -> List[SoftwareInfo]:
    """
    从Excel文件加载软件列表
    
    Args:
        file_path: Excel文件路径
        
    Returns:
        List[SoftwareInfo]: 软件信息列表
    """
    try:
        df = pd.read_excel(file_path)
        
        # 检查必要的列
        required_columns = ['软件名称', '官网地址']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise ValueError(f"Excel文件缺少必要的列: {missing_columns}")
        
        software_list = []
        for _, row in df.iterrows():
            software_info = SoftwareInfo(
                name=str(row['软件名称']).strip(),
                url=str(row['官网地址']).strip(),
                strategy_hint=str(row.get('策略提示', '')).strip() if '策略提示' in df.columns else None,
                metadata={
                    'category': str(row.get('分类', '')).strip() if '分类' in df.columns else None,
                    'priority': str(row.get('优先级', '')).strip() if '优先级' in df.columns else None,
                    'description': str(row.get('描述', '')).strip() if '描述' in df.columns else None,
                }
            )
            
            # 跳过空行
            if software_info.name and software_info.url:
                software_list.append(software_info)
        
        return software_list
        
    except Exception as e:
        raise Exception(f"加载Excel文件失败: {str(e)}")


def save_results_to_excel(results: List, output_path: str):
    """
    保存结果到Excel文件
    
    Args:
        results: 检测结果列表
        output_path: 输出文件路径
    """
    try:
        # 转换结果为字典列表
        data = []
        for result in results:
            data.append({
                '软件名称': result.name,
                '版本号': result.version,
                '下载地址': result.download_url,
                '发布日期': result.release_date.strftime('%Y-%m-%d') if result.release_date else '',
                '文件大小': result.file_size or '',
                '检查时间': result.detection_time.strftime('%Y-%m-%d %H:%M:%S') if result.detection_time else '',
                '检测状态': '成功' if result.success else '失败',
                '错误信息': result.error_message or '',
                '使用策略': result.strategy_used or ''
            })
        
        # 创建DataFrame并保存
        df = pd.DataFrame(data)
        df.to_excel(output_path, index=False, engine='openpyxl')
        
        print(f"结果已保存到: {output_path}")
        
    except Exception as e:
        raise Exception(f"保存结果失败: {str(e)}")


def cmd_detect_single(args):
    """命令行：检测单个软件"""
    logger = get_logger(__name__)
    
    try:
        # 加载配置
        config = load_config(args.config)
        
        # 创建检测器
        detector = SoftwareVersionDetector(config)
        
        # 创建软件信息
        software_info = SoftwareInfo(
            name=args.name,
            url=args.url,
            strategy_hint=args.strategy
        )
        
        # 执行检测
        logger.info(f"开始检测: {args.name}")
        result = detector.detect_version(software_info)
        
        # 输出结果
        if result.success:
            print(f"✓ 检测成功")
            print(f"  软件名称: {result.name}")
            print(f"  版本号: {result.version}")
            print(f"  下载地址: {result.download_url}")
            if result.release_date:
                print(f"  发布日期: {result.release_date}")
            if result.file_size:
                print(f"  文件大小: {result.file_size}")
            print(f"  检测时间: {result.detection_time}")
            print(f"  使用策略: {result.strategy_used}")
        else:
            print(f"✗ 检测失败: {result.error_message}")
        
        # 保存结果（如果指定了输出文件）
        if args.output:
            save_results_to_excel([result], args.output)
        
    except Exception as e:
        logger.error(f"检测失败: {str(e)}")
        print(f"错误: {str(e)}")
        sys.exit(1)


def cmd_detect_batch(args):
    """命令行：批量检测"""
    logger = get_logger(__name__)
    
    try:
        # 加载配置
        config = load_config(args.config)
        
        # 创建检测器
        detector = SoftwareVersionDetector(config)
        
        # 加载软件列表
        if args.input.endswith('.xlsx') or args.input.endswith('.xls'):
            software_list = load_software_from_excel(args.input)
        elif args.input.endswith('.json'):
            with open(args.input, 'r', encoding='utf-8') as f:
                data = json.load(f)
                software_list = [SoftwareInfo(**item) for item in data]
        else:
            raise ValueError("不支持的输入文件格式，请使用Excel(.xlsx)或JSON(.json)文件")
        
        logger.info(f"加载了 {len(software_list)} 个软件")
        
        # 执行批量检测
        print(f"开始批量检测 {len(software_list)} 个软件...")
        results = detector.batch_detect(software_list, concurrent=not args.no_concurrent)
        
        # 统计结果
        success_count = sum(1 for r in results if r.success)
        failure_count = len(results) - success_count
        
        print(f"\n检测完成:")
        print(f"  总数: {len(results)}")
        print(f"  成功: {success_count}")
        print(f"  失败: {failure_count}")
        print(f"  成功率: {success_count/len(results)*100:.1f}%")
        
        # 显示失败的软件
        if failure_count > 0 and args.verbose:
            print(f"\n失败的软件:")
            for result in results:
                if not result.success:
                    print(f"  - {result.name}: {result.error_message}")
        
        # 保存结果
        if args.output:
            save_results_to_excel(results, args.output)
        else:
            # 默认输出文件名
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"software_versions_{timestamp}.xlsx"
            save_results_to_excel(results, output_path)
        
    except Exception as e:
        logger.error(f"批量检测失败: {str(e)}")
        print(f"错误: {str(e)}")
        sys.exit(1)


def cmd_start_service(args):
    """命令行：启动服务"""
    logger = get_logger(__name__)
    
    try:
        # 加载配置
        config = load_config(args.config)
        
        # 创建版本服务
        version_service = VersionService(config)
        
        # 如果指定了软件列表文件，加载并注册软件
        if args.software_list:
            if args.software_list.endswith('.xlsx') or args.software_list.endswith('.xls'):
                software_list = load_software_from_excel(args.software_list)
            elif args.software_list.endswith('.json'):
                with open(args.software_list, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    software_list = [SoftwareInfo(**item) for item in data]
            else:
                raise ValueError("不支持的软件列表文件格式")
            
            # 注册软件
            registered_count = version_service.register_software_batch(software_list)
            logger.info(f"注册了 {registered_count} 个软件")
        
        # 启动自动更新调度器
        if args.auto_update:
            version_service.start_auto_update_scheduler()
        
        # 创建并启动API服务
        app = create_app(version_service, config.get('api', {}))
        
        host = args.host or config.get('api', {}).get('host', '0.0.0.0')
        port = args.port or config.get('api', {}).get('port', 8080)
        debug = args.debug or config.get('api', {}).get('debug', False)
        
        print(f"启动Mac软件版本追踪器服务...")
        print(f"API地址: http://{host}:{port}")
        print(f"API文档: http://{host}:{port}/docs")
        print(f"健康检查: http://{host}:{port}/health")
        
        app.run(host=host, port=port, debug=debug)
        
    except Exception as e:
        logger.error(f"启动服务失败: {str(e)}")
        print(f"错误: {str(e)}")
        sys.exit(1)


def cmd_list_strategies(args):
    """命令行：列出可用策略"""
    try:
        config = load_config(args.config)
        detector = SoftwareVersionDetector(config)
        
        supported_software = detector.get_supported_software()
        
        print("可用的检测策略:")
        print("=" * 50)
        
        strategies = {}
        for software in supported_software:
            strategy = software.get('strategy', 'unknown')
            if strategy not in strategies:
                strategies[strategy] = []
            strategies[strategy].append(software)
        
        for strategy_name, software_list in strategies.items():
            print(f"\n{strategy_name}:")
            for software in software_list:
                print(f"  - {software['name']}: {software.get('description', '')}")
        
    except Exception as e:
        print(f"错误: {str(e)}")
        sys.exit(1)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Mac软件版本自动追踪器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 检测单个软件
  python main.py detect-single --name "VS Code" --url "https://code.visualstudio.com"
  
  # 批量检测
  python main.py detect-batch --input software.xlsx --output results.xlsx
  
  # 启动API服务
  python main.py start-service --software-list software.xlsx --auto-update
  
  # 列出可用策略
  python main.py list-strategies
        """
    )
    
    # 全局参数
    parser.add_argument('--config', '-c', default='config/settings.py',
                       help='配置文件路径')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='详细输出')
    parser.add_argument('--log-level', default='INFO',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='日志级别')
    
    # 子命令
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 检测单个软件
    parser_single = subparsers.add_parser('detect-single', help='检测单个软件版本')
    parser_single.add_argument('--name', '-n', required=True, help='软件名称')
    parser_single.add_argument('--url', '-u', required=True, help='软件官网地址')
    parser_single.add_argument('--strategy', '-s', help='指定检测策略')
    parser_single.add_argument('--output', '-o', help='输出文件路径')
    parser_single.set_defaults(func=cmd_detect_single)
    
    # 批量检测
    parser_batch = subparsers.add_parser('detect-batch', help='批量检测软件版本')
    parser_batch.add_argument('--input', '-i', required=True, help='输入文件路径(Excel或JSON)')
    parser_batch.add_argument('--output', '-o', help='输出文件路径')
    parser_batch.add_argument('--no-concurrent', action='store_true', help='禁用并发检测')
    parser_batch.set_defaults(func=cmd_detect_batch)
    
    # 启动服务
    parser_service = subparsers.add_parser('start-service', help='启动API服务')
    parser_service.add_argument('--software-list', help='软件列表文件')
    parser_service.add_argument('--host', default='0.0.0.0', help='服务主机地址')
    parser_service.add_argument('--port', type=int, default=8080, help='服务端口')
    parser_service.add_argument('--auto-update', action='store_true', help='启用自动更新')
    parser_service.add_argument('--debug', action='store_true', help='调试模式')
    parser_service.set_defaults(func=cmd_start_service)
    
    # 列出策略
    parser_strategies = subparsers.add_parser('list-strategies', help='列出可用的检测策略')
    parser_strategies.set_defaults(func=cmd_list_strategies)
    
    # 解析参数
    args = parser.parse_args()
    
    # 设置日志
    setup_logging(level=args.log_level)
    
    # 如果没有指定命令，显示帮助
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # 执行对应的命令
    args.func(args)


if __name__ == "__main__":
    main()