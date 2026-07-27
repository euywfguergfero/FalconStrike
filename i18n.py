#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FalconStrike - 国际化（i18n）支持
"""

import os
import json
from utils import get_app_dir

LOCALES_DIR = os.path.join(get_app_dir(), 'locales')
DEFAULT_LANG = 'zh-CN'

# 全局语言包
LANG = {}


def load_language(lang_code):
    """加载指定语言包，出错时返回空字典"""
    lang_file = os.path.join(LOCALES_DIR, f"{lang_code}.json")
    try:
        with open(lang_file, 'r', encoding='utf-8') as f:
            content = f.read()
            # 去除可能的 BOM
            if content.startswith('\ufeff'):
                content = content[1:]
            return json.loads(content)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"[WARN] Failed to load language '{lang_code}': {e}")
        # 尝试加载默认语言
        if lang_code != DEFAULT_LANG:
            return load_language(DEFAULT_LANG)
        return {}


def init_i18n(lang_code):
    """初始化全局语言包"""
    global LANG
    loaded = load_language(lang_code)
    if loaded:
        LANG.clear()
        LANG.update(loaded)
    else:
        print("[ERROR] No valid language pack found. Using built-in fallback keys.")
        # 提供一个最小的 fallback
        LANG.update({
            "app_name": "FalconStrike",
            "subtitle": "Security Tool",
            "url": "",
            "realtime_status": "Real-time Protection",
            "enabled_symbol": "[*]",
            "disabled_symbol": "[ ]",
            "blocks_label": "Blocks",
            "quarantined_label": "Quarantined",
            "samples_label": "Samples",
            "menu": {
                "1": "Quick Scan",
                "2": "Deep Scan",
                "3": "Full Scan",
                "4": "View Report",
                "5": "Real-time Protection",
                "6": "Quarantine Manager",
                "7": "Takeover Defender",
                "8": "Cleanup Mode",
                "9": "Settings",
                "10": "Trust Zone",
                "0": "Exit"
            },
            "prompt": "Select function (number)",
            "exit": "Exiting",
            "invalid": "Invalid input",
            "admin_warning": "Run as Admin recommended.",
            "config_loaded": "Config loaded, %d rules.",
            "config_failed": "Config failed: %s",
            "interrupted": "Interrupted.",
            "press_enter": "Press Enter to return...",
            "placeholder": "(Placeholder)",
            "scanning": "Scanning...",
            "quick_scan": "Quick Scan",
            "deep_scan": "Deep Scan",
            "full_scan": "Full Scan",
            "settings_title": "Settings",
            "settings.update_samples": "Update Samples",
            "settings.view_config": "View Config",
            "settings.back": "Back",
            "settings.syncing": "Syncing...",
            "settings.sync_already_latest": "Already latest.",
            "settings.sync_success": "Updated! Added %d, total %d.",
            "settings.sync_failed": "Sync failed.",
            "quarantine": {
                "title": "Quarantine",
                "empty": "Empty.",
                "count": "%d files.",
                "restore": "Restore",
                "delete": "Delete",
                "clean_orphans": "Clean Orphans"
            },
            "trust_zone": {
                "title": "Trust Zone",
                "empty": "Empty.",
                "count": "%d paths.",
                "add": "Add",
                "remove": "Remove",
                "clear": "Clear"
            },
            "realtime": {
                "title": "Real-time Protection",
                "status_running": "Running",
                "status_stopped": "Stopped",
                "start": "Start",
                "stop": "Stop"
            },
            "defender": {
                "title": "Takeover Defender",
                "takeover": "Takeover",
                "restore": "Restore"
            }
        })


def t(key, *args):
    """
    翻译函数
    用法: t("menu.1") -> "快速扫描"
          t("config_loaded", 10) -> "配置加载成功，已加载 10 条哈希规则。"
    """
    keys = key.split('.')
    value = LANG
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            # 如果 key 不存在，返回 key 本身
            return key
    if args and isinstance(value, str):
        try:
            return value % args
        except TypeError:
            return value
    return value