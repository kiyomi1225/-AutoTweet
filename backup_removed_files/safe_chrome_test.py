# safe_chrome_test.py - 安全なChrome実行テスト
import sys
import time

def safe_chrome_test():
    """
    安全なChrome実行テスト（CMDクラッシュ回避）
    """
    print("=== 安全Chrome実行テスト ===")
    
    try:
        # final_chrome_manager.pyが存在するか確認
        from pathlib import Path
        if not Path("final_chrome_manager.py").exists():
            print("✗ final_chrome_manager.py が見つかりません")
            print("先に simple_update_config.py を実行してください")
            return False
        
        # 安全にインポート
        print("FinalChromeManager インポート中...")
        
        import importlib.util
        spec = importlib.util.spec_from_file_location("final_chrome_manager", "final_chrome_manager.py")
        if spec is None:
            print("✗ モジュールspecが作成できません")
            return False
        
        final_chrome_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(final_chrome_module)
        
        print("✓ FinalChromeManager インポート成功")
        
        # Chromeマネージャーインスタンス作成
        chrome = final_chrome_module.FinalChromeManager()
        print("✓ FinalChromeManager インスタンス作成成功")
        
        # Chrome起動テスト
        print("\nChrome起動テスト実行...")
        print("※警告が出てもChromeが開けば成功です")
        
        success = chrome.start_chrome("acc1", "https://www.google.com")
        
        if success:
            print("✓ Chrome起動成功")
            print("✓ アクティブアカウント:", chrome.get_active_accounts())
            
            print("\n5秒間動作確認中...")
            time.sleep(5)
            
            print("Chrome終了中...")
            chrome.close_chrome("acc1")
            print("✓ Chrome終了完了")
            
            return True
        else:
            print("✗ Chrome起動失敗")
            return False
            
    except Exception as e:
        print(f"✗ テストエラー: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_vpn_chrome_separately():
    """
    VPNとChromeを別々にテスト
    """
    print(f"\n=== VPN + Chrome 別々テスト ===")
    
    try:
        sys.path.append('.')
        from modules.config_manager import ConfigManager
        from modules.vpn_manager import VPNManager
        
        config = ConfigManager()
        vpn_manager = VPNManager(config)
        
        print(f"元のIP: {vpn_manager.original_ip}")
        
        # VPN接続
        print("\n[Step 1] VPN接続テスト...")
        vpn_success = vpn_manager.connect_account_vpn("acc1")
        
        if vpn_success:
            info = vpn_manager.get_connection_info()
            print(f"✓ VPN接続成功: {info['current_ip']}")
            
            # VPN接続したままChrome起動テスト
            print(f"\n[Step 2] VPN接続状態でChrome起動テスト...")
            chrome_success = safe_chrome_test()
            
            if chrome_success:
                print(f"✓ VPN + Chrome 統合成功！")
                result = True
            else:
                print(f"✗ Chrome部分で失敗")
                result = False
            
        else:
            print(f"✗ VPN接続失敗")
            result = False
        
        # VPN切断
        if vpn_success:
            print(f"\n[Step 3] VPN切断...")
            vpn_manager.disconnect()
            print(f"✓ VPN切断完了")
        
        return result
        
    except Exception as e:
        print(f"✗ VPN + Chrome テストエラー: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("安全なChrome実行テストを開始します\n")
    
    # Chrome単体テスト
    print("[テスト1] Chrome単体テスト")
    chrome_result = safe_chrome_test()
    
    if chrome_result:
        print("\n✓ Chrome単体テスト成功")
        
        # VPN + Chrome統合テスト
        print("\n[テスト2] VPN + Chrome統合テスト")
        integration_result = test_vpn_chrome_separately()
        
        if integration_result:
            print(f"\n🎉 全システム動作確認完了！")
            print(f"VPN + Chrome 完全統合成功！")
            print(f"\n次の開発段階:")
            print(f"1. GPT Fetcher - ChatGPTからツイート取得")
            print(f"2. Tweet Poster - Twitter自動投稿")
            print(f"3. Main Controller - 24時間自動運用")
        else:
            print(f"\n⚠ 統合テストで問題発生")
    else:
        print(f"\n⚠ Chrome単体テストで問題発生")
        print(f"Chrome問題の詳細調査が必要です")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"メイン実行エラー: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        input("\n何かキーを押すと終了します...")  # CMDが閉じないように