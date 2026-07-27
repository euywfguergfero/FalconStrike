#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FalconStrike - 接管 Windows Defender 模块（最终版）
"""

import subprocess
import winreg
import ctypes
import time
from utils import print_info, print_success, print_warning, print_error
from config import load_config


def get_current_language():
    """从配置中获取当前语言代码"""
    try:
        config = load_config()
        return config.get("language", "zh-CN")
    except:
        return "zh-CN"


def get_manual_guide(lang_code=None):
    """根据语言代码返回手动操作指南（精简版）"""
    if lang_code is None:
        lang_code = get_current_language()

    guides = {
        "zh-CN": """
请手动关闭 Windows Defender 的实时保护：

方法一（最简单）：通过 Windows 安全中心
1. 点击任务栏右下角的“^”展开图标，双击盾牌图标（或搜索“Windows 安全中心”）
2. 点击“病毒和威胁防护”
3. 点击“管理设置”
4. 将“实时保护”开关关闭
5. 如果提示需要管理员权限，请确认

方法二（备选）：如果安全中心被锁定，可以使用注册表
1. 按 Win + R，输入 regedit，回车
2. 导航到：HKEY_LOCAL_MACHINE\\SOFTWARE\\Policies\\Microsoft\\Windows Defender
3. 新建 DWORD (32位) 值，命名为 DisableAntiSpyware，值为 1
4. 重启电脑

完成后，再次运行 FalconStrike 的“接管”功能即可生效。
""",
        "zh-TW": """
請手動關閉 Windows Defender 的即時保護：

方法一（最簡單）：透過 Windows 安全性中心
1. 點擊工作列右下角的「^」展開圖示，雙擊盾牌圖示（或搜尋「Windows 安全性中心」）
2. 點擊「病毒與威脅防護」
3. 點擊「管理設定」
4. 將「即時保護」開關關閉
5. 如果提示需要系統管理員權限，請確認

方法二（備用）：如果安全性中心被鎖定，可以使用登錄檔
1. 按 Win + R，輸入 regedit，按 Enter
2. 瀏覽到：HKEY_LOCAL_MACHINE\\SOFTWARE\\Policies\\Microsoft\\Windows Defender
3. 新增 DWORD (32位元) 值，命名為 DisableAntiSpyware，值為 1
4. 重新啟動電腦

完成後，再次執行 FalconStrike 的「接管」功能即可生效。
""",
        "en-US": """
Please manually disable Windows Defender real-time protection:

Method 1 (Simplest): Through Windows Security Center
1. Click the "^" icon on the taskbar, double-click the shield icon (or search for "Windows Security")
2. Click "Virus & threat protection"
3. Click "Manage settings"
4. Turn off the "Real-time protection" switch
5. Confirm if administrator permission is prompted

Method 2 (Fallback): If the security center is locked, use the registry
1. Press Win + R, type regedit, press Enter
2. Navigate to: HKEY_LOCAL_MACHINE\\SOFTWARE\\Policies\\Microsoft\\Windows Defender
3. Create a new DWORD (32-bit) value named DisableAntiSpyware, set value to 1
4. Reboot your computer

After completion, run FalconStrike's "Takeover" function again to make it effective.
""",
        "ja-JP": """
Windows Defender のリアルタイム保護を手動で無効にしてください：

方法1（最も簡単）：Windows セキュリティセンターから
1. タスクバーの「^」アイコンをクリックし、シールドアイコンをダブルクリック（または「Windows セキュリティ」を検索）
2. 「ウイルスと脅威の防止」をクリック
3. 「設定の管理」をクリック
4. 「リアルタイム保護」のスイッチをオフにする
5. 管理者権限を求められたら確認する

方法2（代替）：セキュリティセンターがロックされている場合、レジストリを使用
1. Win + R を押し、regedit と入力して Enter
2. 以下の場所に移動：HKEY_LOCAL_MACHINE\\SOFTWARE\\Policies\\Microsoft\\Windows Defender
3. 新しい DWORD (32 ビット) 値を作成し、名前を DisableAntiSpyware、値を 1 に設定
4. パソコンを再起動

完了後、FalconStrike の「引き継ぎ」機能を再度実行すると有効になります。
""",
        "ko-KR": """
Windows Defender 실시간 보호를 수동으로 비활성화하십시오:

방법 1 (가장 간단): Windows 보안 센터를 통해
1. 작업 표시줄의 "^" 아이콘을 클릭하고 방패 아이콘을 더블 클릭 (또는 "Windows 보안" 검색)
2. "바이러스 및 위협 방지" 클릭
3. "설정 관리" 클릭
4. "실시간 보호" 스위치를 끕니다
5. 관리자 권한이 필요하면 확인

방법 2 (대체): 보안 센터가 잠겨 있으면 레지스트리 사용
1. Win + R 키를 누르고 regedit 입력 후 Enter
2. 다음 위치로 이동: HKEY_LOCAL_MACHINE\\SOFTWARE\\Policies\\Microsoft\\Windows Defender
3. 새 DWORD (32비트) 값 생성, 이름 DisableAntiSpyware, 값 1 설정
4. 컴퓨터 다시 시작

완료 후 FalconStrike의 "인수" 기능을 다시 실행하면 적용됩니다.
""",
        "fr-FR": """
Veuillez désactiver manuellement la protection en temps réel de Windows Defender :

Méthode 1 (la plus simple) : via le Centre de sécurité Windows
1. Cliquez sur l'icône "^" dans la barre des tâches, double-cliquez sur l'icône de bouclier (ou recherchez "Sécurité Windows")
2. Cliquez sur "Protection contre les virus et menaces"
3. Cliquez sur "Gérer les paramètres"
4. Désactivez l'interrupteur "Protection en temps réel"
5. Confirmez si une autorisation administrateur est demandée

Méthode 2 (alternative) : si le centre de sécurité est verrouillé, utilisez le registre
1. Appuyez sur Win + R, tapez regedit, appuyez sur Entrée
2. Accédez à : HKEY_LOCAL_MACHINE\\SOFTWARE\\Policies\\Microsoft\\Windows Defender
3. Créez une nouvelle valeur DWORD (32 bits) nommée DisableAntiSpyware, définissez la valeur à 1
4. Redémarrez votre ordinateur

Après cela, exécutez à nouveau la fonction "Prendre le contrôle" de FalconStrike pour l'appliquer.
""",
        "de-DE": """
Bitte deaktivieren Sie manuell den Echtzeitschutz von Windows Defender:

Methode 1 (am einfachsten): Über das Windows-Sicherheitscenter
1. Klicken Sie auf das "^"-Symbol in der Taskleiste, doppelklicken Sie auf das Schildsymbol (oder suchen Sie nach "Windows-Sicherheit")
2. Klicken Sie auf "Viren- und Bedrohungsschutz"
3. Klicken Sie auf "Einstellungen verwalten"
4. Schalten Sie den Schalter "Echtzeitschutz" aus
5. Bestätigen Sie, falls Administratorrechte erforderlich sind

Methode 2 (Alternative): Wenn das Sicherheitscenter gesperrt ist, verwenden Sie die Registrierung
1. Drücken Sie Win + R, geben Sie regedit ein, drücken Sie Enter
2. Navigieren Sie zu: HKEY_LOCAL_MACHINE\\SOFTWARE\\Policies\\Microsoft\\Windows Defender
3. Erstellen Sie einen neuen DWORD (32-Bit)-Wert mit dem Namen DisableAntiSpyware und setzen Sie den Wert auf 1
4. Starten Sie Ihren Computer neu

Führen Sie danach die "Übernahme"-Funktion von FalconStrike erneut aus, um sie zu aktivieren.
""",
        "es-ES": """
Desactive manualmente la protección en tiempo real de Windows Defender:

Método 1 (más simple): a través del Centro de seguridad de Windows
1. Haga clic en el icono "^" en la barra de tareas, haga doble clic en el icono de escudo (o busque "Seguridad de Windows")
2. Haga clic en "Protección contra virus y amenazas"
3. Haga clic en "Administrar configuración"
4. Desactive el interruptor "Protección en tiempo real"
5. Confirme si se solicita permiso de administrador

Método 2 (alternativa): si el centro de seguridad está bloqueado, use el registro
1. Presione Win + R, escriba regedit, presione Enter
2. Navegue a: HKEY_LOCAL_MACHINE\\SOFTWARE\\Policies\\Microsoft\\Windows Defender
3. Cree un nuevo valor DWORD (32 bits) llamado DisableAntiSpyware, establezca el valor en 1
4. Reinicie su computadora

Después de eso, ejecute nuevamente la función "Tomar el control" de FalconStrike para que surta efecto.
"""
    }

    return guides.get(lang_code, guides["en-US"])


def run_powershell(command):
    """执行 PowerShell 命令并返回 (成功标志, 输出, 错误)"""
    try:
        result = subprocess.run(
            ['powershell', '-Command', command],
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return False, "", str(e)


def disable_defender_realtime():
    """禁用 Windows Defender 实时保护（多种方法）"""
    print_info("  Disabling Windows Defender real-time protection...")

    # ---- 方法1: PowerShell 强力禁用 ----
    success, out, err = run_powershell(
        'Set-MpPreference -DisableRealtimeMonitoring $true -Force -ErrorAction Stop'
    )
    if success:
        print_success("  PowerShell command executed with -Force.")
        time.sleep(1)
        if not is_defender_active():
            print_success("  Defender real-time protection disabled via PowerShell.")
            return True
        else:
            print_warning("  Defender still shows as enabled after PowerShell. Trying next method.")
    else:
        print_error(f"  PowerShell failed: {err}")

    # ---- 方法2: 注册表（策略项） ----
    try:
        key_path = r"SOFTWARE\Policies\Microsoft\Windows Defender"
        key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path)
        winreg.SetValueEx(key, "DisableRealtimeMonitoring", 0, winreg.REG_DWORD, 1)
        winreg.CloseKey(key)
        print_success("  Registry key set (DisableRealtimeMonitoring).")
        if not is_defender_active():
            print_success("  Defender disabled via registry.")
            return True
        else:
            print_warning("  Registry method did not disable Defender.")
    except PermissionError:
        print_error("  Registry access denied (PermissionError).")
    except Exception as e:
        print_error(f"  Registry method failed: {e}")

    # ---- 方法3: 组策略注册表备用位置 ----
    try:
        key_path = r"SOFTWARE\Microsoft\Windows Defender\Real-Time Protection"
        key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path)
        winreg.SetValueEx(key, "DisableRealtimeMonitoring", 0, winreg.REG_DWORD, 1)
        winreg.CloseKey(key)
        print_success("  Registry key set (Real-Time Protection).")
        if not is_defender_active():
            print_success("  Defender disabled via registry (Real-Time Protection).")
            return True
        else:
            print_warning("  Registry method did not disable Defender.")
    except Exception as e:
        print_error(f"  Registry method (Real-Time Protection) failed: {e}")

    # ---- 方法4: 服务控制 ----
    try:
        print_info("  Attempting to stop Defender service...")
        success, out, err = run_powershell(
            'Stop-Service -Name WinDefend -Force -ErrorAction Stop'
        )
        if success:
            print_success("  WinDefend service stopped.")
            run_powershell('Set-Service -Name WinDefend -StartupType Disabled')
            if not is_defender_active():
                print_success("  Defender disabled by stopping service.")
                return True
            else:
                print_warning("  Service stop did not disable Defender.")
        else:
            print_error(f"  Service stop failed: {err}")
    except Exception as e:
        print_error(f"  Service method failed: {e}")

    # ---- 所有方法都失败，显示多语言手动指南 ----
    print_warning("  All automated methods failed. Please follow the manual steps below.")
    lang = get_current_language()
    print_info(get_manual_guide(lang))
    return False


def enable_defender_realtime():
    """重新启用 Windows Defender 实时保护"""
    print_info("  Enabling Windows Defender real-time protection...")

    # 移除注册表禁用项
    for key_path in [
        r"SOFTWARE\Policies\Microsoft\Windows Defender",
        r"SOFTWARE\Microsoft\Windows Defender\Real-Time Protection"
    ]:
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_SET_VALUE)
            winreg.DeleteValue(key, "DisableRealtimeMonitoring")
            winreg.CloseKey(key)
            print_success(f"  Removed registry key from {key_path}")
        except FileNotFoundError:
            pass
        except Exception as e:
            print_warning(f"  Registry cleanup failed for {key_path}: {e}")

    # 启用 Defender 服务
    run_powershell('Set-Service -Name WinDefend -StartupType Automatic')
    run_powershell('Start-Service -Name WinDefend -ErrorAction SilentlyContinue')

    # PowerShell 启用
    success, out, err = run_powershell('Set-MpPreference -DisableRealtimeMonitoring $false -Force')
    if success:
        print_success("  Defender real-time protection enabled.")
        return True
    else:
        print_error(f"  PowerShell failed: {err}")
        print_info("  You may need to manually enable Defender in Windows Security settings.")
        return False


def is_defender_active():
    """检查 Defender 实时保护是否启用（准确检测）"""
    # 方法1: PowerShell Get-MpComputerStatus
    success, out, err = run_powershell(
        'Get-MpComputerStatus | Select-Object -ExpandProperty RealTimeProtectionEnabled'
    )
    if success and out:
        if out.strip().lower() == 'true':
            return True
        elif out.strip().lower() == 'false':
            return False

    # 方法2: 检查注册表（策略）
    try:
        key_path = r"SOFTWARE\Policies\Microsoft\Windows Defender"
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_READ)
        value, _ = winreg.QueryValueEx(key, "DisableRealtimeMonitoring")
        winreg.CloseKey(key)
        if value == 1:
            return False
        else:
            return True
    except FileNotFoundError:
        pass
    except Exception:
        pass

    # 方法3: 检查注册表（Real-Time Protection）
    try:
        key_path = r"SOFTWARE\Microsoft\Windows Defender\Real-Time Protection"
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_READ)
        value, _ = winreg.QueryValueEx(key, "DisableRealtimeMonitoring")
        winreg.CloseKey(key)
        if value == 1:
            return False
        else:
            return True
    except FileNotFoundError:
        pass
    except Exception:
        pass

    # 方法4: 检查服务状态
    try:
        result = subprocess.run(
            ['sc', 'query', 'WinDefend'],
            capture_output=True,
            text=True
        )
        if 'RUNNING' in result.stdout:
            return True
        else:
            return False
    except:
        pass

    # 默认假设启用
    return True


def takeover_defender():
    """接管 Defender"""
    if not ctypes.windll.shell32.IsUserAnAdmin():
        print_error("  Administrator privileges required.")
        return False

    if not disable_defender_realtime():
        return False

    print_info("  Note: Full registration as default antivirus requires Microsoft certification.")
    print_info("  FalconStrike will now function as the active real-time protection.")
    print_info("  Please start FalconStrike real-time protection from menu 5.")
    return True


def restore_defender():
    """恢复 Defender"""
    if not ctypes.windll.shell32.IsUserAnAdmin():
        print_error("  Administrator privileges required.")
        return False
    return enable_defender_realtime()


def defender_status():
    """显示 Defender 状态"""
    if is_defender_active():
        print_info("  Windows Defender real-time protection is ENABLED.")
    else:
        print_warning("  Windows Defender real-time protection is DISABLED.")
    return is_defender_active()