#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FalconStrike - 隔离区管理模块
"""

import os
import json
import shutil
import hashlib
from datetime import datetime
from utils import get_app_dir, print_info, print_success, print_warning, print_error

QUARANTINE_DIR = os.path.join(get_app_dir(), 'quarantine')
METADATA_FILE = os.path.join(QUARANTINE_DIR, 'quarantine_metadata.json')


def ensure_quarantine_dir():
    """确保隔离区目录存在"""
    if not os.path.exists(QUARANTINE_DIR):
        os.makedirs(QUARANTINE_DIR)


def load_metadata():
    """加载隔离区元数据"""
    ensure_quarantine_dir()
    if not os.path.exists(METADATA_FILE):
        return {}
    try:
        with open(METADATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}


def save_metadata(metadata):
    """保存隔离区元数据"""
    ensure_quarantine_dir()
    with open(METADATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)


def quarantine_file(file_path, reason="Quarantined by user"):
    """
    将文件移至隔离区
    返回: (是否成功, 隔离后的路径, 错误信息)
    """
    if not os.path.exists(file_path):
        return False, None, "File does not exist"

    ensure_quarantine_dir()

    # 计算文件哈希
    try:
        with open(file_path, 'rb') as f:
            file_hash = hashlib.md5(f.read()).hexdigest()
    except Exception as e:
        return False, None, f"Failed to hash file: {e}"

    # 生成隔离文件名（原文件名 + 时间戳 + 哈希）
    base_name = os.path.basename(file_path)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    quarantined_name = f"{base_name}.{timestamp}.{file_hash[:8]}.quar"
    quarantined_path = os.path.join(QUARANTINE_DIR, quarantined_name)

    # 移动文件
    try:
        shutil.move(file_path, quarantined_path)
    except Exception as e:
        return False, None, f"Failed to move file: {e}"

    # 记录元数据
    metadata = load_metadata()
    metadata[quarantined_path] = {
        "original_path": file_path,
        "quarantined_path": quarantined_path,
        "timestamp": datetime.now().isoformat(),
        "file_hash": file_hash,
        "file_size": os.path.getsize(quarantined_path),
        "reason": reason
    }
    save_metadata(metadata)

    return True, quarantined_path, None


def restore_file(quarantined_path):
    """
    从隔离区恢复文件
    返回: (是否成功, 错误信息)
    """
    if not os.path.exists(quarantined_path):
        return False, "Quarantined file not found"

    metadata = load_metadata()
    if quarantined_path not in metadata:
        return False, "Metadata not found for this file"

    original_path = metadata[quarantined_path]["original_path"]

    # 检查原路径是否已被占用
    if os.path.exists(original_path):
        # 如果原路径存在，生成一个新名称
        base, ext = os.path.splitext(original_path)
        counter = 1
        while True:
            new_path = f"{base}_restored_{counter}{ext}"
            if not os.path.exists(new_path):
                original_path = new_path
                break
            counter += 1

    try:
        shutil.move(quarantined_path, original_path)
    except Exception as e:
        return False, f"Failed to restore: {e}"

    # 删除元数据
    del metadata[quarantined_path]
    save_metadata(metadata)

    return True, None


def delete_permanently(quarantined_path):
    """
    彻底删除隔离区文件
    返回: (是否成功, 错误信息)
    """
    if not os.path.exists(quarantined_path):
        return False, "File not found"

    try:
        os.remove(quarantined_path)
    except Exception as e:
        return False, f"Failed to delete: {e}"

    metadata = load_metadata()
    if quarantined_path in metadata:
        del metadata[quarantined_path]
        save_metadata(metadata)

    return True, None


def get_quarantine_list():
    """获取隔离区文件列表"""
    metadata = load_metadata()
    result = []
    for path, info in metadata.items():
        if os.path.exists(path):
            result.append({
                "quarantined_path": path,
                "original_path": info.get("original_path", "unknown"),
                "timestamp": info.get("timestamp", "unknown"),
                "file_hash": info.get("file_hash", "unknown"),
                "file_size": info.get("file_size", 0),
                "reason": info.get("reason", "No reason")
            })
        else:
            # 文件已被手动删除，清理元数据
            # 这里不删除，留待用户手动清理
            pass
    return result


def clean_orphaned_metadata():
    """清理孤立元数据（文件已不存在）"""
    metadata = load_metadata()
    to_delete = []
    for path in metadata:
        if not os.path.exists(path):
            to_delete.append(path)
    for path in to_delete:
        del metadata[path]
    if to_delete:
        save_metadata(metadata)
    return len(to_delete)