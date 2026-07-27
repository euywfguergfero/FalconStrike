#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FalconStrike - 扫描引擎（多线程优化版，集成信用区）
"""

import os
import psutil
import hashlib
import winreg
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from utils import print_info, print_success, print_warning, print_error
from config import load_hashes, load_config
from trust_zone import is_trusted


class ScanResult:
    """扫描结果条目"""
    def __init__(self, type_, path, reason, severity="medium", extra=None):
        self.type = type_
        self.path = path
        self.reason = reason
        self.severity = severity
        self.extra = extra or {}
        self.timestamp = datetime.now().isoformat()

    def to_dict(self):
        return {
            "type": self.type,
            "path": self.path,
            "reason": self.reason,
            "severity": self.severity,
            "extra": self.extra,
            "timestamp": self.timestamp
        }


# 白名单路径（末尾不带反斜杠）
WHITELIST_PATHS = [
    r"C:\Windows",
    r"C:\Program Files",
    r"C:\Program Files (x86)",
    r"C:\ProgramData\Microsoft\Windows Defender",
]


def is_whitelisted(path):
    """检查路径是否在白名单中"""
    path_lower = path.lower()
    for wl in WHITELIST_PATHS:
        if path_lower.startswith(wl.lower()):
            return True
    return False


def scan_processes():
    """扫描所有进程（增加信用区和白名单过滤）"""
    results = []
    hashes = load_hashes()
    suspicious_dirs = [
        r"C:\Users\Public",
        r"C:\ProgramData",
        os.environ.get("TEMP", ""),
        os.environ.get("APPDATA", ""),
        os.environ.get("LOCALAPPDATA", "")
    ]
    suspicious_dirs = [d for d in suspicious_dirs if d]

    print_info("Scanning processes...")
    for proc in psutil.process_iter(['pid', 'name', 'exe', 'cmdline']):
        try:
            exe = proc.info['exe']
            if not exe or not os.path.exists(exe):
                continue
            # 信用区优先跳过
            if is_trusted(exe):
                continue
            if is_whitelisted(exe):
                continue

            # 哈希匹配
            try:
                with open(exe, 'rb') as f:
                    file_hash = hashlib.md5(f.read()).hexdigest()
                if file_hash in hashes:
                    desc = hashes[file_hash]
                    if isinstance(desc, dict):
                        desc = desc.get("description", "Malicious file")
                    results.append(ScanResult(
                        "process", exe,
                        f"Malicious hash: {desc} (MD5: {file_hash})",
                        "critical"
                    ))
                    continue
            except:
                pass

            # 可疑目录检查
            is_system = exe.lower().startswith(r"c:\windows")
            if not is_system:
                in_suspicious = any(exe.lower().startswith(d.lower()) for d in suspicious_dirs if d)
                if in_suspicious:
                    results.append(ScanResult(
                        "process", exe,
                        f"Running from suspicious dir: {os.path.dirname(exe)}",
                        "high"
                    ))
                    continue

            # 高危端口
            try:
                for conn in proc.net_connections(kind='inet'):
                    if conn.raddr and conn.raddr.port in [4444, 5555, 1337, 8080, 8888, 6666]:
                        results.append(ScanResult(
                            "process", exe,
                            f"Outbound to port {conn.raddr.port} (C2)",
                            "high",
                            {"remote": f"{conn.raddr.ip}:{conn.raddr.port}"}
                        ))
                        break
            except:
                pass
        except:
            continue
    return results


def scan_startups():
    """扫描注册表启动项（增加信用区和白名单）"""
    results = []
    hashes = load_hashes()
    run_paths = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Run"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"),
    ]

    print_info("Scanning startup entries...")
    for hive, path in run_paths:
        try:
            key = winreg.OpenKey(hive, path, 0, winreg.KEY_READ)
            i = 0
            while True:
                try:
                    name, value, _ = winreg.EnumValue(key, i)
                    if os.path.exists(value):
                        if is_trusted(value) or is_whitelisted(value):
                            i += 1
                            continue
                        # 哈希匹配
                        try:
                            with open(value, 'rb') as f:
                                file_hash = hashlib.md5(f.read()).hexdigest()
                            if file_hash in hashes:
                                desc = hashes[file_hash]
                                if isinstance(desc, dict):
                                    desc = desc.get("description", "Malicious")
                                results.append(ScanResult(
                                    "startup", value,
                                    f"Hash match: {desc} (MD5: {file_hash})",
                                    "critical",
                                    {"reg": f"{path}\\{name}"}
                                ))
                                i += 1
                                continue
                        except:
                            pass
                        # 可疑目录
                        suspicious_dirs = [r"C:\Users\Public", r"C:\ProgramData"]
                        if any(value.lower().startswith(d.lower()) for d in suspicious_dirs):
                            results.append(ScanResult(
                                "startup", value,
                                f"Startup from suspicious dir: {os.path.dirname(value)}",
                                "high",
                                {"reg": f"{path}\\{name}"}
                            ))
                    i += 1
                except OSError:
                    break
            winreg.CloseKey(key)
        except:
            pass
    return results


def scan_services():
    """扫描服务（增加信用区和白名单）"""
    results = []
    hashes = load_hashes()
    print_info("Scanning services...")
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services", 0, winreg.KEY_READ)
        i = 0
        while True:
            try:
                svc = winreg.EnumKey(key, i)
                sk = winreg.OpenKey(key, svc, 0, winreg.KEY_READ)
                try:
                    image_path, _ = winreg.QueryValueEx(sk, "ImagePath")
                    exe = image_path.strip('"')
                    if exe and os.path.exists(exe):
                        if is_trusted(exe) or is_whitelisted(exe):
                            winreg.CloseKey(sk)
                            i += 1
                            continue
                        try:
                            with open(exe, 'rb') as f:
                                file_hash = hashlib.md5(f.read()).hexdigest()
                            if file_hash in hashes:
                                desc = hashes[file_hash]
                                if isinstance(desc, dict):
                                    desc = desc.get("description", "Malicious")
                                results.append(ScanResult(
                                    "service", exe,
                                    f"Hash match: {desc} (MD5: {file_hash})",
                                    "critical",
                                    {"service": svc}
                                ))
                        except:
                            pass
                except:
                    pass
                winreg.CloseKey(sk)
                i += 1
            except OSError:
                break
        winreg.CloseKey(key)
    except:
        pass
    return results


def scan_files_multithreaded(directories):
    """多线程文件扫描，集成信用区检查"""
    results = []
    hashes = load_hashes()
    config = load_config()
    max_size_mb = config.get("scan", {}).get("max_file_size_mb", 100)
    max_size_bytes = max_size_mb * 1024 * 1024
    skip_exts = set(config.get("scan", {}).get("skip_extensions", [".tmp", ".log", ".bak"]))
    exec_exts = {'.exe', '.dll', '.scr', '.ocx', '.sys', '.msi', '.com', '.pif', '.bat', '.cmd', '.vbs', '.ps1', '.js', '.jar'}

    file_list = []
    for root_dir in directories:
        if not os.path.exists(root_dir):
            continue
        for root, _, files in os.walk(root_dir):
            # 跳过系统目录
            if any(part in root.lower() for part in ['$recycle.bin', 'system volume information', 'windows\\winsxs']):
                continue
            for f in files:
                full = os.path.join(root, f)
                # 信用区跳过
                if is_trusted(full):
                    continue
                ext = os.path.splitext(f)[1].lower()
                if ext in skip_exts:
                    continue
                if ext not in exec_exts:
                    continue
                try:
                    size = os.path.getsize(full)
                    if size > max_size_bytes or size == 0:
                        continue
                except:
                    continue
                file_list.append(full)

    print_info(f"Found {len(file_list)} files to scan (multi-threaded)...")
    found_results = []
    with ThreadPoolExecutor(max_workers=config.get("scan", {}).get("threads", 4)) as executor:
        future_to_path = {executor.submit(scan_single_file, path, hashes): path for path in file_list}
        completed = 0
        total = len(file_list)
        for future in as_completed(future_to_path):
            completed += 1
            if completed % 100 == 0 or completed == total:
                print(f"\r  Progress: {completed}/{total} files", end='')
            # 小睡防止 CPU 过热（每 50 个文件休息 0.05 秒）
            if completed % 50 == 0:
                time.sleep(0.05)
            try:
                result = future.result()
                if result:
                    found_results.append(result)
            except:
                pass
    print()
    return found_results


def scan_single_file(file_path, hashes):
    """单文件扫描函数"""
    try:
        with open(file_path, 'rb') as f:
            file_hash = hashlib.md5(f.read()).hexdigest()
        if file_hash in hashes:
            desc = hashes[file_hash]
            if isinstance(desc, dict):
                desc = desc.get("description", "Malicious file")
            return ScanResult(
                "file", file_path,
                f"Hash match: {desc} (MD5: {file_hash})",
                "critical"
            )
    except:
        pass
    return None


def quick_scan():
    """快速扫描（进程+启动项+服务）"""
    results = []
    results.extend(scan_processes())
    results.extend(scan_startups())
    results.extend(scan_services())
    return results


def deep_scan():
    """深度扫描：快速扫描 + 文件哈希（默认目录）"""
    results = quick_scan()
    config = load_config()
    dirs = config.get("scan", {}).get("scan_directories", [
        r"C:\Users\Public",
        r"C:\ProgramData",
        r"C:\Windows\Temp",
        r"C:\Users\*\Desktop",
        r"C:\Users\*\Downloads"
    ])
    expanded_dirs = []
    for d in dirs:
        if "*" in d:
            base = d.split("*")[0]
            if os.path.exists(base):
                for user_dir in os.listdir(base):
                    full = os.path.join(base, user_dir, d.split("*")[1].lstrip('\\'))
                    if os.path.exists(full):
                        expanded_dirs.append(full)
        else:
            if os.path.exists(d):
                expanded_dirs.append(d)
    results.extend(scan_files_multithreaded(expanded_dirs))
    return results


def full_scan():
    """全盘扫描：所有磁盘分区（只扫描可执行文件）"""
    drives = []
    for d in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        if os.path.exists(f"{d}:\\"):
            drives.append(f"{d}:\\")

    dirs_to_scan = []
    for drive in drives:
        dirs_to_scan.append(os.path.join(drive, "Users"))
        dirs_to_scan.append(os.path.join(drive, "ProgramData"))

    results = quick_scan()
    results.extend(scan_files_multithreaded(dirs_to_scan))
    return results