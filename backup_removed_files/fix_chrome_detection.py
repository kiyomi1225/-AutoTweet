# fix_chrome_detection.py - Chrome起動判定修正
import subprocess
import time
import psutil
from pathlib import Path

def test_chrome_with_process_detection():
    """
    プロセス検出でChrome起動確認
    """
    print("=== Chrome起動判定修正テスト ===")
    
    chrome_exe = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    
    # 起動前のChromeプロセス数を記録
    def count_chrome_processes():
        count = 0
        for proc in psutil.process_iter(['pid', 'name']):
            if 'chrome' in proc.info['name'].lower():
                count += 1
        return count
    
    initial_chrome_count = count_chrome_processes()
    print(f"起動前Chromeプロセス数: {initial_chrome_count}")
    
    # テストパターン
    patterns = [
        {
            "name": "プロファイル指定（絶対パス）",
            "cmd": [
                chrome_exe,
                f"--user-data-dir={Path('chrome_profiles').absolute()}",
                "--profile-directory=acc1",
                "https://www.google.com"
            ]
        },
        {
            "name": "プロファイル指定（相対パス）", 
            "cmd": [
                chrome_exe,
                "--user-data-dir=chrome_profiles",
                "--profile-directory=acc1",
                "https://www.google.com"
            ]
        },
        {
            "name": "プロファイルなし",
            "cmd": [
                chrome_exe,
                "https://www.google.com"
            ]
        }
    ]
    
    successful_pattern = None
    
    for i, pattern in enumerate(patterns):
        print(f"\n[テスト {i+1}] {pattern['name']}")
        
        # プロファイルディレクトリ作成
        Path("chrome_profiles").mkdir(exist_ok=True)
        Path("chrome_profiles/acc1").mkdir(exist_ok=True)
        
        print(f"実行コマンド:")
        for arg in pattern['cmd']:
            print(f"  {arg}")
        
        try:
            # Chrome起動
            process = subprocess.Popen(
                pattern['cmd'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            print(f"Chrome起動コマンド実行完了")
            
            # プロセス検出で確認（Chromeは複数プロセスで動作）
            print(f"5秒待機してプロセス確認...")
            time.sleep(5)
            
            current_chrome_count = count_chrome_processes()
            print(f"現在のChromeプロセス数: {current_chrome_count}")
            
            if current_chrome_count > initial_chrome_count:
                print(f"✓ {pattern['name']} 起動成功（プロセス数増加）")
                successful_pattern = pattern
                
                # プロセス情報表示
                print(f"Chromeプロセス一覧:")
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    if 'chrome' in proc.info['name'].lower():
                        print(f"  PID {proc.info['pid']}: {proc.info['name']}")
                
                # 起動したChromeを終了（テスト用）
                print(f"テスト用Chrome終了中...")
                for proc in psutil.process_iter(['pid', 'name']):
                    if 'chrome' in proc.info['name'].lower():
                        try:
                            p = psutil.Process(proc.info['pid'])
                            p.kill()
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
                
                time.sleep(2)
                print(f"✓ Chrome終了完了")
                
                break
            else:
                print(f"✗ {pattern['name']} 起動失敗（プロセス数変化なし）")
                
                # プロセスが起動していない場合の対処
                if process.poll() is not None:
                    print(f"  プロセス終了コード: {process.returncode}")
                else:
                    print(f"  プロセスは実行中だが検出できない")
                    process.terminate()
                
        except Exception as e:
            print(f"✗ {pattern['name']} エラー: {e}")
    
    return successful_pattern

def create_working_chrome_manager(working_pattern):
    """
    動作するChrome管理クラスを作成
    """
    if not working_pattern:
        print("動作するパターンが見つからないため、Chrome管理クラス作成をスキップ")
        return False
    
    print(f"\n=== 動作Chrome管理クラス作成 ===")
    print(f"採用パターン: {working_pattern['name']}")
    
    # ChromeManagerクラス作成
    chrome_manager_code = f'''# working_chrome_manager.py - 動作確認済みChrome管理
import subprocess
import time
import psutil
from pathlib import Path

class WorkingChromeManager:
    def __init__(self):
        self.chrome_exe = r"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
        self.active_accounts = set()
        
    def start_chrome(self, account_id, url="https://www.google.com"):
        """動作確認済みのChrome起動"""
        try:
            # プロファイルディレクトリ作成
            Path("chrome_profiles").mkdir(exist_ok=True)
            Path("chrome_profiles/acc1").mkdir(exist_ok=True)
            
            # 動作確認済みコマンド
            cmd = {repr(working_pattern['cmd'])[:-1] + ', url]'}
            
            print(f"Chrome起動: {{account_id}} -> {{url}}")
            
            # 起動前プロセス数
            initial_count = self._count_chrome_processes()
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # プロセス数増加確認
            time.sleep(3)
            current_count = self._count_chrome_processes()
            
            if current_count > initial_count:
                self.active_accounts.add(account_id)
                print(f"✓ Chrome起動成功: {{account_id}}")
                return True
            else:
                print(f"✗ Chrome起動失敗: {{account_id}}")
                return False
                
        except Exception as e:
            print(f"Chrome起動エラー: {{e}}")
            return False
    
    def _count_chrome_processes(self):
        """Chromeプロセス数をカウント"""
        count = 0
        for proc in psutil.process_iter(['name']):
            if 'chrome' in proc.info['name'].lower():
                count += 1
        return count
    
    def close_chrome(self, account_id):
        """Chrome終了"""
        if account_id in self.active_accounts:
            # 全Chromeプロセス終了（簡易版）
            for proc in psutil.process_iter(['pid', 'name']):
                if 'chrome' in proc.info['name'].lower():
                    try:
                        p = psutil.Process(proc.info['pid'])
                        p.kill()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
            
            self.active_accounts.discard(account_id)
            print(f"✓ Chrome終了: {{account_id}}")
    
    def is_active(self, account_id):
        """アクティブ状態確認"""
        return account_id in self.active_accounts
    
    def get_active_accounts(self):
        """アクティブアカウント一覧"""
        return list(self.active_accounts)

# テスト実行
if __name__ == "__main__":
    chrome = WorkingChromeManager()
    
    print("動作Chrome管理テスト...")
    success = chrome.start_chrome("test", "https://www.google.com")
    
    if success:
        print("✓ 動作Chrome管理成功")
        time.sleep(5)
        chrome.close_chrome("test")
        print("✓ Chrome終了完了")
    else:
        print("✗ 動作Chrome管理失敗")
'''
    
    # ファイル保存
    with open("working_chrome_manager.py", "w", encoding="utf-8") as f:
        f.write(chrome_manager_code)
    
    print("✓ working_chrome_manager.py 作成完了")
    return True

def test_vpn_chrome_integration():
    """
    VPN + 動作Chrome統合テスト
    """
    print(f"\n=== VPN + 動作Chrome統合テスト ===")
    
    try:
        import sys
        sys.path.append('.')
        from modules.config_manager import ConfigManager
        from modules.vpn_manager import VPNManager
        
        # VPN接続
        config = ConfigManager()
        vpn_manager = VPNManager(config)
        
        print(f"元のIP: {vpn_manager.original_ip}")
        
        print("VPN接続中...")
        vpn_success = vpn_manager.connect_account_vpn("acc1")
        
        if vpn_success:
            info = vpn_manager.get_connection_info()
            print(f"✓ VPN接続成功: {info['current_ip']}")
            
            # 動作Chrome起動
            print("動作Chrome起動...")
            
            # 動作Chromeマネージャーをインポート
            import importlib.util
            spec = importlib.util.spec_from_file_location("working_chrome_manager", "working_chrome_manager.py")
            working_chrome_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(working_chrome_module)
            
            chrome = working_chrome_module.WorkingChromeManager()
            chrome_success = chrome.start_chrome("acc1", "https://whatismyipaddress.com/")
            
            if chrome_success:
                print("🎉 VPN + Chrome統合完全成功！")
                print(f"ブラウザでVPN IPが表示されているか確認してください")
                print(f"期待されるIP: {info['current_ip']}")
                
                print("10秒間確認時間...")
                time.sleep(10)
                
                chrome.close_chrome("acc1")
                print("✓ Chrome終了")
                
                result = True
            else:
                print("✗ Chrome起動失敗")
                result = False
            
            # VPN切断
            vpn_manager.disconnect()
            print("✓ VPN切断完了")
            
            return result
        else:
            print("✗ VPN接続失敗")
            return False
            
    except Exception as e:
        print(f"✗ 統合テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("Chrome起動判定修正テストを開始します\n")
    
    # プロセス検出でChrome起動テスト
    working_pattern = test_chrome_with_process_detection()
    
    if working_pattern:
        # 動作Chrome管理作成
        created = create_working_chrome_manager(working_pattern)
        
        if created:
            # VPN統合テスト
            integration_result = test_vpn_chrome_integration()
            
            if integration_result:
                print(f"\n🎉 Chrome問題完全解決！")
                print(f"VPN + Chrome統合完全成功！")
                print(f"\n次のステップ:")
                print(f"1. GPT Fetcher開発")
                print(f"2. Tweet Poster開発")
                print(f"3. 24時間自動運用システム完成")
            else:
                print(f"\n⚠ 統合テストで問題発生")
        else:
            print(f"\n⚠ Chrome管理作成失敗")
    else:
        print(f"\n⚠ 動作するChromeパターンが見つかりません")
        print(f"手動確認: Chromeウィンドウが実際に開いていますか？")

if __name__ == "__main__":
    main()