#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
创建示例Excel文件
"""

import pandas as pd

# 示例软件数据
software_data = [
    {
        '软件名称': 'Chrome',
        '官网地址': 'https://www.google.com/chrome/',
        '分类': '浏览器',
        '优先级': '高',
        '描述': 'Google Chrome浏览器',
        '策略提示': 'chrome'
    },
    {
        '软件名称': 'Firefox',
        '官网地址': 'https://www.mozilla.org/firefox/',
        '分类': '浏览器',
        '优先级': '高',
        '描述': 'Mozilla Firefox浏览器',
        '策略提示': 'firefox'
    },
    {
        '软件名称': 'VS Code',
        '官网地址': 'https://code.visualstudio.com',
        '分类': '开发工具',
        '优先级': '高',
        '描述': 'Visual Studio Code编辑器',
        '策略提示': 'vscode'
    },
    {
        '软件名称': 'PyCharm',
        '官网地址': 'https://www.jetbrains.com/pycharm/',
        '分类': '开发工具',
        '优先级': '中',
        '描述': 'JetBrains PyCharm IDE',
        '策略提示': 'jetbrains'
    },
    {
        '软件名称': 'IntelliJ IDEA',
        '官网地址': 'https://www.jetbrains.com/idea/',
        '分类': '开发工具',
        '优先级': '中',
        '描述': 'JetBrains IntelliJ IDEA',
        '策略提示': 'jetbrains'
    },
    {
        '软件名称': 'Photoshop',
        '官网地址': 'https://www.adobe.com/products/photoshop.html',
        '分类': '设计工具',
        '优先级': '中',
        '描述': 'Adobe Photoshop',
        '策略提示': 'adobe'
    },
    {
        '软件名称': 'Illustrator',
        '官网地址': 'https://www.adobe.com/products/illustrator.html',
        '分类': '设计工具',
        '优先级': '中',
        '描述': 'Adobe Illustrator',
        '策略提示': 'adobe'
    },
    {
        '软件名称': 'Zoom',
        '官网地址': 'https://zoom.us',
        '分类': '通讯工具',
        '优先级': '高',
        '描述': 'Zoom视频会议',
        '策略提示': 'zoom'
    },
    {
        '软件名称': 'Microsoft Office',
        '官网地址': 'https://www.microsoft.com/microsoft-365',
        '分类': '办公软件',
        '优先级': '高',
        '描述': 'Microsoft Office套件',
        '策略提示': 'microsoft'
    },
    {
        '软件名称': 'Homebrew',
        '官网地址': 'https://github.com/Homebrew/brew',
        '分类': '系统工具',
        '优先级': '中',
        '描述': 'macOS包管理器',
        '策略提示': 'github'
    },
    {
        '软件名称': 'Docker Desktop',
        '官网地址': 'https://www.docker.com/products/docker-desktop',
        '分类': '开发工具',
        '优先级': '中',
        '描述': 'Docker桌面版',
        '策略提示': ''
    },
    {
        '软件名称': 'Notion',
        '官网地址': 'https://www.notion.so',
        '分类': '效率工具',
        '优先级': '中',
        '描述': 'Notion笔记应用',
        '策略提示': ''
    },
    {
        '软件名称': 'Slack',
        '官网地址': 'https://slack.com',
        '分类': '通讯工具',
        '优先级': '中',
        '描述': 'Slack团队协作',
        '策略提示': ''
    },
    {
        '软件名称': 'Spotify',
        '官网地址': 'https://www.spotify.com',
        '分类': '娱乐软件',
        '优先级': '低',
        '描述': 'Spotify音乐',
        '策略提示': ''
    },
    {
        '软件名称': 'VLC',
        '官网地址': 'https://www.videolan.org/vlc/',
        '分类': '媒体播放',
        '优先级': '中',
        '描述': 'VLC媒体播放器',
        '策略提示': ''
    }
]

# 创建DataFrame
df = pd.DataFrame(software_data)

# 保存为Excel文件
df.to_excel('example_software.xlsx', index=False, engine='openpyxl')

print("示例Excel文件已创建: example_software.xlsx")
print(f"包含 {len(software_data)} 个软件")