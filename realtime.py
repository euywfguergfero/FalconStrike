#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FalconStrike - 实时保护模块（支持后台守护进程 + 用户交互弹窗）
"""

import os
import sys
import time
import threading
import psutil
import hashlib
import subprocess
from utils import print_info, print_success, print_warning, print_error, get_app_dir
from config import load_config, save_config, load_hashes
from quarantine import quarantine_file
from trust_zone import is_trusted, add_to_trust_zone, remove_from_trust_zone

# 全局标志（仅用于当前进程）
_running = False
_thread = None
_observer = None

# PID 文件路径
PID_FILE = os.path.join(get_app_dir(), 'data', 'falconstrike.pid')

# 临时忽略列表（内存缓存，仅当前会话有效）
_temp_ignore = set()
_ignore_lock = threading.Lock()


def is_temp_ignored(path):
    """检查是否在临时忽略列表中"""
    with _ignore_lock:
        return path in _temp_ignore


def add_temp_ignore(path):
    """添加到临时忽略列表"""
    with _ignore_lock:
        _temp_ignore.add(path)


def get_current_language():
    """从配置中获取当前语言代码"""
    try:
        config = load_config()
        return config.get("language", "zh-CN")
    except:
        return "zh-CN"


def get_action_texts(lang):
    """根据语言返回对话框文本"""
    texts = {
        'zh-CN': {
            'title': '发现可疑文件',
            'msg': '发现可疑文件：\n{path}\n请选择操作：',
            'delete': '删除文件',
            'quarantine': '放到隔离区',
            'ignore': '忽略（本次）'
        },
        'zh-TW': {
            'title': '發現可疑檔案',
            'msg': '發現可疑檔案：\n{path}\n請選擇操作：',
            'delete': '刪除檔案',
            'quarantine': '放到隔離區',
            'ignore': '略過（本次）'
        },
        'en-US': {
            'title': 'Suspicious File Detected',
            'msg': 'Suspicious file detected:\n{path}\nPlease choose action:',
            'delete': 'Delete File',
            'quarantine': 'Move to Quarantine',
            'ignore': 'Ignore (once)'
        },
        'ja-JP': {
            'title': '疑わしいファイルを検出',
            'msg': '疑わしいファイルを検出しました：\n{path}\n操作を選択してください：',
            'delete': 'ファイルを削除',
            'quarantine': '隔離する',
            'ignore': '無視（今回のみ）'
        },
        'ko-KR': {
            'title': '의심스러운 파일 발견',
            'msg': '의심스러운 파일을 발견했습니다：\n{path}\n작업을 선택하세요：',
            'delete': '파일 삭제',
            'quarantine': '격리',
            'ignore': '무시 (이번만)'
        },
        'fr-FR': {
            'title': 'Fichier suspect détecté',
            'msg': 'Fichier suspect détecté :\n{path}\nChoisissez une action :',
            'delete': 'Supprimer',
            'quarantine': 'Mettre en quarantaine',
            'ignore': 'Ignorer (une fois)'
        },
        'de-DE': {
            'title': 'Verdächtige Datei erkannt',
            'msg': 'Verdächtige Datei erkannt:\n{path}\nWählen Sie eine Aktion:',
            'delete': 'Löschen',
            'quarantine': 'In Quarantäne verschieben',
            'ignore': 'Ignorieren (einmal)'
        },
        'es-ES': {
            'title': 'Archivo sospechoso detectado',
            'msg': 'Archivo sospechoso detectado:\n{path}\nElija una acción:',
            'delete': 'Eliminar',
            'quarantine': 'Mover a cuarentena',
            'ignore': 'Ignorar (una vez)'
        }
    }
    return texts.get(lang, texts['en-US'])


def prompt_user_for_action(file_path):
    """
    弹出用户交互对话框，返回用户选择：
    'delete' , 'quarantine' , 'ignore' 或 None（超时/关闭）
    """
    lang = get_current_language()
    texts = get_action_texts(lang)
    msg = texts['msg'].format(path=file_path)

    try:
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()  # 隐藏主窗口
        top = tk.Toplevel(root)
        top.title(texts['title'])
        top.geometry('450x180')
        top.transient(root)
        top.grab_set()
        top.resizable(False, False)

        # 居中显示
        top.update_idletasks()
        width = top.winfo_width()
        height = top.winfo_height()
        x = (top.winfo_screenwidth() // 2) - (width // 2)
        y = (top.winfo_screenheight() // 2) - (height // 2)
        top.geometry(f'+{x}+{y}')

        tk.Label(top, text=msg, wraplength=400, justify='left').pack(pady=10, padx=10)

        result = tk.StringVar(value='')

        def on_click(action):
            result.set(action)
            top.destroy()
            root.quit()

        frame = tk.Frame(top)
        frame.pack(pady=10)
        tk.Button(frame, text=texts['delete'], width=12,
                  command=lambda: on_click('delete')).pack(side=tk.LEFT, padx=5)
        tk.Button(frame, text=texts['quarantine'], width=14,
                  command=lambda: on_click('quarantine')).pack(side=tk.LEFT, padx=5)
        tk.Button(frame, text=texts['ignore'], width=12,
                  command=lambda: on_click('ignore')).pack(side=tk.LEFT, padx=5)

        # 超时自动忽略（60秒无操作）
        def timeout():
            if result.get() == '':
                result.set('ignore')
                top.destroy()
                root.quit()
        top.after(60000, timeout)  # 60秒超时

        root.mainloop()
        return result.get()

    except Exception as e:
        # 如果无法显示对话框（无桌面环境），默认忽略
        print_error(f"  Failed to show dialog: {e}")
        print_info("  Defaulting to 'ignore'.")
        return 'ignore'


def handle_suspicious_file(file_path, reason=""):
    """
    处理可疑文件：检查临时忽略，弹窗让用户选择操作
    """
    # 如果已在临时忽略列表，直接跳过
    if is_temp_ignored(file_path):
        return

    # 检查是否在信用区（已信任）
    if is_trusted(file_path):
        return

    action = prompt_user_for_action(file_path)

    if action == 'delete':
        try:
            os.remove(file_path)
            print_warning(f"  Real-time: Deleted suspicious file: {file_path}")
        except Exception as e:
            print_error(f"  Real-time: Failed to delete {file_path}: {e}")

    elif action == 'quarantine':
        success, _, err = quarantine_file(file_path, reason=reason or "Real-time detection")
        if success:
            print_warning(f"  Real-time: Quarantined {file_path}")
        else:
            print_error(f"  Real-time: Failed to quarantine {file_path}: {err}")

    elif action == 'ignore':
        add_temp_ignore(file_path)
        print_info(f"  Real-time: Ignored (temporarily) {file_path}")
    else:
        # 默认忽略（超时或关闭窗口）
        add_temp_ignore(file_path)
        print_info(f"  Real-time: Ignored (timeout) {file_path}")


def _update_config_enabled(enabled):
    """更新配置文件中的实时保护启用状态"""
    try:
        config = load_config()
        if "realtime" not in config:
            config["realtime"] = {}
        config["realtime"]["enabled"] = enabled
        save_config(config)
    except Exception as e:
        print_error(f"  Failed to update config: {e}")


def _write_pid():
    """写入当前进程 PID 到文件"""
    try:
        os.makedirs(os.path.dirname(PID_FILE), exist_ok=True)
        with open(PID_FILE, 'w') as f:
            f.write(str(os.getpid()))
        return True
    except Exception as e:
        print_error(f"  Failed to write PID file: {e}")
        return False


def _read_pid():
    """读取 PID 文件中的 PID"""
    try:
        with open(PID_FILE, 'r') as f:
            return int(f.read().strip())
    except:
        return None


def _remove_pid():
    """删除 PID 文件"""
    try:
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
        return True
    except:
        return False


def _is_pid_running(pid):
    """检查指定 PID 的进程是否在运行"""
    try:
        proc = psutil.Process(pid)
        return proc.is_running()
    except:
        return False


def is_realtime_running():
    """检查实时保护是否正在运行（包括后台进程）"""
    if _running:
        return True
    pid = _read_pid()
    if pid is not None and _is_pid_running(pid):
        return True
    return False


class FileChangeHandler:
    def __init__(self):
        pass

    def on_created(self, event):
        if not event.is_directory:
            self.check_file(event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            self.check_file(event.src_path)

    def check_file(self, path):
        ext = os.path.splitext(path)[1].lower()
        if ext not in ['.exe', '.dll', '.scr', '.bat', '.cmd', '.vbs', '.ps1']:
            return
        if is_temp_ignored(path) or is_trusted(path):
            return
        hashes = load_hashes()
        try:
            with open(path, 'rb') as f:
                md5 = hashlib.md5(f.read()).hexdigest()
            if md5 in hashes:
                handle_suspicious_file(path, reason="Real-time file monitoring")
        except:
            pass


def monitor_processes():
    """监控新进程创建（轮询）"""
    known_pids = set(psutil.pids())
    while _running:
        current_pids = set(psutil.pids())
        new_pids = current_pids - known_pids
        for pid in new_pids:
            try:
                proc = psutil.Process(pid)
                exe = proc.exe()
                if exe and os.path.exists(exe) and not is_temp_ignored(exe) and not is_trusted(exe):
                    hashes = load_hashes()
                    with open(exe, 'rb') as f:
                        md5 = hashlib.md5(f.read()).hexdigest()
                    if md5 in hashes:
                        # 先尝试终止进程
                        try:
                            proc.terminate()
                            proc.wait(timeout=3)
                        except:
                            try:
                                proc.kill()
                            except:
                                pass
                        # 然后弹窗询问
                        handle_suspicious_file(exe, reason="Real-time process monitoring")
            except:
                pass
        known_pids = current_pids
        time.sleep(2)


def start_realtime_daemon():
    """启动后台守护进程（独立于主窗口）"""
    if _running:
        print_warning("  Real-time protection already running in this process.")
        return False

    pid = _read_pid()
    if pid is not None and _is_pid_running(pid):
        print_warning("  Real-time protection is already running in background.")
        return False

    try:
        script = sys.argv[0]
        if getattr(sys, 'frozen', False):
            exe = sys.executable
            args = [exe, '--daemon']
        else:
            exe = sys.executable
            args = [exe, script, '--daemon']

        subprocess.Popen(args, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print_success("  Real-time protection started in background.")
        print_info("  You can close the main window; protection will continue.")
        return True
    except Exception as e:
        print_error(f"  Failed to start background process: {e}")
        return False


def stop_realtime_daemon():
    """停止后台实时保护进程"""
    pid = _read_pid()
    if pid is None:
        print_warning("  No background real-time protection found.")
        return False

    try:
        proc = psutil.Process(pid)
        proc.terminate()
        proc.wait(timeout=5)
        _remove_pid()
        print_success("  Background real-time protection stopped.")
        return True
    except psutil.NoSuchProcess:
        _remove_pid()
        print_warning("  Background process already terminated.")
        return False
    except Exception as e:
        print_error(f"  Failed to stop background process: {e}")
        return False


def run_daemon():
    """守护进程主循环（由 --daemon 调用）"""
    global _running
    _running = True

    if not _write_pid():
        return

    # 文件监控
    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
        class Handler(FileSystemEventHandler, FileChangeHandler):
            pass
        event_handler = Handler()
        observer = Observer()
        watch_dirs = [os.path.expanduser("~\\Downloads"), os.environ.get("TEMP", "")]
        for d in watch_dirs:
            if os.path.exists(d):
                observer.schedule(event_handler, d, recursive=True)
        observer.start()
        print_info("  File monitor started.")
    except ImportError:
        print_warning("  watchdog not installed. File monitoring disabled.")
        observer = None

    # 进程监控线程（非守护，让主线程保持运行）
    thread = threading.Thread(target=monitor_processes, daemon=False)
    thread.start()

    try:
        while _running:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        _running = False
        if observer:
            observer.stop()
            observer.join()
        thread.join(timeout=2)
        _remove_pid()
        print_info("  Real-time daemon stopped.")


def start_realtime_interactive():
    """交互式启动（在主菜单中调用）"""
    if is_realtime_running():
        print_warning("  Real-time protection is already running.")
        return False
    return start_realtime_daemon()


def stop_realtime_interactive():
    """交互式停止"""
    if not is_realtime_running():
        print_warning("  Real-time protection is not running.")
        return False
    return stop_realtime_daemon()


def realtime_status():
    """显示状态并返回布尔值"""
    if is_realtime_running():
        print_success("  Real-time protection is running.")
        return True
    else:
        print_warning("  Real-time protection is stopped.")
        return False


# ========== 别名（兼容旧接口） ==========
start_realtime = start_realtime_interactive
stop_realtime = stop_realtime_interactive