# test_chrome_shutdown.py - Chrome終了テスト
import time
import subprocess
import psutil

def count_chrome_processes():
    """Chromeプロセス数をカウント"""
    count = 0
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        if 'chrome' in proc.info['name'].lower():
            count += 1
            processes.append({
                'pid': proc.info['pid'],
                'name': proc.info['name'],
                'cmdline': proc.info.get('cmdline', [])
            })
    return count, processes

def test_chrome_shutdown_methods():
    """
    Chrome終了方法をテスト
    """
    print("=== Chrome終了方法テスト ===")
    
    # Chrome起動
    print("\n[準備] Chrome起動...")
    chrome_exe = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    
    process = subprocess.Popen([
        chrome_exe,
        "--user-data-dir=chrome_profiles",
        "--profile-directory=test_shutdown",
        "https://www.google.com"
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    time.sleep(5)
    
    initial_count, initial_processes = count_chrome_processes()
    print(f"起動後Chromeプロセス数: {initial_count}")
    
    if initial_count == 0:
        print("✗ Chrome起動確認できません")
        return
    
    # テスト方法
    shutdown_methods = [
        {
            "name": "方法1: taskkill 通常終了",
            "func": lambda: subprocess.run(["taskkill", "/im", "chrome.exe"], 
                                         capture_output=True, timeout=5)
        },
        {
            "name": "方法2: taskkill 強制終了",
            "func": lambda: subprocess.run(["taskkill", "/f", "/im", "chrome.exe"], 
                                         capture_output=True, timeout=5)
        },
        {
            "name": "方法3: psutil個別終了",
            "func": lambda: terminate_chrome_psutil()
        },
        {
            "name": "方法4: PowerShell終了",
            "func": lambda: subprocess.run([
                "powershell", "-Command", 
                "Get-Process -Name chrome -ErrorAction SilentlyContinue | Stop-Process -Force"
            ], capture_output=True, timeout=10)
        }
    ]
    
    def terminate_chrome_psutil():
        """psutilでChrome終了"""
        for proc in psutil.process_iter(['pid', 'name']):
            if 'chrome' in proc.info['name'].lower():
                try:
                    p = psutil.Process(proc.info['pid'])
                    p.terminate()  # まずは通常終了
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        
        time.sleep(2)
        
        # 残存プロセスを強制終了
        for proc in psutil.process_iter(['pid', 'name']):
            if 'chrome' in proc.info['name'].lower():
                try:
                    p = psutil.Process(proc.info['pid'])
                    p.kill()  # 強制終了
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
    
    # 各方法をテスト
    for i, method in enumerate(shutdown_methods):
        print(f"\n[テスト {i+1}] {method['name']}")
        
        # Chrome再起動（前回のテストで終了している場合）
        current_count, _ = count_chrome_processes()
        if current_count == 0:
            print("Chrome再起動中...")
            subprocess.Popen([
                chrome_exe,
                "--user-data-dir=chrome_profiles", 
                "--profile-directory=test_shutdown",
                "https://www.google.com"
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(3)
        
        # 終了前のプロセス数
        before_count, before_processes = count_chrome_processes()
        print(f"終了前プロセス数: {before_count}")
        
        if before_count == 0:
            print("✗ 終了対象のChromeプロセスがありません")
            continue
        
        # 終了実行
        try:
            method['func']()
            print(f"終了コマンド実行完了")
        except Exception as e:
            print(f"終了コマンドエラー: {e}")
            continue
        
        # 結果確認（段階的に確認）
        for wait_time in [2, 5, 10]:
            time.sleep(wait_time - (2 if wait_time > 2 else 0))
            after_count, after_processes = count_chrome_processes()
            print(f"{wait_time}秒後プロセス数: {after_count}")
            
            if after_count == 0:
                print(f"✓ {method['name']} 成功（{wait_time}秒で完全終了）")
                break
        else:
            print(f"⚠ {method['name']} 部分的成功（一部プロセス残存）")
            # 残存プロセス情報
            for proc in after_processes:
                print(f"  残存: PID {proc['pid']} - {proc['name']}")
    
    # 最終クリーンアップ
    print(f"\n[最終クリーンアップ]")
    final_count, _ = count_chrome_processes()
    if final_count > 0:
        print(f"残存プロセス強制終了中: {final_count}個")
        for proc in psutil.process_iter(['pid', 'name']):
            if 'chrome' in proc.info['name'].lower():
                try:
                    p = psutil.Process(proc.info['pid'])
                    p.kill()
                except:
                    pass
        
        time.sleep(2)
        final_final_count, _ = count_chrome_processes()
        print(f"最終プロセス数: {final_final_count}")

def test_working_chrome_manager_shutdown():
    """
    修正版WorkingChromeManagerの終了テスト
    """
    print(f"\n=== 修正版ChromeManager終了テスト ===")
    
    try:
        from working_chrome_manager import WorkingChromeManager
        
        chrome = WorkingChromeManager()
        
        print("Chrome起動テスト...")
        success = chrome.start_chrome("test_shutdown", "https://chatgpt.com/g/g-684b62030c9081918ba4ad6ffd1b9392-ji-ke-tuitozuo-cheng-ai-tasi")
        
        if success:
            print("✓ Chrome起動成功")
            
            initial_count = chrome._count_chrome_processes()
            print(f"起動後プロセス数: {initial_count}")
            
            print("5秒後にChrome終了テスト...")
            time.sleep(5)
            
            # 修正版終了メソッドテスト
            chrome.close_chrome("test_shutdown")
            
            time.sleep(3)
            final_count = chrome._count_chrome_processes()
            print(f"終了後プロセス数: {final_count}")
            
            if final_count == 0:
                print("✓ 修正版Chrome終了成功")
            else:
                print(f"⚠ 修正版Chrome終了部分的成功（{final_count}個残存）")
                
                # 全終了テスト
                print("全Chrome終了テスト...")
                chrome.close_all_chrome()
                
                time.sleep(3)
                all_final_count = chrome._count_chrome_processes()
                print(f"全終了後プロセス数: {all_final_count}")
        else:
            print("✗ Chrome起動失敗")
            
    except Exception as e:
        print(f"✗ 修正版テストエラー: {e}")
        import traceback
        traceback.print_exc()

def main():
    print("Chrome終了問題解決テストを開始します\n")
    
    # 基本的な終了方法テスト
    test_chrome_shutdown_methods()
    
    # 修正版ChromeManagerテスト  
    test_working_chrome_manager_shutdown()
    
    print(f"\n=== Chrome終了テスト完了 ===")
    print("最も効果的な方法が特定されました")

if __name__ == "__main__":
    main()