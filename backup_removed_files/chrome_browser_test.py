# chrome_browser_test.py - Chrome実際起動テスト
import subprocess
import time
import sys
import psutil
sys.path.append('.')

from modules.config_manager import ConfigManager
from modules.chrome_manager import ChromeManager

def test_chrome_browser_only():
    """
    --versionテストをスキップして実際のブラウザ起動のみテスト
    """
    print("=== Chrome実際起動テスト開始 ===")
    
    try:
        config = ConfigManager()
        chrome_manager = ChromeManager(config)
        
        chrome_path = chrome_manager.chrome_executable
        print(f"Chrome実行パス: {chrome_path}")
        
        # テスト1: 基本Chrome起動
        print("\n" + "="*50)
        print("[テスト1] Chrome基本起動テスト")
        
        print("Chrome起動中...")
        try:
            process = subprocess.Popen([
                chrome_path,
                "--new-window",
                "https://www.google.com"
            ])
            
            print("3秒後にプロセス確認...")
            time.sleep(3)
            
            # Chromeプロセス確認
            chrome_running = False
            for proc in psutil.process_iter(['pid', 'name']):
                if 'chrome' in proc.info['name'].lower():
                    chrome_running = True
                    print(f"✓ Chromeプロセス発見: PID {proc.info['pid']}")
                    break
            
            if chrome_running:
                print("✅ Chrome基本起動成功")
                
                # Chrome終了
                print("Chrome終了中...")
                for proc in psutil.process_iter(['pid', 'name']):
                    if 'chrome' in proc.info['name'].lower():
                        proc.kill()
                
                time.sleep(2)
                print("✓ Chrome終了完了")
                
            else:
                print("❌ Chrome起動失敗")
                return False
                
        except Exception as e:
            print(f"❌ Chrome起動エラー: {str(e)}")
            return False
        
        # テスト2: プロファイル指定起動
        print("\n" + "="*50)
        print("[テスト2] Chromeプロファイル指定起動テスト")
        
        print("プロファイル指定でChrome起動中...")
        try:
            process = subprocess.Popen([
                chrome_path,
                "--user-data-dir=chrome_test_profiles",
                "--profile-directory=test_profile",
                "--new-window",
                "https://www.google.com"
            ])
            
            time.sleep(3)
            
            chrome_running = False
            for proc in psutil.process_iter(['pid', 'name']):
                if 'chrome' in proc.info['name'].lower():
                    chrome_running = True
                    break
            
            if chrome_running:
                print("✅ Chromeプロファイル起動成功")
                
                # Chrome終了
                for proc in psutil.process_iter(['pid', 'name']):
                    if 'chrome' in proc.info['name'].lower():
                        proc.kill()
                
                time.sleep(2)
                print("✓ Chrome終了完了")
                
            else:
                print("❌ Chromeプロファイル起動失敗")
                return False
                
        except Exception as e:
            print(f"❌ Chromeプロファイル起動エラー: {str(e)}")
            return False
        
        # テスト3: ChromeManager経由テスト
        print("\n" + "="*50)
        print("[テスト3] ChromeManager経由テスト")
        
        test_account = "acc1"
        print(f"ChromeManager経由でアカウント {test_account} 起動中...")
        
        try:
            success = chrome_manager.start_chrome_profile(test_account, "https://www.google.com")
            
            if success:
                print("✅ ChromeManager起動成功")
                
                # アクティブプロファイル確認
                active_profiles = chrome_manager.get_active_profiles()
                print(f"✓ アクティブプロファイル: {active_profiles}")
                
                # プロファイル情報取得
                info = chrome_manager.get_profile_info(test_account)
                print(f"✓ プロファイル情報: {info}")
                
                print("5秒間動作確認...")
                time.sleep(5)
                
                # Chrome終了
                chrome_manager.close_chrome_profile(test_account)
                print("✓ ChromeManager終了成功")
                
            else:
                print("❌ ChromeManager起動失敗")
                return False
                
        except Exception as e:
            print(f"❌ ChromeManager テストエラー: {str(e)}")
            return False
        
        print("\n" + "="*50)
        print("🎉 Chrome実際起動テスト完了 - 全て成功！")
        print("="*50)
        
        print("\n次のステップ:")
        print("1. python test_vpn_chrome.py でVPN統合テスト")
        print("2. 実際のTwitter自動化開発開始")
        
        return True
        
    except Exception as e:
        print(f"❌ テスト全体エラー: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_chrome_browser_only()