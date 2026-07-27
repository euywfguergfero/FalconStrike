#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FalconStrike - 主入口
"""

import sys
import os
import json

# ===== 调试：标记启动 =====
print("[DEBUG] main.py started", flush=True)

# 扫描引擎
try:
    from scanner import quick_scan, deep_scan, full_scan
    print("[DEBUG] scanner imported successfully", flush=True)
except ImportError as e:
    print("[ERROR] Failed to import scanner module. Please install psutil:")
    print("        pip install psutil")
    sys.exit(1)

from utils import (
    clear_screen,
    print_color,
    print_success,
    print_warning,
    print_error,
    print_info,
    wait_for_enter,
    is_admin
)
from config import load_config, save_config, load_hashes, get_available_languages
from i18n import init_i18n, t
from cloud_sync import sync_cloud_samples, get_local_sample_count
from quarantine import (
    quarantine_file,
    restore_file,
    delete_permanently,
    get_quarantine_list,
    clean_orphaned_metadata
)
from trust_zone import (
    get_trust_zone,
    add_to_trust_zone,
    remove_from_trust_zone,
    clear_trust_zone
)
from report import generate_report, display_report, get_latest_report
from realtime import start_realtime, stop_realtime, realtime_status, is_realtime_running
from defender_takeover import takeover_defender, restore_defender, defender_status

print("[DEBUG] All imports successful", flush=True)

VERSION = "1.0.0"
BANNER = r"""
  _____ _    _     ____ ___  _   _ ____ _____ ____  ___ _  _______
 |  ___/ \  | |   / ___/ _ \| \ | / ___|_   _|  _ \|_ _| |/ / ____|
 | |_ / _ \ | |  | |  | | | |  \| \___ \ | | | |_) || || ' /|  _|
 |  _/ ___ \| |__| |__| |_| | |\  |___) || | |  _ < | || . \| |___
 |_|/_/   \_\_____\____\___/|_| \_|____/ |_| |_| \_\___|_|\_\_____|
"""


def print_banner():
    """显示 Banner 和状态"""
    clear_screen()
    print_color(BANNER, color='\033[36m', bold=True)
    print_color(f"  {t('app_name')} v{VERSION} - \"{t('subtitle')}\"", color='\033[33m', bold=True)
    print_color(f"  {t('url')}", color='\033[37m')
    print_color("=" * 70, color='\033[37m')

    # 优先使用实际运行状态
    rt_is_running = is_realtime_running()
    if rt_is_running:
        status_symbol = t("enabled_symbol")
        status_color = '\033[32m'
    else:
        status_symbol = t("disabled_symbol")
        status_color = '\033[31m'

    sample_count = get_local_sample_count()
    print_color(
        f"  {t('realtime_status')}: {status_color}{status_symbol}\033[37m  |  {t('blocks_label')}: 0  |  {t('quarantined_label')}: 0  |  {t('samples_label')}: {sample_count}",
        color='\033[37m'
    )
    print_color("=" * 70, color='\033[37m')

    for i in range(1, 11):
        print_color(f"  {i}.  {t(f'menu.{i}')}", color='\033[37m')
    print_color(f"  0.  {t('menu.0')}", color='\033[37m')
    print_color("=" * 70, color='\033[37m')


def display_scan_results(results, scan_type="Quick"):
    """显示扫描结果并生成报告"""
    if not results:
        print_success(f"  {scan_type} scan complete. No threats found.")
        report_path = generate_report(results, scan_type)
        print_info(f"  Report saved to: {report_path}")
        return

    critical = [r for r in results if r.severity == "critical"]
    high = [r for r in results if r.severity == "high"]
    medium = [r for r in results if r.severity == "medium"]
    low = [r for r in results if r.severity == "low"]

    print_warning(f"  Found {len(results)} threat(s):")
    if critical:
        print_color(f"    [CRITICAL] {len(critical)} items", color='\033[31m', bold=True)
        for r in critical[:10]:
            print_color(f"      - {r.path}", color='\033[31m')
            print_color(f"        Reason: {r.reason}", color='\033[37m')
        if len(critical) > 10:
            print_info(f"      ... and {len(critical)-10} more critical items")
    if high:
        print_color(f"    [HIGH] {len(high)} items", color='\033[33m', bold=True)
        for r in high[:5]:
            print_color(f"      - {r.path}", color='\033[33m')
            print_color(f"        Reason: {r.reason}", color='\033[37m')
        if len(high) > 5:
            print_info(f"      ... and {len(high)-5} more high-risk items")
    if medium:
        print_color(f"    [MEDIUM] {len(medium)} items", color='\033[34m', bold=True)
        for r in medium[:3]:
            print_color(f"      - {r.path}", color='\033[34m')
            print_color(f"        Reason: {r.reason}", color='\033[37m')
        if len(medium) > 3:
            print_info(f"      ... and {len(medium)-3} more medium-risk items")
    if low:
        print_info(f"    [LOW] {len(low)} items (use --report for details)")

    report_path = generate_report(results, scan_type)
    print_info(f"  Report saved to: {report_path}")


def settings_menu():
    """设置子菜单"""
    while True:
        clear_screen()
        print_color("\n  === " + t("settings_title") + " ===", color='\033[36m', bold=True)
        print_color("  1.  " + t("settings.update_samples"), color='\033[37m')
        print_color("  2.  " + t("settings.view_config"), color='\033[37m')
        print_color("  3.  " + t("settings.switch_language"), color='\033[37m')
        print_color("  0.  " + t("settings.back"), color='\033[37m')
        print_color("=" * 70, color='\033[37m')

        choice = input(f"\033[33m  {t('prompt')}: \033[37m").strip()

        if choice == "0":
            break
        elif choice == "1":
            print_info("\n  " + t("settings.syncing"))
            success, added, total = sync_cloud_samples(force=False)
            if success:
                if added == 0:
                    print_info(f"  {t('settings.sync_already_latest')}")
                else:
                    print_success(f"  {t('settings.sync_success', added, total)}")
            else:
                print_error(f"  {t('settings.sync_failed')}")
            wait_for_enter(t('press_enter'))
        elif choice == "2":
            config = load_config()
            print_color("\n  " + json.dumps(config, indent=2, ensure_ascii=False), color='\033[37m')
            wait_for_enter(t('press_enter'))
        elif choice == "3":
            available = get_available_languages()
            print_info("  Available languages:")
            for idx, lang in enumerate(available, 1):
                print_color(f"    {idx}. {lang}", color='\033[37m')
            print_info("  0. Cancel")
            lang_choice = input("  Select language number: ").strip()
            if lang_choice == "0":
                continue
            try:
                idx = int(lang_choice)
                if 1 <= idx <= len(available):
                    new_lang = available[idx-1]
                    config = load_config()
                    config["language"] = new_lang
                    if save_config(config):
                        print_success(f"  Language switched to {new_lang}.")
                        print_info("  Restart the program to apply changes, or type 'reload' to reload language now.")
                        reload_choice = input("  Reload language now? (y/N): ").strip().lower()
                        if reload_choice == 'y':
                            init_i18n(new_lang)
                            print_success("  Language reloaded.")
                        else:
                            print_info("  Please restart FalconStrike for changes to take full effect.")
                    else:
                        print_error("  Failed to save language preference.")
                else:
                    print_error("  Invalid selection.")
            except ValueError:
                print_error("  Please enter a number.")
            wait_for_enter(t('press_enter'))
        else:
            print_error(f"\n  {t('invalid')}")
            wait_for_enter(t('press_enter'))


def quarantine_menu():
    """隔离区管理子菜单"""
    while True:
        clear_screen()
        print_color("\n  === " + t("quarantine.title") + " ===", color='\033[36m', bold=True)
        items = get_quarantine_list()
        if not items:
            print_info("  " + t("quarantine.empty"))
        else:
            print_info(f"  {t('quarantine.count', len(items))}")
            for idx, item in enumerate(items[:10], 1):
                print_color(f"    {idx}. {os.path.basename(item['original_path'])}", color='\033[37m')
                print_color(f"       Original: {item['original_path']}", color='\033[33m')
                print_color(f"       Time: {item['timestamp']}", color='\033[33m')
            if len(items) > 10:
                print_info(f"      ... and {len(items)-10} more items")
        print_color("\n  1.  " + t("quarantine.restore"), color='\033[37m')
        print_color("  2.  " + t("quarantine.delete"), color='\033[37m')
        print_color("  3.  " + t("quarantine.clean_orphans"), color='\033[37m')
        print_color("  0.  " + t("settings.back"), color='\033[37m')
        print_color("=" * 70, color='\033[37m')

        choice = input(f"\033[33m  {t('prompt')}: \033[37m").strip()

        if choice == "0":
            break
        elif choice == "1":
            if not items:
                print_warning("  No items to restore.")
                wait_for_enter(t('press_enter'))
                continue
            print_info("  Enter the number of the file to restore:")
            idx_input = input("  > ").strip()
            try:
                idx = int(idx_input)
                if 1 <= idx <= len(items):
                    path = items[idx-1]['quarantined_path']
                    success, err = restore_file(path)
                    if success:
                        print_success("  File restored successfully.")
                    else:
                        print_error(f"  Restore failed: {err}")
                else:
                    print_error("  Invalid index.")
            except ValueError:
                print_error("  Please enter a number.")
            wait_for_enter(t('press_enter'))

        elif choice == "2":
            if not items:
                print_warning("  No items to delete.")
                wait_for_enter(t('press_enter'))
                continue
            print_info("  Enter the number of the file to permanently delete:")
            idx_input = input("  > ").strip()
            try:
                idx = int(idx_input)
                if 1 <= idx <= len(items):
                    path = items[idx-1]['quarantined_path']
                    confirm = input(f"  Are you sure to permanently delete {os.path.basename(path)}? (y/N): ").strip().lower()
                    if confirm == 'y':
                        success, err = delete_permanently(path)
                        if success:
                            print_success("  File permanently deleted.")
                        else:
                            print_error(f"  Delete failed: {err}")
                    else:
                        print_info("  Cancelled.")
                else:
                    print_error("  Invalid index.")
            except ValueError:
                print_error("  Please enter a number.")
            wait_for_enter(t('press_enter'))

        elif choice == "3":
            count = clean_orphaned_metadata()
            print_info(f"  Cleaned {count} orphaned metadata entries.")
            wait_for_enter(t('press_enter'))

        else:
            print_error(f"\n  {t('invalid')}")
            wait_for_enter(t('press_enter'))


def trust_zone_menu():
    """信用区管理子菜单"""
    while True:
        clear_screen()
        print_color("\n  === " + t("trust_zone.title") + " ===", color='\033[36m', bold=True)
        trust_list = get_trust_zone()
        if not trust_list:
            print_info("  " + t("trust_zone.empty"))
        else:
            print_info(f"  {t('trust_zone.count', len(trust_list))}")
            for idx, path in enumerate(trust_list, 1):
                print_color(f"    {idx}. {path}", color='\033[37m')
        print_color("\n  1.  " + t("trust_zone.add"), color='\033[37m')
        print_color("  2.  " + t("trust_zone.remove"), color='\033[37m')
        print_color("  3.  " + t("trust_zone.clear"), color='\033[37m')
        print_color("  0.  " + t("settings.back"), color='\033[37m')
        print_color("=" * 70, color='\033[37m')

        choice = input(f"\033[33m  {t('prompt')}: \033[37m").strip()

        if choice == "0":
            break
        elif choice == "1":
            path = input("  Enter path to trust: ").strip().strip('"')
            if not path:
                print_error("  Path cannot be empty.")
                wait_for_enter(t('press_enter'))
                continue
            success, msg = add_to_trust_zone(path)
            if success:
                print_success(f"  {msg}")
            else:
                print_error(f"  {msg}")
            wait_for_enter(t('press_enter'))

        elif choice == "2":
            trust_list = get_trust_zone()
            if not trust_list:
                print_warning("  Trust zone is empty.")
                wait_for_enter(t('press_enter'))
                continue
            print_info("  Enter the number of the path to remove:")
            idx_input = input("  > ").strip()
            try:
                idx = int(idx_input)
                if 1 <= idx <= len(trust_list):
                    path = trust_list[idx - 1]
                    confirm = input(f"  Remove '{path}'? (y/N): ").strip().lower()
                    if confirm == 'y':
                        success, msg = remove_from_trust_zone(path)
                        if success:
                            print_success(f"  {msg}")
                        else:
                            print_error(f"  {msg}")
                    else:
                        print_info("  Cancelled.")
                else:
                    print_error("  Invalid index.")
            except ValueError:
                print_error("  Please enter a number.")
            wait_for_enter(t('press_enter'))

        elif choice == "3":
            trust_list = get_trust_zone()
            if not trust_list:
                print_warning("  Trust zone is already empty.")
                wait_for_enter(t('press_enter'))
                continue
            confirm = input("  Clear all trust entries? (y/N): ").strip().lower()
            if confirm == 'y':
                success, msg = clear_trust_zone()
                if success:
                    print_success(f"  {msg}")
                else:
                    print_error(f"  {msg}")
            else:
                print_info("  Cancelled.")
            wait_for_enter(t('press_enter'))

        else:
            print_error(f"\n  {t('invalid')}")
            wait_for_enter(t('press_enter'))


def realtime_menu():
    """实时保护子菜单"""
    while True:
        clear_screen()
        print_color("\n  === " + t("realtime.title") + " ===", color='\033[36m', bold=True)
        if is_realtime_running():
            print_success("  " + t("realtime.status_running"))
        else:
            print_warning("  " + t("realtime.status_stopped"))
        print_color("\n  1.  " + t("realtime.start"), color='\033[37m')
        print_color("  2.  " + t("realtime.stop"), color='\033[37m')
        print_color("  0.  " + t("settings.back"), color='\033[37m')
        print_color("=" * 70, color='\033[37m')

        choice = input(f"\033[33m  {t('prompt')}: \033[37m").strip()

        if choice == "0":
            break
        elif choice == "1":
            if start_realtime():
                print_success("  Real-time protection started.")
            else:
                print_error("  Failed to start real-time protection.")
            wait_for_enter(t('press_enter'))
        elif choice == "2":
            if stop_realtime():
                print_success("  Real-time protection stopped.")
            else:
                print_error("  Failed to stop real-time protection.")
            wait_for_enter(t('press_enter'))
        else:
            print_error(f"\n  {t('invalid')}")
            wait_for_enter(t('press_enter'))


def defender_menu():
    """接管 Defender 子菜单"""
    while True:
        clear_screen()
        print_color("\n  === " + t("defender.title") + " ===", color='\033[36m', bold=True)
        defender_status()
        print_color("\n  1.  " + t("defender.takeover"), color='\033[37m')
        print_color("  2.  " + t("defender.restore"), color='\033[37m')
        print_color("  0.  " + t("settings.back"), color='\033[37m')
        print_color("=" * 70, color='\033[37m')

        choice = input(f"\033[33m  {t('prompt')}: \033[37m").strip()

        if choice == "0":
            break
        elif choice == "1":
            if takeover_defender():
                print_success("  FalconStrike has taken over real-time protection.")
                print_info("  Please start FalconStrike real-time protection from menu 5.")
            else:
                print_error("  Takeover failed.")
            wait_for_enter(t('press_enter'))
        elif choice == "2":
            if restore_defender():
                print_success("  Windows Defender restored.")
            else:
                print_error("  Restore failed.")
            wait_for_enter(t('press_enter'))
        else:
            print_error(f"\n  {t('invalid')}")
            wait_for_enter(t('press_enter'))


def cleanup_mode():
    """清理模式：扫描并隔离所有发现的威胁"""
    print_info(f"\n  {t('scanning')} (Quick) before cleanup...")
    results = quick_scan()
    if not results:
        print_success("  No threats found. Nothing to clean.")
        wait_for_enter(t('press_enter'))
        return

    display_scan_results(results, "Quick")
    print()
    confirm = input("  Do you want to quarantine all detected threats? (y/N): ").strip().lower()
    if confirm == 'y':
        quarantined_count = 0
        failed_count = 0
        for r in results:
            if r.type in ["process", "file", "startup", "service"] and os.path.exists(r.path):
                success, _, err = quarantine_file(r.path, reason=r.reason)
                if success:
                    quarantined_count += 1
                else:
                    failed_count += 1
                    print_error(f"  Failed to quarantine {r.path}: {err}")
        print_success(f"  Quarantined {quarantined_count} files.")
        if failed_count > 0:
            print_warning(f"  Failed to quarantine {failed_count} files.")
    else:
        print_info("  Cleanup cancelled.")
    wait_for_enter(t('press_enter'))


def handle_choice(choice):
    """处理用户选择"""
    if choice == "0":
        print_color(f"\n  {t('exit')}", color='\033[31m')
        sys.exit(0)

    elif choice == "1":
        print_info(f"\n  {t('scanning')} (Quick)...")
        results = quick_scan()
        display_scan_results(results, "Quick")
        wait_for_enter(t('press_enter'))

    elif choice == "2":
        print_info(f"\n  {t('scanning')} (Deep)...")
        results = deep_scan()
        display_scan_results(results, "Deep")
        wait_for_enter(t('press_enter'))

    elif choice == "3":
        print_info(f"\n  {t('scanning')} (Full)...")
        results = full_scan()
        display_scan_results(results, "Full")
        wait_for_enter(t('press_enter'))

    elif choice == "4":
        display_report()
        wait_for_enter(t('press_enter'))

    elif choice == "5":
        realtime_menu()

    elif choice == "6":
        quarantine_menu()

    elif choice == "7":
        defender_menu()

    elif choice == "8":
        cleanup_mode()

    elif choice == "9":
        settings_menu()

    elif choice == "10":
        trust_zone_menu()

    else:
        print_error(f"\n  {t('invalid')}")
        wait_for_enter(t('press_enter'))


def main():
    """主循环"""
    print("[DEBUG] Entering main()", flush=True)

    # 检查是否为守护进程模式
    if len(sys.argv) > 1 and sys.argv[1] == '--daemon':
        print("[DEBUG] Starting daemon mode", flush=True)
        from realtime import run_daemon
        run_daemon()
        return

    print("[DEBUG] Loading config...", flush=True)
    config = load_config()
    lang_code = config.get("language", "zh-CN")
    print(f"[DEBUG] Language: {lang_code}", flush=True)

    print("[DEBUG] Initializing i18n...", flush=True)
    init_i18n(lang_code)

    if not is_admin():
        print_warning(f"\n  {t('admin_warning')}")
        wait_for_enter(t('press_enter'))

    try:
        print("[DEBUG] Loading hashes...", flush=True)
        hashes = load_hashes()
        print_info(f"  {t('config_loaded', len(hashes))}")
        wait_for_enter(t('press_enter'))
    except Exception as e:
        print_error(f"  {t('config_failed', str(e))}")
        wait_for_enter(t('press_enter'))
        sys.exit(1)

    print("[DEBUG] Entering main loop", flush=True)
    while True:
        print_banner()
        choice = input(f"\033[33m  {t('prompt')}: \033[37m").strip()
        handle_choice(choice)


if __name__ == "__main__":
    try:
        print("[DEBUG] Running main()", flush=True)
        main()
    except KeyboardInterrupt:
        print_color(f"\n  {t('interrupted')}", color='\033[31m')
        sys.exit(1)
    except Exception as e:
        print(f"[FATAL] Unhandled exception: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")
        sys.exit(1)