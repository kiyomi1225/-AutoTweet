# fix_tap_device.py - TAPデバイス指定修正
import subprocess
import sys
from pathlib import Path
sys.path.append('.')

from modules.config_manager import ConfigManager

def get_available_tap_devices():
    """
    利用可能なTAPデバイスを取得
    """
    print("=== 利用可能なTAPデバイス確認 ===")
    
    try:
        # PowerShellでTAPアダプター情報を取得
        result = subprocess.run([
            "powershell", "-Command",
            "Get-NetAdapter | Where-Object {$_.InterfaceDescription -like '*TAP*' -and $_.Status -eq 'Up'} | Select-Object Name, InterfaceDescription, InterfaceGuid"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("利用可能なTAPアダプター:")
            print(result.stdout)
            return result.stdout
        else:
            print("TAPアダプター取得エラー")
            return None
            
    except Exception as e:
        print(f"エラー: {str(e)}")
        return None

def test_openvpn_with_device():
    """
    特定のTAPデバイスを指定してOpenVPNテスト
    """
    print("\n=== OpenVPN TAPデバイス指定テスト ===")
    
    config = ConfigManager()
    vpn_config = config.get_vpn_config()
    account_config = config.get_account_config("acc1")
    
    # OpenVPNコマンド（デバイス自動選択）
    cmd = [
        r"C:\Program Files\OpenVPN\bin\openvpn.exe",
        "--config", str(Path(vpn_config["ovpn_dir"]) / account_config["vpn_file"]),
        "--auth-user-pass", str(Path(vpn_config["auth_file"])),
        "--dev", "tun",  # TUNデバイス使用
        "--dev-type", "tun",  # 明示的にTUN指定
        "--verb", "3",
        "--log", "logs/openvpn_fixed.log",
        "--script-security", "2",
        "--route-delay", "5"  # ルート設定の遅延
    ]
    
    print("修正されたOpenVPNコマンド:")
    print(" ".join(f'"{arg}"' if " " in arg else arg for arg in cmd))
    
    # ログディレクトリ作成
    Path("logs").mkdir(exist_ok=True)
    
    print(f"\nOpenVPN実行開始 (15秒間)...")
    
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        import time
        time.sleep(15)
        
        if process.poll() is None:
            print("✓ OpenVPN正常実行中")
            
            # プロセス終了
            process.terminate()
            try:
                stdout, stderr = process.communicate(timeout=5)
                print("✓ プロセス正常終了")
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
                print("⚠ プロセス強制終了")
            
            # ログ確認
            log_file = Path("logs/openvpn_fixed.log")
            if log_file.exists():
                print(f"\n=== 修正版OpenVPNログ（最後の500文字）===")
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    log_content = f.read()
                    print(log_content[-500:])
                return True
            else:
                print("⚠ ログファイルが作成されませんでした")
                
        else:
            stdout, stderr = process.communicate()
            print("✗ OpenVPNプロセスが予期せず終了")
            print(f"stdout: {stdout}")
            print(f"stderr: {stderr}")
            
        return False
        
    except Exception as e:
        print(f"✗ OpenVPN実行エラー: {str(e)}")
        return False

def update_vpn_manager_with_fix():
    """
    VPNManagerの設定を修正
    """
    print(f"\n=== VPNManager設定修正 ===")
    
    config = ConfigManager()
    config_data = config.config_data
    
    # VPN設定にTAPデバイス設定を追加
    config_data["vpn"]["device_type"] = "tun"
    config_data["vpn"]["use_dev_type"] = True
    config_data["vpn"]["script_security"] = "2"
    config_data["vpn"]["route_delay"] = "5"
    
    config._save_config(config_data)
    print("✓ VPN設定更新完了")
    print("  - デバイスタイプ: TUN")
    print("  - スクリプトセキュリティ: 2")
    print("  - ルート遅延: 5秒")

def main():
    """
    メイン実行
    """
    print("TAPデバイス問題の修正を開始します\n")
    
    # 利用可能なTAPデバイス確認
    get_available_tap_devices()
    
    # OpenVPNテスト（修正版）
    test_result = test_openvpn_with_device()
    
    if test_result:
        print("\n✓ 修正版OpenVPNテスト成功")
        
        # 設定更新
        update_vpn_manager_with_fix()
        
        print("\n🎉 TAPデバイス問題修正完了！")
        print("\n次のステップ:")
        print("1. python test_vpn_connection.py でVPN単体テスト")
        print("2. python test_vpn_chrome.py で統合テスト")
        
    else:
        print("\n⚠ 修正版でも問題が続いています")
        print("手動でのOpenVPN設定調整が必要かもしれません")

if __name__ == "__main__":
    main()