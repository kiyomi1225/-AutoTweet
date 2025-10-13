# force_fix_chrome.py - Chrome強制修正
import subprocess
import time
import sys
from pathlib import Path

def test_chrome_with_safe_encoding():
    """
    安全なエンコーディングでChrome起動テスト
    """
    print("=== Chrome安全エンコーディングテスト ===")
    
    # Chrome実行ファイル
    chrome_exe = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    
    if not Path(chrome_exe).exists():
        print(f"✗ Chrome実行ファイルが見つかりません: {chrome_exe}")
        return False
    
    # 最もシンプルなコマンド
    cmd = [
        chrome_exe,
        "--user-data-dir=chrome_profiles",
        "--profile-directory=acc1", 
        "--no-first-run",
        "--new-window",
        "https://www.google.com"
    ]
    
    print("Chrome起動コマンド:")
    for arg in cmd:
        print(f"  {arg}")
    
    try:
        print("\nChrome起動中...")
        
        # エンコーディングエラーを完全に回避
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,  # 出力を無視
            stderr=subprocess.DEVNULL,  # エラー出力を無視
            text=False  # バイナリモード
        )
        
        # 5秒待機
        time.sleep(5)
        
        if process.poll() is None:
            print("✓ Chrome起動成功（エンコーディング問題回避）")
            
            # Chromeプロセス確認
            import psutil
            chrome_processes = []
            for proc in psutil.process_iter(['pid', 'name']):
                if 'chrome' in proc.info['name'].lower():
                    chrome_processes.append(proc.info['pid'])
            
            print(f"✓ Chromeプロセス数: {len(chrome_processes)}")
            
            # プロセス終了
            process.terminate()
            try:
                process.wait(timeout=5)
                print("✓ Chrome正常終了")
            except subprocess.TimeoutExpired:
                process.kill()
                print("⚠ Chrome強制終了")
            
            # 残存プロセスクリーンアップ
            for pid in chrome_processes:
                try:
                    p = psutil.Process(pid)
                    p.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            print("✓ Chromeプロセスクリーンアップ完了")
            return True
        else:
            print("✗ Chrome起動失敗")
            return False
            
    except Exception as e:
        print(f"✗ Chrome起動エラー: {str(e)}")
        return False

def test_vpn_chrome_integration():
    """
    VPN + Chrome統合テスト（エンコーディング安全版）
    """
    print("\n=== VPN + Chrome統合テスト（安全版）===")
    
    try:
        sys.path.append('.')
        from modules.config_manager import ConfigManager
        from modules.vpn_manager import VPNManager
        
        # VPN接続
        config = ConfigManager()
        vpn_manager = VPNManager(config)
        
        print(f"元のIP: {vpn_manager.original_ip}")
        
        print("\nVPN接続中...")
        vpn_success = vpn_manager.connect_account_vpn("acc1")
        
        if vpn_success:
            info = vpn_manager.get_connection_info()
            print(f"✓ VPN接続成功: {info['current_ip']}")
            
            # Chrome起動（安全版）
            print("\nChrome起動（安全版）...")
            chrome_success = test_chrome_with_safe_encoding()
            
            if chrome_success:
                print("✓ VPN + Chrome統合成功！")
                
                print("\n10秒間動作確認...")
                time.sleep(10)
                
                result = True
            else:
                print("✗ Chrome起動部分で失敗")
                result = False
            
            # VPN切断
            print("\nVPN切断中...")
            vpn_manager.disconnect()
            print("✓ VPN切断完了")
            
            return result
        else:
            print("✗ VPN接続失敗")
            return False
            
    except Exception as e:
        print(f"✗ 統合テストエラー: {str(e)}")
        return False

def main():
    print("Chrome強制修正テストを開始します\n")
    
    # Chrome単体テスト
    chrome_result = test_chrome_with_safe_encoding()
    
    if chrome_result:
        print("\n✓ Chrome単体テスト成功")
        
        # VPN統合テスト
        integration_result = test_vpn_chrome_integration()
        
        if integration_result:
            print("\n🎉 VPN + Chrome統合完全成功！")
            print("\n次のステップ:")
            print("1. GPT Fetcher開発")
            print("2. Tweet Poster開発") 
            print("3. 24時間自動運用システム完成")
        else:
            print("\n⚠ 統合テストで問題発生")
    else:
        print("\n⚠ Chrome単体テストで問題発生")

if __name__ == "__main__":
    main()