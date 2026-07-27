#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FalconStrike - 报告生成和查看模块
"""

import os
import json
from datetime import datetime
from utils import get_app_dir, print_info, print_color, print_success, print_warning, print_error

REPORTS_DIR = os.path.join(get_app_dir(), 'reports')


def ensure_reports_dir():
    if not os.path.exists(REPORTS_DIR):
        os.makedirs(REPORTS_DIR)


def generate_report(results, scan_type="Quick"):
    """生成扫描报告并保存为 JSON 文件"""
    ensure_reports_dir()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"scan_{scan_type}_{timestamp}.json"
    filepath = os.path.join(REPORTS_DIR, filename)

    report_data = {
        "scan_type": scan_type,
        "timestamp": datetime.now().isoformat(),
        "total_threats": len(results),
        "findings": [r.to_dict() for r in results]
    }

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)

    return filepath


def get_latest_report():
    """获取最新报告文件路径"""
    ensure_reports_dir()
    files = [f for f in os.listdir(REPORTS_DIR) if f.endswith('.json')]
    if not files:
        return None
    files.sort(reverse=True)
    return os.path.join(REPORTS_DIR, files[0])


def display_report(filepath=None):
    """显示报告内容"""
    if filepath is None:
        filepath = get_latest_report()
        if not filepath:
            print_error("  No reports found. Please run a scan first.")
            return

    if not os.path.exists(filepath):
        print_error(f"  Report file not found: {filepath}")
        return

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print_error(f"  Failed to read report: {e}")
        return

    print_color("\n  === SCAN REPORT ===", color='\033[36m', bold=True)
    print_info(f"  Scan Type: {data.get('scan_type', 'Unknown')}")
    print_info(f"  Timestamp: {data.get('timestamp', 'Unknown')}")
    print_info(f"  Total Threats: {data.get('total_threats', 0)}")

    findings = data.get('findings', [])
    if not findings:
        print_success("  No threats found.")
        return

    for idx, item in enumerate(findings, 1):
        severity = item.get('severity', 'medium')
        if severity == 'critical':
            color = '\033[31m'
            label = '[CRITICAL]'
        elif severity == 'high':
            color = '\033[33m'
            label = '[HIGH]'
        elif severity == 'medium':
            color = '\033[34m'
            label = '[MEDIUM]'
        else:
            color = '\033[37m'
            label = '[LOW]'

        print_color(f"  {idx}. {label} {item.get('type', '').upper()}", color=color, bold=True)
        print_color(f"      Path: {item.get('path', '')}", color='\033[37m')
        print_color(f"      Reason: {item.get('reason', '')}", color='\033[37m')
        if item.get('extra'):
            extra = item['extra']
            extra_str = ', '.join([f"{k}: {v}" for k, v in extra.items()])
            print_color(f"      Extra: {extra_str}", color='\033[37m')

    print_info(f"\n  Report saved to: {filepath}")