#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FalconStrike - 工具函数
"""

import os
import sys
from colorama import Fore, Style, init

# 初始化 colorama（Windows 兼容）
init(autoreset=True)


def clear_screen():
    """清屏"""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_color(text, color=Fore.WHITE, bold=False, end='\n'):
    """彩色打印"""
    style = Style.BRIGHT if bold else ''
    print(f"{style}{color}{text}{Style.RESET_ALL}", end=end)


def print_header(text):
    """打印标题（蓝色加粗）"""
    print_color(f"\n  {text}", Fore.CYAN, bold=True)


def print_success(text):
    """打印成功信息（绿色）"""
    print_color(f"  [OK] {text}", Fore.GREEN)


def print_warning(text):
    """打印警告信息（黄色）"""
    print_color(f"  [!] {text}", Fore.YELLOW)


def print_error(text):
    """打印错误信息（红色）"""
    print_color(f"  [X] {text}", Fore.RED)


def print_info(text):
    """打印普通信息（白色）"""
    print_color(f"  [*] {text}", Fore.WHITE)


def wait_for_enter(prompt="  Press Enter to return to menu..."):
    """等待用户按回车"""
    input(Fore.WHITE + prompt)


def is_admin():
    """检查是否以管理员权限运行"""
    try:
        return os.getuid() == 0
    except AttributeError:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0


def get_app_dir():
    """获取程序所在目录"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))