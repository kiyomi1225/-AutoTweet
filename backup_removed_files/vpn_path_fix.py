# vpn_path_fix.py - VPN実行パス修正
import subprocess
import sys
import time
from pathlib import Path
sys.path.append('.')

from modules.config_manager import ConfigManager

def test_openvpn_paths():
    """
    OpenVPN実行パスのテスト
    """
    print("=== OpenVPN実行パステスト ===")
    
    possible_paths = [
        r"C:\Program Files\OpenVPN\bin\openvpn.exe",
        r"C:\Program Files (x86)\OpenVPN\bin\openvpn.exe",
        "openvpn.exe",
        "openvpn"
    ]
    
    working_path = None
    
    for path in possible_paths:
        print(f"\n[テスト] {path}")
        try:
            result = subprocess.run(
                [path, "--version"], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            
            if result.returncode == 0:
                print(f"✓ 動作確認: {path}")
                print(f"  出力: {result.stdout.strip()}")
                working_path = path
                break
            else:
                print(f"✗ エラー: {result.stderr}")
                
        except FileNotFoundError:
            print("✗ ファイルが見つかりません")
        except subprocess.TimeoutExpired:
            print("✗ タイムアウト")
        except Exception as e:
            print(f"✗ エラー: {str(e)}")
    
    return working_path

def test_manual_vpn_connection():
    """
    手動VPN接続テスト
    """
    print("\n=== 手動VPN接続テスト ===")
    
    config = ConfigManager()
    vpn_config = config.get_vpn_config()
    account_config = config.get_account_config("acc1")
    
    if not account_config:
        print("✗ アカウント設定が見つかりません")
        return False
    
    # OpenVPN実行パス取得
    working_path = test_openvpn_paths()
    if not working_path:
        print("✗ 動作するOpenVPNが見つかりません")
        return False
    
    print(f"\n使用するOpenVPN: {working_path}")
    
    # VPNファイルパス
    ovpn_file = Path(vpn_config["ovpn_dir"]) / account_config["vpn_file"]
    auth_file = Path(vpn_config["auth_file"])
    
    print(f"VPNファイル: {ovpn_file}")
    print(f"認証ファイル: {auth_file}")
    
    # 手動VPN接続コマンド
    cmd = [
        working_path,
        "--config", str(ovpn_file),
        "--auth-user-pass", str(auth_file),
        "--verb", "3",
        "--log", "logs/openvpn_manual.log"
    ]
    
    print(f"\n実行コマンド:")
    print(" ".join(cmd))
    
    print(f"\n手動VPN接続開始...")
    print("※15秒後に自動終了します")
    
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # 15秒待機
        time.sleep(15)
        
        # プロセス状態確認
        if process.poll() is None:
            print("✓ OpenVPNプロセス実行中")
            
            # プロセス終了
            process.terminate()
            try:
                process.wait(timeout=5)
                print("✓ プロセス正常終了")
            except subprocess.TimeoutExpired:
                process.kill()
                print("⚠ プロセス強制終了")
            
            # ログ確認
            log_file = Path("logs/openvpn_manual.log")
            if log_file.exists():
                print("\n=== OpenVPNログ ===")
                with open(log_file, 'r') as f:
                    log_content = f.read()
                    print(log_content[-500:])  # 最後の500文字
                return True
            else:
                print("⚠ ログファイルが作成されませんでした")
                
        else:
            # プロセスが終了している
            stdout, stderr = process.communicate()
            print("✗ OpenVPNプロセスが予期せず終了")
            print(f"stdout: {stdout}")
            print(f"stderr: {stderr}")
            
        return False
        
    except Exception as e:
        print(f"✗ 手動VPN接続エラー: {str(e)}")
        return False

def update_vpn_manager_config():
    """
    VPNManager設定を更新
    """
    print("\n=== VPNManager設定更新 ===")
    
    working_path = test_openvpn_paths()
    if not working_path:
        print("✗ 動作するOpenVPNが見つかりません")
        return False
    
    # 設定ファイル更新
    config = ConfigManager()
    config_data = config.config_data
    
    # OpenVPN実行パスを設定に追加
    config_data["vpn"]["openvpn_executable"] = working_path
    config_data["vpn"]["connection_timeout"] = 45  # タイムアウト延長
    config_data["vpn"]["retry_count"] = 3
    
    # ログディレクトリ作成
    Path("logs").mkdir(exist_ok=True)
    
    config._save_config(config_data)
    print(f"✓ VPNManager設定更新完了")
    print(f"  OpenVPN実行パス: {working_path}")
    print(f"  接続タイムアウト: 45秒")
    
    return True

def main():
    """
    メイン実行
    """
    print("VPN実行パス問題の修正を開始します\n")
    
    # OpenVPN実行パステスト
    working_path = test_openvpn_paths()
    
    if working_path:
        print(f"\n✓ 動作するOpenVPN発見: {working_path}")
        
        # 手動VPN接続テスト
        manual_test = test_manual_vpn_connection()
        
        if manual_test:
            print("\n✓ 手動VPN接続テスト成功")
            
            # 設定更新
            config_updated = update_vpn_manager_config()
            
            if config_updated:
                print("\n🎉 VPN修正完了！")
                print("\n次のステップ:")
                print("1. python test_vpn_connection.py でVPN単体テスト")
                print("2. python test_vpn_chrome.py で統合テスト")
            else:
                print("\n⚠ 設定更新に失敗しました")
        else:
            print("\n⚠ 手動VPN接続テストに失敗しました")
            print("認証情報やVPNファイルを確認してください")
    else:
        print("\n✗ 動作するOpenVPNが見つかりません")
        print("\nOpenVPNのインストールが必要です:")
        print("https://openvpn.net/download-open-vpn/")

if __name__ == "__main__":
    main()