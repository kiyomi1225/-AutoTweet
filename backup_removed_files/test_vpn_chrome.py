# test_vpn_chrome.py - VPN + Chrome統合テスト
import time
import sys
sys.path.append('.')

from modules.config_manager import ConfigManager
from modules.vpn_manager import VPNManager
from modules.chrome_manager import ChromeManager

def test_vpn_chrome_integration():
    """
    VPN + Chrome統合テスト
    """
    print("=== VPN + Chrome統合テスト開始 ===")
    
    try:
        # 初期化
        config = ConfigManager()
        vpn_manager = VPNManager(config)
        chrome_manager = ChromeManager(config)
        
        print(f"元のIP: {vpn_manager.original_ip}")
        
        # テスト対象アカウント
        test_account = "acc1"
        
        # Step 1: VPN接続
        print(f"\n[Step 1] {test_account}のVPNに接続中...")
        vpn_success = vpn_manager.connect_account_vpn(test_account)
        
        if not vpn_success:
            print("✗ VPN接続失敗")
            return False
        
        # 接続確認
        vpn_info = vpn_manager.get_connection_info()
        print(f"✓ VPN接続成功")
        print(f"  VPN IP: {vpn_info['current_ip']}")
        print(f"  接続アカウント: {vpn_info['account_id']}")
        
        # Step 2: Chrome起動
        print(f"\n[Step 2] Chrome起動中...")
        
        # IP確認用のURLを開く
        ip_check_url = "https://whatismyipaddress.com/"
        chrome_success = chrome_manager.start_chrome_profile(test_account, ip_check_url)
        
        if not chrome_success:
            print("✗ Chrome起動失敗")
            vpn_manager.disconnect()
            return False
        
        print(f"✓ Chrome起動成功")
        print(f"  URL: {ip_check_url}")
        print(f"  プロファイル: {test_account}")
        
        # Step 3: 動作確認
        print(f"\n[Step 3] 統合動作確認中...")
        print("ブラウザでVPN IPが表示されているか確認してください")
        print(f"期待されるIP: {vpn_info['current_ip']}")
        
        # 確認時間
        confirmation_time = 15
        print(f"\n{confirmation_time}秒間確認時間...")
        for i in range(confirmation_time, 0, -1):
            print(f"  残り {i} 秒 - VPNとChromeが正常動作中", end='\r')
            time.sleep(1)
        print()
        
        # Step 4: 追加テスト（ChatGPTアクセス）
        print(f"\n[Step 4] ChatGPTアクセステスト...")
        
        # アカウント設定からGPT URLを取得
        account_config = config.get_account_config(test_account)
        gpt_url = account_config.get("gpt_url", "https://chatgpt.com")
        
        # 新しいタブでChatGPTを開く
        nav_success = chrome_manager.navigate_to_url(test_account, gpt_url)
        if nav_success:
            print(f"✓ ChatGPTアクセス成功: {gpt_url}")
        else:
            print(f"⚠ ChatGPTアクセス失敗")
        
        print("\n10秒間ChatGPT動作確認...")
        time.sleep(10)
        
        # Step 5: クリーンアップ
        print(f"\n[Step 5] クリーンアップ中...")
        
        # Chrome終了
        chrome_manager.close_chrome_profile(test_account)
        print("✓ Chrome終了")
        
        # VPN切断
        vpn_manager.disconnect()
        print("✓ VPN切断")
        
        # 最終確認
        time.sleep(3)
        final_info = vpn_manager.get_connection_info()
        if final_info['current_ip'] == vpn_manager.original_ip:
            print("✓ IP復旧確認")
        else:
            print("⚠ IP未復旧")
        
        print("\n=== VPN + Chrome統合テスト完了 ===")
        return True
        
    except Exception as e:
        print(f"✗ テストエラー: {str(e)}")
        
        # エラー時のクリーンアップ
        try:
            chrome_manager.close_all_profiles()
            vpn_manager.disconnect()
        except:
            pass
        
        import traceback
        traceback.print_exc()
        return False

def test_multiple_accounts():
    """
    複数アカウントの連続テスト
    """
    print("=== 複数アカウント連続テスト開始 ===")
    
    try:
        config = ConfigManager()
        vpn_manager = VPNManager(config)
        chrome_manager = ChromeManager(config)
        
        # 全アカウント取得
        accounts = config.get_all_accounts()
        print(f"テスト対象アカウント: {accounts}")
        
        for i, account_id in enumerate(accounts):
            print(f"\n--- アカウント {i+1}/{len(accounts)}: {account_id} ---")
            
            # VPN接続
            print(f"VPN接続中: {account_id}")
            if not vpn_manager.connect_account_vpn(account_id):
                print(f"✗ VPN接続失敗: {account_id}")
                continue
            
            vpn_info = vpn_manager.get_connection_info()
            print(f"✓ VPN接続: {vpn_info['current_ip']}")
            
            # Chrome起動
            print(f"Chrome起動中: {account_id}")
            if not chrome_manager.start_chrome_profile(account_id):
                print(f"✗ Chrome起動失敗: {account_id}")
                vpn_manager.disconnect()
                continue
            
            print(f"✓ Chrome起動成功")
            
            # 短時間確認
            print("5秒間動作確認...")
            time.sleep(5)
            
            # クリーンアップ
            chrome_manager.close_chrome_profile(account_id)
            vpn_manager.disconnect()
            print(f"✓ {account_id} 完了")
            
            # 次のアカウントまで待機
            if i < len(accounts) - 1:
                print("次のアカウントまで3秒待機...")
                time.sleep(3)
        
        print("\n=== 複数アカウント連続テスト完了 ===")
        return True
        
    except Exception as e:
        print(f"✗ 複数アカウントテストエラー: {str(e)}")
        return False

def main():
    """
    メイン実行関数
    """
    print("VPN + Chrome統合テストメニュー")
    print("1. 単一アカウントテスト（詳細確認）")
    print("2. 複数アカウント連続テスト")
    print("3. 終了")
    
    while True:
        choice = input("\n選択してください (1-3): ")
        
        if choice == "1":
            test_vpn_chrome_integration()
            break
        elif choice == "2":
            test_multiple_accounts()
            break
        elif choice == "3":
            print("テストを終了します")
            break
        else:
            print("無効な選択です。1-3を入力してください。")

if __name__ == "__main__":
    # 事前チェック
    print("VPN + Chrome統合テストの事前確認:")
    
    from pathlib import Path
    
    # 認証ファイル確認
    auth_file = Path("config/auth.txt")
    if not auth_file.exists():
        print("✗ config/auth.txt が存在しません")
        exit(1)
    else:
        print("✓ 認証ファイル存在")
    
    # VPNファイル確認
    ovpn_dir = Path("config/ovpn")
    ovpn_files = list(ovpn_dir.glob("*.ovpn")) if ovpn_dir.exists() else []
    if not ovpn_files:
        print("✗ config/ovpn/ にVPNファイルがありません")
        exit(1)
    else:
        print(f"✓ VPNファイル: {len(ovpn_files)}件")
    
    # Chrome確認
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
    ]
    
    chrome_found = any(Path(path).exists() for path in chrome_paths)
    if not chrome_found:
        print("✗ Google Chromeが見つかりません")
        exit(1)
    else:
        print("✓ Google Chrome存在")
    
    print("\n事前確認完了！")
    main()