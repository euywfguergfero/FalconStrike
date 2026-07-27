#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FalconStrike - 信用区管理模块
"""

import os
from utils import print_info, print_success, print_warning, print_error
from config import load_config, save_config


def get_trust_zone():
    """获取信用区列表"""
    config = load_config()
    return config.get("trust_zone", {}).get("paths", [])


def save_trust_zone(paths):
    """保存信用区列表"""
    config = load_config()
    if "trust_zone" not in config:
        config["trust_zone"] = {}
    config["trust_zone"]["paths"] = paths
    save_config(config)


def add_to_trust_zone(path):
    """添加路径到信用区"""
    if not os.path.exists(path):
        return False, "Path does not exist"

    trust_list = get_trust_zone()
    if path in trust_list:
        return False, "Path already in trust zone"

    trust_list.append(path)
    save_trust_zone(trust_list)
    return True, "Added successfully"


def remove_from_trust_zone(path):
    """从信用区移除路径"""
    trust_list = get_trust_zone()
    if path not in trust_list:
        return False, "Path not in trust zone"

    trust_list.remove(path)
    save_trust_zone(trust_list)
    return True, "Removed successfully"


def clear_trust_zone():
    """清空信用区"""
    save_trust_zone([])
    return True, "Trust zone cleared"


def is_trusted(path):
    """检查路径是否在信用区中"""
    if not path:
        return False
    trust_list = get_trust_zone()
    path_lower = path.lower()
    for trusted in trust_list:
        if path_lower.startswith(trusted.lower()):
            return True
    return False