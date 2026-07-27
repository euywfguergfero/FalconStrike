# FalconStrike – 轻量级通用杀毒引擎

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![GitHub release](https://img.shields.io/github/v/release/euywfguergfero/FalconStrike)](https://github.com/euywfguergfero/FalconStrike/releases)

**FalconStrike** 是一款轻量级、纯命令行的 Windows 杀毒工具，专注于快速检测和清除恶意软件。它没有 GUI、没有广告、没有后台驻留垃圾，只有纯粹的杀毒能力。

---

## 核心特性

- **实时保护** – 文件/进程/注册表/网络全方位监控，支持后台守护进程（关闭主窗口后继续运行）
- **多模式扫描** – 快速 / 深度 / 全盘扫描，利用多线程加速
- **强力清理** – 进程终止、启动项删除、服务禁用、文件隔离
- **接管 Windows Defender** – 一键禁用 Defender 实时保护，让 FalconStrike 接管
- **报告生成** – 扫描结果自动生成 JSON 报告，便于分析
- **隔离区管理** – 查看、恢复、彻底删除隔离文件
- **信用区（Trust Zone）** – 自定义信任路径，避免误报
- **多语言支持** – 简体中文、繁体中文、English、日本語、한국어、Français、Deutsch、Español（自动检测系统语言）
- **云端样本库** – 从 GitHub 仓库同步数十万恶意软件哈希（36万+ 条）
- **完全命令行** – 适合服务器运维和批量部署

---

## 快速开始

### 方式一：直接下载可执行文件（推荐普通用户）
1. 前往 [Releases](https://github.com/euywfguergfero/FalconStrike/releases) 下载最新版 `FalconStrike.exe`
2. **右键 → 以管理员身份运行**（确保能够扫描系统目录和终止进程）
3. 首次运行建议执行：
   - 进入 `9. 设置` → `1. 更新样本库`（下载云端哈希库，约 30–40 MB）
   - 进入 `5. 实时保护` → `1. 启动实时保护`（开启后台守护）

### 方式二：从源码运行（适合开发者）
```bash
# 克隆仓库
git clone https://github.com/euywfguergfero/FalconStrike.git
cd FalconStrike

# 安装依赖（推荐使用虚拟环境）
pip install -r requirements.txt

# 运行
python main.py
```

---

## 主界面预览

```
  _____ _    _     ____ ___  _   _ ____ _____ ____  ___ _  _______
 |  ___/ \  | |   / ___/ _ \| \ | / ___|_   _|  _ \|_ _| |/ / ____|
 | |_ / _ \ | |  | |  | | | |  \| \___ \ | | | |_) || || ' /|  _|
 |  _/ ___ \| |__| |__| |_| | |\  |___) || | |  _ < | || . \| |___
 |_|/_/   \_\_____\____\___/|_| \_|____/ |_| |_| \_\___|_|\_\_____|

  FalconStrike v1.0.0 - "轻量级通用杀毒引擎"
  https://github.com/euywfguergfero/FalconStrike
======================================================================
  实时保护状态: [*]  |  已拦截: 0  |  隔离文件: 0  |  样本数: 368763
======================================================================
  1.  快速扫描
  2.  深度扫描
  3.  全盘扫描
  4.  查看报告
  5.  实时保护
  6.  隔离区管理
  7.  接管 Windows Defender
  8.  清理模式
  9.  设置
  10. 信用区管理
  0.  退出
======================================================================
  选择功能（填数字）：
```

---

## 使用指南

### 主菜单功能说明

| 编号 | 功能 | 说明 |
|------|------|------|
| 1 | 快速扫描 | 扫描进程、启动项、服务（约 10–30 秒） |
| 2 | 深度扫描 | 快速扫描 + 常见目录文件哈希扫描 |
| 3 | 全盘扫描 | 所有磁盘分区的可执行文件扫描（多线程） |
| 4 | 查看报告 | 显示最近一次扫描的 JSON 报告 |
| 5 | 实时保护 | 启动/停止后台守护进程（文件+进程监控） |
| 6 | 隔离区管理 | 查看、恢复、彻底删除隔离文件 |
| 7 | 接管 Defender | 禁用 Windows Defender 实时保护 |
| 8 | 清理模式 | 扫描并一键隔离所有威胁 |
| 9 | 设置 | 更新样本库、查看配置、切换语言 |
| 10 | 信用区管理 | 添加/删除信任路径（避免误报） |

### 实时保护（菜单 5）
- 启动后，FalconStrike 会在后台监控 `Downloads` 和 `TEMP` 目录的新增/修改文件，以及所有新启动的进程。
- 一旦发现匹配哈希库的可疑文件，会弹出对话框让用户选择：**删除**、**隔离**或**忽略**（60 秒无操作自动忽略）。
- 关闭主窗口后，保护依然在后台运行（通过 PID 文件管理）。

### 接管 Windows Defender（菜单 7）
- 尝试自动禁用 Defender 实时保护。若因系统策略失败，会显示多语言手动操作指南。
- 接管后，建议立即启动 FalconStrike 的实时保护（菜单 5）。

### 更新样本库（菜单 9 → 1）
- 从 GitHub 仓库 `CYB3RMX/MalwareHashDB` 下载约 36.8 万个恶意软件哈希（MD5）。
- 首次下载约 30–40 MB，请保持网络畅通。
- 样本库存储在 `data/hashes.json`，支持手动更新。

---

## 配置与文件结构

```
FalconStrike/
├── main.py                  # 主程序
├── scanner.py               # 扫描引擎
├── realtime.py              # 实时保护模块
├── quarantine.py            # 隔离区管理
├── trust_zone.py            # 信用区管理
├── defender_takeover.py     # Defender 接管
├── report.py                # 报告生成
├── cloud_sync.py            # 云端样本库同步
├── config.py                # 配置管理
├── i18n.py                  # 多语言引擎
├── utils.py                 # 工具函数
├── requirements.txt         # Python 依赖
├── data/
│   ├── config.json          # 用户配置（自动生成）
│   ├── hashes.json          # 恶意哈希库（自动下载）
│   └── falconstrike.pid     # 实时保护 PID 文件
├── locales/
│   ├── zh-CN.json           # 简体中文
│   ├── zh-TW.json           # 繁体中文
│   ├── en-US.json           # 英语
│   ├── ja-JP.json           # 日语
│   ├── ko-KR.json           # 韩语
│   ├── fr-FR.json           # 法语
│   ├── de-DE.json           # 德语
│   └── es-ES.json           # 西班牙语
├── logs/                    # 运行日志
├── reports/                 # 扫描报告
└── quarantine/              # 隔离区存储
```

---

## 开发与贡献

### 技术栈
- Python 3.10+
- psutil – 进程管理
- watchdog – 文件监控（可选，推荐安装）
- tkinter – 用户交互弹窗（Windows 自带）
- colorama – 彩色输出

### 构建可执行文件
```bash
# 安装 PyInstaller
pip install pyinstaller

# 打包（以管理员身份运行）
pyinstaller --onefile --windowed --name FalconStrike --icon=app.ico main.py
```

### 贡献指南
1. Fork 本仓库
2. 创建新分支 (`git checkout -b feature/your-feature`)
3. 提交更改 (`git commit -am 'Add some feature'`)
4. 推送 (`git push origin feature/your-feature`)
5. 创建 Pull Request

---

## 许可证

MIT License – 可自由使用、修改、分发，但需保留版权声明。详见 [LICENSE](LICENSE) 文件。

---

## 免责声明

- 本工具仅供安全研究和合法授权的应急响应使用。
- 使用者需自行承担所有风险。
- 请勿用于非法用途，否则后果自负。

---

## 致谢

- [psutil](https://github.com/giampaolo/psutil)
- [watchdog](https://github.com/gorakhargosh/watchdog)
- [CYB3RMX/MalwareHashDB](https://github.com/CYB3RMX/MalwareHashDB)
- 所有贡献者和测试用户

---

**Star ⭐ 支持我们，让 FalconStrike 更强大！**
```
