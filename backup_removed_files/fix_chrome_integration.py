# test_simple_chrome.py - シンプルChrome起動テスト
import sys
import time
sys.path.append('.')

from modules.config_manager import ConfigManager
from modules.chrome_manager import ChromeManager

def test_simple_chrome_start():
    """
    最もシンプルなChrome起動テスト
    """
    print("=== シンプルChrome起動テスト ===")
    
    try:
        config = ConfigManager()
        chrome_manager = ChromeManager(config)
        
        test_account = "acc1"
        url = "https://www.google.com"
        
        print(f"Chrome起動テスト: {test_account} -> {url}")
        
        success = chrome_manager.start_chrome_profile(test_account, url)
        
        if success:
            print("✓ Chrome起動成功")
            
            # アクティブプロファイル確認
            active_profiles = chrome_manager.get_active_profiles()
            print(f"✓ アクティブプロファイル: {active_profiles}")
            
            # プロファイル情報
            info = chrome_manager.get_profile_info(test_account)
            print(f"✓ プロファイル情報: {info}")
            
            print("5秒間動作確認...")
            time.sleep(5)
            
            # Chrome終了
            chrome_manager.close_chrome_profile(test_account)
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

def main():
    print("修正版ChromeManagerテストを開始します\n")
    
    result = test_simple_chrome_start()
    
    if result:
        print("\n🎉 Chrome修正成功！")
        print("\n次のステップ:")
        print("1. python test_vpn_chrome.py で統合テスト")
        print("2. 成功したらGPT Fetcher開発開始")
    else:
        print("\n⚠ Chrome問題が続いています")
        print("さらなる調査が必要です")

if __name__ == "__main__":
    main()# fix_chrome_integration.py - Chrome統合問題修正
import subprocess
import time
import sys
import psutil
from pathlib import Path
sys.path.append('.')

from modules.config_manager import ConfigManager
from modules.chrome_manager import ChromeManager

def cleanup_chrome_processes():
    """
    すべてのChromeプロセスを終了
    """
    print("=== Chrome プロセスクリーンアップ ===")
    
    killed_count = 0
    try:
        for proc in psutil.process_iter(['pid', 'name']):
            if 'chrome' in proc.info['name'].lower():
                try:
                    proc.kill()
                    killed_count += 1
                    print(f"Chrome プロセス終了: PID {proc.info['pid']}")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        
        if killed_count > 0:
            print(f"✓ {killed_count}個のChromeプロセスを終了しました")
            time.sleep(3)
        else:
            print("✓ 実行中のChromeプロセスはありません")
            
    except Exception as e:
        print(f"⚠ プロセスクリーンアップエラー: {str(e)}")

def fix_chrome_profiles():
    """
    Chromeプロファイル問題を修正
    """
    print("\n=== Chrome プロファイル修復 ===")
    
    try:
        # 既存のプロファイルディレクトリを削除
        profile_dirs = [
            "chrome_profiles",
            "chrome_test_profiles"
        ]
        
        for profile_dir in profile_dirs:
            if Path(profile_dir).exists():
                import shutil
                shutil.rmtree(profile_dir)
                print(f"✓ {profile_dir} 削除完了")
        
        # 新しいプロファイルディレクトリ作成
        Path("chrome_profiles").mkdir(exist_ok=True)
        Path("chrome_profiles/acc1").mkdir(exist_ok=True)
        Path("chrome_profiles/acc2").mkdir(exist_ok=True)
        
        print("✓ 新しいプロファイルディレクトリ作成完了")
        
    except Exception as e:
        print(f"⚠ プロファイル修復エラー: {str(e)}")

def test_chrome_basic():
    """
    Chrome基本動作テスト
    """
    print("\n=== Chrome 基本動作テスト ===")
    
    try:
        config = ConfigManager()
        chrome_manager = ChromeManager(config)
        
        chrome_path = chrome_manager.chrome_executable
        print(f"Chrome実行パス: {chrome_path}")
        
        if not Path(chrome_path).exists():
            print(f"✗ Chrome実行ファイルが見つかりません: {chrome_path}")
            return False
        
        # 最もシンプルなChrome起動テスト
        print("Chrome起動テスト中...")
        
        cmd = [
            chrome_path,
            "--no-sandbox",
            "--disable-dev-shm-usage", 
            "--new-window",
            "https://www.google.com"
        ]
        
        process = subprocess.Popen(cmd)
        
        # 5秒待機
        time.sleep(5)
        
        # Chromeプロセス確認
        chrome_running = False
        for proc in psutil.process_iter(['pid', 'name']):
            if 'chrome' in proc.info['name'].lower():
                chrome_running = True
                break
        
        if chrome_running:
            print("✓ Chrome基本起動成功")
            
            # Chrome終了
            cleanup_chrome_processes()
            return True
        else:
            print("✗ Chrome基本起動失敗")
            return False
            
    except Exception as e:
        print(f"✗ Chrome基本テストエラー: {str(e)}")
        return False

def test_chrome_manager():
    """
    ChromeManager経由テスト
    """
    print("\n=== ChromeManager 動作テスト ===")
    
    try:
        config = ConfigManager()
        chrome_manager = ChromeManager(config)
        
        test_account = "acc1"
        
        print(f"ChromeManager経由でアカウント {test_account} 起動中...")
        
        success = chrome_manager.start_chrome_profile(test_account, "https://www.google.com")
        
        if success:
            print("✓ ChromeManager起動成功")
            
            # アクティブプロファイル確認
            active_profiles = chrome_manager.get_active_profiles()
            print(f"✓ アクティブプロファイル: {active_profiles}")
            
            # 5秒待機
            time.sleep(5)
            
            # Chrome終了
            chrome_manager.close_chrome_profile(test_account)
            print("✓ ChromeManager終了成功")
            
            return True
        else:
            print("✗ ChromeManager起動失敗")
            return False
            
    except Exception as e:
        print(f"✗ ChromeManagerテストエラー: {str(e)}")
        return False

def main():
    """
    メイン実行
    """
    print("Chrome統合問題修正を開始します\n")
    
    # Step 1: プロセスクリーンアップ
    cleanup_chrome_processes()
    
    # Step 2: プロファイル修復
    fix_chrome_profiles()
    
    # Step 3: Chrome基本テスト
    basic_result = test_chrome_basic()
    
    if not basic_result:
        print("\n⚠ Chrome基本動作に問題があります")
        print("Chrome再インストールが必要かもしれません")
        return False
    
    # Step 4: ChromeManager テスト
    manager_result = test_chrome_manager()
    
    if manager_result:
        print("\n🎉 Chrome統合問題修正完了！")
        print("\n次のステップ:")
        print("1. python test_vpn_chrome.py で統合テスト再実行")
        print("2. 成功したらGPT Fetcher開発開始")
        return True
    else:
        print("\n⚠ ChromeManager に問題があります")
        print("設定ファイルやプロファイル設定を確認してください")
        return False

if __name__ == "__main__":
    main()