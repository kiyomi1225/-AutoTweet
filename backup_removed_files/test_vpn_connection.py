# test_vpn_connection.py - VPN接続テスト
import time
import sys
sys.path.append('.')

from modules.config_manager import ConfigManager
from modules.vpn_manager import VPNManager

def test_vpn_connection():
    """
    実際のVPN接続テスト
    """
    print("=== VPN接続テスト開始 ===")
    
    try:
        # 初期化
        config = ConfigManager()
        vpn_manager = VPNManager(config)
        
        print(f"元のIP: {vpn_manager.original_ip}")
        
        # acc1のVPNに接続
        print("\nacc1のVPNに接続中...")
        success = vpn_manager.connect_account_vpn("acc1")
        
        if success:
            print("✓ VPN接続成功！")
            
            # 接続情報表示
            info = vpn_manager.get_connection_info()
            print(f"  現在のIP: {info['current_ip']}")
            print(f"  接続アカウント: {info['account_id']}")
            
            # 10秒待機
            print("\n10秒間待機中...")
            for i in range(10, 0, -1):
                print(f"  残り {i} 秒", end='\r')
                time.sleep(1)
            print()
            
        else:
            print("✗ VPN接続失敗")
            return
        
        # VPN切断
        print("VPN切断中...")
        vpn_manager.disconnect()
        
        # 切断確認
        time.sleep(3)
        final_info = vpn_manager.get_connection_info()
        print(f"切断後のIP: {final_info['current_ip']}")
        
        if final_info['current_ip'] == vpn_manager.original_ip:
            print("✓ IP復旧確認")
        else:
            print("⚠ IP未復旧")
        
        print("\n=== VPN接続テスト完了 ===")
        
    except Exception as e:
        print(f"✗ テストエラー: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # 事前チェック
    print("VPN接続の事前確認:")
    
    from pathlib import Path
    
    # 認証ファイル確認
    auth_file = Path("config/auth.txt")
    if not auth_file.exists():
        print("✗ config/auth.txt が存在しません")
        print("  NordVPNの認証情報を設定してください:")
        print("  1行目: ユーザー名")
        print("  2行目: パスワード")
        exit(1)
    else:
        print("✓ 認証ファイル存在")
    
    # VPNファイル確認
    ovpn_dir = Path("config/ovpn")
    ovpn_files = list(ovpn_dir.glob("*.ovpn")) if ovpn_dir.exists() else []
    if not ovpn_files:
        print("✗ config/ovpn/ にVPNファイルがありません")
        print("  NordVPNの.ovpnファイルを配置してください")
        exit(1)
    else:
        print(f"✓ VPNファイル: {len(ovpn_files)}件")
    
    # OpenVPN確認
    import subprocess
    try:
        subprocess.run(["openvpn", "--version"], 
                      capture_output=True, timeout=5)
        print("✓ OpenVPN実行可能")
    except:
        print("⚠ OpenVPNが見つかりません（実行時にエラーの可能性）")
    
    print("\n事前確認完了。VPN接続テストを開始しますか？")
    response = input("続行する場合は 'y' を入力: ")
    
    if response.lower() == 'y':
        test_vpn_connection()
    else:
        print("テストをキャンセルしました")