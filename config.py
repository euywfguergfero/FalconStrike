#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FalconStrike - 配置管理
"""

import os
import json
import shutil
import locale
import ctypes
from datetime import datetime
from utils import get_app_dir, print_warning, print_error, print_info

CONFIG_FILE = os.path.join(get_app_dir(), 'data', 'config.json')
HASHES_FILE = os.path.join(get_app_dir(), 'data', 'hashes.json')

DEFAULT_CONFIG = {
    "language": "zh-CN",  # 默认值，会被自动检测覆盖
    "cloud": {
        "auto_sync": True,
        "sync_url": "https://raw.githubusercontent.com/yourname/falconstrike-samples/main",
        "last_sync": None
    },
    "realtime": {
        "enabled": True,
        "file_monitor": True,
        "process_monitor": True,
        "registry_monitor": True,
        "network_monitor": True,
        "excluded_paths": [],
        "excluded_processes": ["explorer.exe", "svchost.exe", "lsass.exe"],
        "excluded_extensions": [".tmp", ".log"]
    },
    "scan": {
        "threads": 4,
        "max_file_size_mb": 100,
        "scan_directories": [
            "C:\\Users\\Public",
            "C:\\ProgramData",
            "C:\\Windows\\Temp",
            "C:\\Users\\*\\Desktop",
            "C:\\Users\\*\\Downloads"
        ],
        "skip_extensions": [".tmp", ".log", ".bak"]
    },
    "defender": {
        "takeover": False
    },
    "report": {
        "output_dir": "./reports",
        "format": "json"
    },
    "logging": {
        "level": "info",
        "file": "./logs/FS.log"
    }
}

DEFAULT_HASHES = {
    "5d41402abc4b2a76b9719d911017c592": {
        "description": "Test sample (hello)",
        "family": "Test",
        "severity": "low"
    },
    "098f6bcd4621d373cade4e832627b4f6": {
        "description": "SilverFox WinOS v2.3",
        "family": "SilverFox",
        "severity": "critical"
    }
}


def detect_system_language():
    """
    检测 Windows 系统语言，返回语言代码
    支持: zh-CN, zh-TW, en-US, ja-JP, ko-KR, fr-FR, de-DE, es-ES
    """
    try:
        windll = ctypes.windll.kernel32
        lang_id = windll.GetUserDefaultUILanguage()
        # 语言 ID 映射
        lang_map = {
            0x0804: "zh-CN",  # 简体中文
            0x0404: "zh-TW",  # 繁体中文
            0x0409: "en-US",  # 英语（美国）
            0x0411: "ja-JP",  # 日语
            0x0412: "ko-KR",  # 韩语
            0x040C: "fr-FR",  # 法语（法国）
            0x0407: "de-DE",  # 德语（德国）
            0x040A: "es-ES",  # 西班牙语（西班牙）
            # 可以继续添加更多
        }
        return lang_map.get(lang_id, "en-US")
    except:
        # 如果 Windows API 失败，使用 locale 模块
        try:
            loc = locale.getdefaultlocale()[0]
            if loc:
                if loc.startswith('zh_CN'):
                    return "zh-CN"
                elif loc.startswith('zh_TW'):
                    return "zh-TW"
                elif loc.startswith('ja'):
                    return "ja-JP"
                elif loc.startswith('ko'):
                    return "ko-KR"
                elif loc.startswith('fr'):
                    return "fr-FR"
                elif loc.startswith('de'):
                    return "de-DE"
                elif loc.startswith('es'):
                    return "es-ES"
                elif loc.startswith('en'):
                    return "en-US"
        except:
            pass
        return "en-US"  # 默认英语

def get_available_languages():
    """扫描 locales 目录，返回可用语言代码列表"""
    locales_dir = os.path.join(get_app_dir(), 'locales')
    if not os.path.exists(locales_dir):
        return ["zh-CN", "zh-TW", "en-US"]  # 如果目录不存在，返回默认
    files = [f for f in os.listdir(locales_dir) if f.endswith('.json')]
    langs = [f[:-5] for f in files]
    if not langs:
        return ["zh-CN", "zh-TW", "en-US"]
    return langs


def ensure_data_dir():
    """确保 data 目录存在"""
    data_dir = os.path.dirname(CONFIG_FILE)
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)


def safe_load_json(filepath, default_data, description="Config"):
    """安全加载 JSON 文件，损坏时自动重建"""
    if not os.path.exists(filepath):
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(default_data, f, indent=4, ensure_ascii=False)
            print_info(f"  Created default {description}: {filepath}")
            return default_data
        except Exception as e:
            print_error(f"  Failed to create {description}: {e}")
            return default_data

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        backup_path = filepath + f".corrupted_{datetime.now().strftime('%Y%m%d_%H%M%S')}.bak"
        try:
            shutil.copy2(filepath, backup_path)
            print_warning(f"  {description} corrupted, backed up to: {backup_path}")
        except Exception:
            pass

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(default_data, f, indent=4, ensure_ascii=False)
            print_info(f"  Rebuilt {description}: {filepath}")
            return default_data
        except Exception as e2:
            print_error(f"  Failed to rebuild {description}: {e2}")
            return default_data
    except Exception as e:
        print_error(f"  Failed to load {description}: {e}")
        return default_data


def load_config():
    """加载配置文件，如果 language 字段未设置则自动检测"""
    ensure_data_dir()
    config = safe_load_json(CONFIG_FILE, DEFAULT_CONFIG, "Config")

    # 如果 language 未设置或为空，则自动检测并保存
    if not config.get("language") or config["language"] not in get_available_languages():
        detected = detect_system_language()
        # 确保检测到的语言在可用列表中，否则 fallback
        if detected not in get_available_languages():
            detected = "zh-CN"
        config["language"] = detected
        save_config(config)
        print_info(f"  Auto-detected system language: {detected}")
    return config


def save_config(config):
    """保存配置文件"""
    ensure_data_dir()
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print_error(f"  Failed to save config: {e}")
        return False


def load_hashes():
    """加载恶意哈希库"""
    ensure_data_dir()
    return safe_load_json(HASHES_FILE, DEFAULT_HASHES, "Hash DB")


def save_hashes(hashes):
    """保存恶意哈希库"""
    ensure_data_dir()
    try:
        with open(HASHES_FILE, 'w', encoding='utf-8') as f:
            json.dump(hashes, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print_error(f"  Failed to save hash DB: {e}")
        return False