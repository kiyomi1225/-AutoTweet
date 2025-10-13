# final_chrome_manager.py - 最終版Chrome管理
import subprocess
import time
import psutil

class FinalChromeManager:
    def __init__(self):
        self.chrome_exe = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        self.user_data_dir = r"C:\Users\shiki\AppData\Local\Google\Chrome\User Data"
        self.active_accounts = set()
        
    def start_chrome(self, account_id, url="https://www.google.com"):
        try:
            cmd = [
                self.chrome_exe,
                f"--user-data-dir={self.user_data_dir}",
                f"--profile-directory={account_id}",
                url
            ]
            
            print(f"Chrome起動: {account_id} -> {url}")
            
            initial_count = self._count_chrome_processes()
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
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
    
    def close_chrome(self, account_id):
        if account_id in self.active_accounts:
            try:
                print(f"Chrome終了開始: {account_id}")
                
                # taskkillで終了
                subprocess.run(["taskkill", "/f", "/im", "chrome.exe"], 
                             capture_output=True, timeout=5)
                
                time.sleep(2)
                
                remaining = self._count_chrome_processes()
                if remaining == 0:
                    print(f"✓ Chrome完全終了: {account_id}")
                else:
                    print(f"⚠ Chrome一部残存: {remaining}プロセス")
                
                self.active_accounts.discard(account_id)
                
            except Exception as e:
                print(f"Chrome終了エラー: {e}")
                self.active_accounts.discard(account_id)
    
    def _count_chrome_processes(self):
        count = 0
        for proc in psutil.process_iter(['name']):
            if 'chrome' in proc.info['name'].lower():
                count += 1
        return count
    
    def is_active(self, account_id):
        return account_id in self.active_accounts
    
    def get_active_accounts(self):
        return list(self.active_accounts)

if __name__ == "__main__":
    chrome = FinalChromeManager()
    
    print("最終版Chrome管理テスト...")
    success = chrome.start_chrome("acc1", "https://chatgpt.com")
    
    if success:
        print("✓ 最終版Chrome起動成功")
        print("5秒間動作確認...")
        time.sleep(5)
        chrome.close_chrome("acc1")
        print("✓ Chrome終了完了")
    else:
        print("✗ 最終版Chrome起動失敗")
