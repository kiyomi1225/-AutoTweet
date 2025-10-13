# modules/chrome_manager.py - Chrome管理（クリーン版）
import subprocess
import time
import psutil
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

try:
    from .logger_setup import setup_module_logger
except ImportError:
    # 直接実行時の対応
    import sys
    sys.path.append('.')
    from modules.logger_setup import setup_module_logger

class ChromeManager:
    def __init__(self, config_manager):
        """
        Chrome管理クラス
        
        Args:
            config_manager: 設定管理インスタンス
        """
        self.config_manager = config_manager
        self.chrome_config = config_manager.get_chrome_config()
        self.logger = setup_module_logger("ChromeManager")
        
        self.active_profiles = {}  # {account_id: process}
        
        # Chrome実行ファイルパス（設定から取得）
        self.chrome_executable = self.chrome_config.get(
            "executable_path", 
            r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        )
        
        # プロファイルディレクトリを準備
        self.user_data_dir = Path(self.chrome_config["user_data_dir"])
        self.user_data_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info("Chrome管理を初期化しました")
    
    def start_chrome_profile(self, account_id: str, url: str = None) -> bool:
        """指定アカウントのChromeプロファイルを起動"""
        try:
            
            # 既存のChromeプロセスを確認・終了
            self._close_existing_chrome_processes()
            
            # 既存プロファイルを確認
            if account_id in self.active_profiles:
                if self.is_profile_active(account_id):
                    self.logger.info(f"既存のChromeプロファイルを使用: {account_id}")
                    return True
                else:
                    del self.active_profiles[account_id]
            
            # アカウント設定を取得
            account_config = self.config_manager.get_account_config(account_id)
            if not account_config:
                self.logger.error(f"アカウント設定が見つかりません: {account_id}")
                return False
            
            # 開始URLを決定
            if url is None:
                url = account_config.get("gpt_url", "https://chatgpt.com")
            
            # プロファイルディレクトリを準備
            profile_dir = self._prepare_profile_directory(account_id, account_config)
            
            # Chrome起動コマンド
            chrome_cmd = self._build_chrome_command(profile_dir, url)
            
            # Chromeプロセスを開始
            process = subprocess.Popen(
                chrome_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )
            
            # Chrome起動確認
            success = self._verify_chrome_startup(profile_dir)
            
            if success:
                self.active_profiles[account_id] = process
                self.logger.info(f"Chrome起動成功: {account_id}")
                return True
            else:
                self.logger.error(f"Chrome起動確認失敗: {account_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Chrome起動エラー: {account_id} - {str(e)}")
            return False
    
    def _verify_chrome_startup(self, profile_dir: Path) -> bool:
        """Chrome起動を確認"""
        try:
            max_attempts = 20  # 最大20秒待機
            
            for attempt in range(max_attempts):
                time.sleep(1)
                
                # Chromeプロセスの存在確認
                chrome_processes = self._find_chrome_processes_by_profile(profile_dir)
                if chrome_processes:

                    return True
                
                # リモートデバッグポートの確認
                if self._check_remote_debug_port():
                    self.logger.info("Chrome起動確認: リモートデバッグポート応答")
                    return True
            
            self.logger.warning("Chrome起動確認タイムアウト")
            return False
            
        except Exception as e:
            self.logger.error(f"Chrome起動確認エラー: {str(e)}")
            return False
    
    def _find_chrome_processes_by_profile(self, profile_dir: Path) -> List[psutil.Process]:
        """指定プロファイルのChromeプロセスを検索"""
        try:
            chrome_processes = []
            profile_name = profile_dir.name
            
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if 'chrome' in proc.info['name'].lower():
                        cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                        if f"--profile-directory={profile_name}" in cmdline:
                            chrome_processes.append(proc)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return chrome_processes
            
        except Exception as e:
            self.logger.debug(f"Chromeプロセス検索エラー: {str(e)}")
            return []
    
    def _check_remote_debug_port(self) -> bool:
        """リモートデバッグポート9222の応答確認"""
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex(('127.0.0.1', 9222))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    def is_profile_active(self, account_id: str) -> bool:
        """指定プロファイルがアクティブかどうか確認"""
        if account_id not in self.active_profiles:
            return False
        
        try:
            # 実際のChromeプロセスの存在確認
            account_config = self.config_manager.get_account_config(account_id)
            if account_config:
                profile_name = account_config.get("chrome_profile", account_id)
                profile_dir = self.user_data_dir / profile_name
                chrome_processes = self._find_chrome_processes_by_profile(profile_dir)
                return len(chrome_processes) > 0
            return False
        except Exception as e:
            self.logger.debug(f"プロファイルアクティブ確認エラー: {str(e)}")
            return False
    
    def _close_existing_chrome_processes(self):
        """既存のChromeプロセスを終了"""
        try:
            killed_count = 0
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if 'chrome' in proc.info['name'].lower():
                        cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                        if str(self.user_data_dir) in cmdline:
                            proc.terminate()
                            killed_count += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if killed_count > 0:
                self.logger.info(f"既存Chromeプロセス終了: {killed_count}件")
                time.sleep(2)
        except Exception as e:
            self.logger.warning(f"既存Chromeプロセス終了エラー: {str(e)}")
    
    def _prepare_profile_directory(self, account_id: str, account_config: Dict[str, Any]) -> Path:
        """プロファイルディレクトリを準備"""
        profile_name = account_config.get("chrome_profile", account_id)
        profile_dir = self.user_data_dir / profile_name
        profile_dir.mkdir(parents=True, exist_ok=True)
        return profile_dir
    
    def _build_chrome_command(self, profile_dir: Path, url: str) -> list:
        """Chrome起動コマンドを構築"""
        cmd = [
            self.chrome_executable,
            f"--user-data-dir={self.user_data_dir}",
            f"--profile-directory={profile_dir.name}",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-default-apps",
            "--remote-debugging-port=9222",
            "--new-window",
            "--disable-session-crashed-bubble",
            "--disable-infobars",
            "--force-new-process"
        ]
        
        # ヘッドレスモード
        if self.chrome_config.get("headless", False):
            cmd.extend(["--headless", "--disable-gpu"])
        
        # ウィンドウサイズ
        window_size = self.chrome_config.get("window_size", [1920, 1080])
        cmd.append(f"--window-size={window_size[0]},{window_size[1]}")
        
        # 開始URL
        cmd.append(url)
        
        return cmd
    
    def close_chrome_profile(self, account_id: str):
        """指定アカウントのChromeプロファイルを終了（画像認識版）"""
        try:
            # 画像認識でChrome閉じるボタンをクリック
            if self._close_chrome_with_image():
                self.logger.info(f"Chrome画像認識終了成功: {account_id}")
            else:
                self.logger.warning("画像認識終了失敗、プロセス終了でフォールバック")
                # フォールバック: プロセス終了
                if account_id in self.active_profiles:
                    process = self.active_profiles[account_id]
                    try:
                        process.terminate()
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
            
            # アクティブプロファイルから削除
            if account_id in self.active_profiles:
                del self.active_profiles[account_id]
            
        except Exception as e:
            self.logger.error(f"Chrome終了エラー: {account_id} - {str(e)}")
    
    def _close_chrome_with_image(self) -> bool:
        """画像認識でChromeの閉じるボタンをクリック（画面右側20%のみ検索）"""
        try:
            import pyautogui
            
            close_image = Path("images/close_button.png")
            if not close_image.exists():
                self.logger.warning("close_button.png が見つかりません")
                return False
            
            # 画面サイズ取得
            screen_width, screen_height = pyautogui.size()
            
            # 画面右側20%の領域を定義
            search_region = (
                int(screen_width * 0.8),  # 左端: 画面の80%位置から
                0,                         # 上端: 画面上部から
                int(screen_width * 0.2),   # 幅: 画面の20%
                screen_height              # 高さ: 画面全体
            )
            
            # 閉じるボタン認識・クリック
            for attempt in range(3):
                try:
                    locations = list(pyautogui.locateAllOnScreen(
                        str(close_image), 
                        confidence=0.8,
                        region=search_region  # 検索領域を指定
                    ))
                    
                    if locations:
                        center = pyautogui.center(locations[0])
                        pyautogui.click(center.x, center.y)
                        self.logger.info(f"Chrome閉じるボタンクリック: ({center.x}, {center.y})")
                        time.sleep(3)  # Chrome終了待機
                        return True
                        
                except pyautogui.ImageNotFoundException:
                    pass
                
                if attempt < 2:
                    time.sleep(2)
            
            return False
            
        except Exception as e:
            self.logger.error(f"Chrome画像認識終了エラー: {str(e)}")
            return False
        
    def close_all_profiles(self):
        """全てのChromeプロファイルを終了"""
        account_ids = list(self.active_profiles.keys())
        for account_id in account_ids:
            self.close_chrome_profile(account_id)
        self._cleanup_chrome_processes()
    
    def _cleanup_chrome_processes(self):
        """残存するChromeプロセスをクリーンアップ"""
        try:
            killed_count = 0
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if 'chrome' in proc.info['name'].lower():
                        cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                        if str(self.user_data_dir) in cmdline:
                            proc.kill()
                            killed_count += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if killed_count > 0:
                self.logger.info(f"残存Chromeプロセス終了: {killed_count}件")
        except Exception as e:
            self.logger.warning(f"Chromeプロセスクリーンアップエラー: {str(e)}")
    
    def get_active_profiles(self) -> List[str]:
        """アクティブなプロファイルリストを取得"""
        active_list = []
        to_remove = []
        
        for account_id, process in self.active_profiles.items():
            if process.poll() is None:
                active_list.append(account_id)
            else:
                to_remove.append(account_id)
        
        for account_id in to_remove:
            del self.active_profiles[account_id]
        
        return active_list


# テスト関数
def test_chrome_manager():
    """ChromeManagerのテスト"""
    print("=== ChromeManager テスト開始 ===")
    
    try:
        from modules.config_manager import ConfigManager
        
        config = ConfigManager()
        chrome_manager = ChromeManager(config)
        print("✓ ChromeManager初期化成功")
        
        print(f"✓ Chrome実行ファイル: {chrome_manager.chrome_executable}")
        print(f"✓ プロファイルディレクトリ: {chrome_manager.user_data_dir}")
        
        # アカウント確認
        accounts = config.get_all_accounts()
        if not accounts:
            print("❌ 利用可能なアカウントがありません")
            return
        
        test_account = accounts[0]
        print(f"✓ テストアカウント: {test_account}")
        
        # Chrome起動テスト
        confirm = input("Chrome起動テストを実行しますか？ (y/n): ")
        if confirm.lower() == 'y':
            print(f"Chrome起動テスト実行中...")
            success = chrome_manager.start_chrome_profile(test_account, "https://www.google.com")
            
            if success:
                print("✅ Chrome起動成功")
                active_profiles = chrome_manager.get_active_profiles()
                print(f"✓ アクティブプロファイル: {active_profiles}")
                
                print("\n5秒後にChromeを終了します...")
                time.sleep(5)
                
                # 画像認識でChrome終了を試行
                if chrome_manager._close_chrome_with_image():
                    print("✅ Chrome画像認識終了成功")
                else:
                    print("⚠️ 画像認識終了失敗、強制終了実行")
                    chrome_manager.close_chrome_profile(test_account)
                print("✅ Chrome終了")
            else:
                print("❌ Chrome起動失敗")
        
        print("\n=== ChromeManager テスト完了 ===")
        return True
        
    except Exception as e:
        print(f"✗ テストエラー: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_chrome_manager()