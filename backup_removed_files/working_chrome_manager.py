# working_chrome_manager.py - 動作確認済みChrome管理
import subprocess
import time
import psutil
from pathlib import Path

class WorkingChromeManager:
    def __init__(self):
        self.chrome_exe = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        self.active_accounts = set()
        
    def start_chrome(self, account_id, url="https://www.google.com"):
        """動作確認済みのChrome起動"""
        try:
            # プロファイルディレクトリ作成
            Path("chrome_profiles").mkdir(exist_ok=True)
            Path("chrome_profiles/acc1").mkdir(exist_ok=True)
            
            # 動作確認済みコマンド
            cmd = ['C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe', '--user-data-dir=C:\\Users\\shiki\\AutoTweet\\chrome_profiles', '--profile-directory=acc1', 'https://www.google.com', url]
            
            print(f"Chrome起動: {account_id} -> {url}")
            
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
                print(f"✓ Chrome起動成功: {account_id}")
                return True
            else:
                print(f"✗ Chrome起動失敗: {account_id}")
                return False
                
        except Exception as e:
            print(f"Chrome起動エラー: {e}")
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
            print(f"✓ Chrome終了: {account_id}")
    
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
