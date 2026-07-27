#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FalconStrike - 云端样本库同步模块（HTTP极速版，带重试）
数据源: CYB3RMX/MalwareHashDB
"""

import os
import json
import sqlite3
import requests
import zipfile
import shutil
import time
from datetime import datetime
from utils import print_info, print_success, print_warning, print_error, get_app_dir

# 配置
REPO_ZIP_URL = "https://github.com/CYB3RMX/MalwareHashDB/archive/refs/heads/main.zip"
PROXY_URLS = [
    "https://mirrors.aliyun.com",
    "https://pypi.tuna.tsinghua.edu.cn/simple",
    "https://gh.api.99988866.xyz/"
]
DOWNLOAD_URLS = [REPO_ZIP_URL] + [proxy + REPO_ZIP_URL for proxy in PROXY_URLS]

REPO_DIR = os.path.join(get_app_dir(), 'data', 'malware_hash_db')
ZIP_PATH = os.path.join(get_app_dir(), 'data', 'malware_hash_db.zip')
HASHES_FILE = os.path.join(get_app_dir(), 'data', 'hashes.json')
VERSION_FILE = os.path.join(get_app_dir(), 'data', 'cloud_version.json')


def download_with_progress(url, dest, max_retries=2):
    """带进度条的下载，支持重试"""
    for attempt in range(max_retries + 1):
        try:
            print_info(f"  Downloading from: {url} (attempt {attempt+1}/{max_retries+1})")
            response = requests.get(url, stream=True, timeout=(10, 120), verify=False)
            if response.status_code != 200:
                print_warning(f"  HTTP {response.status_code}, retrying...")
                time.sleep(2)
                continue

            total_size = int(response.headers.get('content-length', 0))
            block_size = 8192
            downloaded = 0

            with open(dest, 'wb') as f:
                for chunk in response.iter_content(chunk_size=block_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            print(f"\r  Downloading: {percent:.1f}% ({downloaded // 1024} KB / {total_size // 1024} KB)", end='')
            print("")  # 换行
            return True
        except requests.exceptions.Timeout:
            print_warning(f"  Timeout, retrying... ({attempt+1}/{max_retries+1})")
            time.sleep(3)
        except Exception as e:
            print_warning(f"  Download error: {e}, retrying...")
            time.sleep(3)
    return False


def download_database(force=False):
    """尝试多个URL下载数据库"""
    db_path = os.path.join(REPO_DIR, 'HashDB')
    if os.path.exists(db_path) and not force:
        print_info("  Local database already exists. Use --force to re-download.")
        return True

    if not os.path.exists(REPO_DIR):
        os.makedirs(REPO_DIR)

    # 依次尝试每个URL
    for url in DOWNLOAD_URLS:
        print_info(f"  Attempting to download from: {url}")
        if download_with_progress(url, ZIP_PATH):
            # 下载成功，解压
            print_info("  Extracting database...")
            if extract_zip(ZIP_PATH, REPO_DIR):
                os.remove(ZIP_PATH)
                print_success("  Database extracted successfully.")
                return True
            else:
                print_warning("  Extraction failed, trying next source...")
                continue
        else:
            print_warning("  Download failed, trying next source...")
            continue

    print_error("  All download sources failed.")
    return False


def extract_zip(zip_path, extract_to):
    """解压ZIP文件，提取HashDB"""
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            file_list = zip_ref.namelist()
            for f in file_list:
                if f.endswith('HashDB'):
                    zip_ref.extract(f, os.path.dirname(extract_to))
                    src = os.path.join(os.path.dirname(extract_to), f)
                    dst = os.path.join(extract_to, 'HashDB')
                    if os.path.exists(dst):
                        os.remove(dst)
                    shutil.move(src, dst)
                    return True
        return False
    except Exception as e:
        print_error(f"  Extract error: {e}")
        return False


def parse_hash_files():
    """解析SQLite数据库，提取所有哈希"""
    db_path = os.path.join(REPO_DIR, 'HashDB')
    if not os.path.exists(db_path):
        print_warning("  HashDB file not found.")
        return False, 0

    merged_hashes = {}
    if os.path.exists(HASHES_FILE):
        try:
            with open(HASHES_FILE, 'r', encoding='utf-8') as f:
                merged_hashes = json.load(f)
        except:
            pass

    hash_count = 0
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='HashDB'")
        if not cursor.fetchone():
            print_error("  Table 'HashDB' not found.")
            conn.close()
            return False, 0

        cursor.execute("SELECT hash, name FROM HashDB")
        rows = cursor.fetchall()
        conn.close()

        for hash_val, name in rows:
            if hash_val and len(hash_val) == 32:
                hash_lower = hash_val.lower()
                merged_hashes[hash_lower] = {
                    "description": name or "MalwareHashDB entry",
                    "source": "CYB3RMX/MalwareHashDB"
                }
                hash_count += 1

        with open(HASHES_FILE, 'w', encoding='utf-8') as f:
            json.dump(merged_hashes, f, indent=2, ensure_ascii=False)

        return True, hash_count
    except sqlite3.Error as e:
        print_error(f"  SQLite error: {e}")
        return False, 0
    except Exception as e:
        print_error(f"  Failed to parse: {e}")
        return False, 0


def sync_from_malware_hash_db(force=False):
    """同步样本库"""
    if not download_database(force):
        print_error("  Failed to download database. Please check network.")
        return False, 0, 0

    success, count = parse_hash_files()
    if success:
        total = get_local_sample_count()
        print_success(f"  Synced {count} hashes from MalwareHashDB.")
        print_info(f"  Total samples in database: {total}")
        return True, count, total
    else:
        return False, 0, 0


# ========== 对外接口 ==========

def get_local_sample_count():
    if not os.path.exists(HASHES_FILE):
        return 0
    try:
        with open(HASHES_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return len(data)
    except:
        return 0

def sync_cloud_samples(force=False):
    return sync_from_malware_hash_db(force)

def get_local_version():
    if not os.path.exists(VERSION_FILE):
        return "0.0.0"
    try:
        with open(VERSION_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get("version", "0.0.0")
    except:
        return "0.0.0"

def save_local_version(version, count):
    try:
        with open(VERSION_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                "version": version,
                "count": count,
                "updated_at": datetime.now().isoformat()
            }, f, indent=2)
        return True
    except:
        return False