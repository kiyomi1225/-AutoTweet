# modules/chrome_manager.py - Chrome管理（完全版）
import subprocess
import time
import psutil
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
import json
import shutil

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
        self.chrome_executable = None
        
        # Chrome実行ファイルを検索
        self._find_chrome_executable()
        
        # プロファイルディレクトリを準備
        self.user_data_dir = Path(self.chrome_config["user_data_dir"])
        self.user_data_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info("Chrome管理を初期化しました")
    
    def _find_chrome_executable(self):
        """Chrome実行ファイルを検索"""
        import platform
        
        system = platform.system()
        possible_paths = []
        
        if system == "Windows":
            possible_paths = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                r"C:\Users\{}\AppData\Local\Google\Chrome\Application\chrome.exe".format(
                    Path.home().name
                )
            ]
        elif system == "Darwin":  # macOS
            possible_paths = [
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
            ]
        else:  # Linux
            possible_paths = [
                "/usr/bin/google-chrome",
                "/usr/bin/chromium-browser",
                "/usr/bin/google-chrome-stable",
                "/snap/bin/chromium"
            ]
        
        # 存在確認
        for path in possible_paths:
            if Path(path).exists():
                self.chrome_executable = path
                self.logger.info(f"Chrome実行ファイル発見: {path}")
                return
        
        # コマンドラインで確認
        try:
            result = subprocess.run(
                ["where", "chrome"] if system == "Windows" else ["which", "google-chrome"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                self.chrome_executable = result.stdout.strip().split('\n')[0]
                self.logger.info(f"Chrome実行ファイル発見（PATH）: {self.chrome_executable}")
                return
        except Exception:
            pass
        
        # デフォルト
        self.chrome_executable = "chrome" if system == "Windows" else "google-chrome"
        self.logger.warning(f"Chrome実行ファイルが見つかりません。デフォルトを使用: {self.chrome_executable}")
    
    def start_chrome_profile(self, account_id: str, url: str = None) -> bool:
        """指定アカウントのChromeプロファイルを起動（プロセス判定修正版）"""
        try:
            self.logger.info(f"Chrome起動デバッグ開始: {account_id}")
            
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
            
            self.logger.info(f"アカウント設定取得完了: {account_config.get('chrome_profile', 'N/A')}")
            
            # 開始URLを決定
            if url is None:
                url = account_config.get("gpt_url", "https://chatgpt.com")
            
            self.logger.info(f"開始URL: {url}")
            
            # プロファイルディレクトリを準備
            profile_dir = self._prepare_profile_directory(account_id, account_config)
            self.logger.info(f"プロファイルディレクトリ: {profile_dir}")
            
            # Chrome実行ファイル確認
            if not self.chrome_executable or self.chrome_executable == "chrome":
                self.logger.warning("Chrome実行ファイルが見つかりません。再検索中...")
                self._find_chrome_executable()
            
            self.logger.info(f"Chrome実行ファイル: {self.chrome_executable}")
            
            # Chrome起動コマンド
            chrome_cmd = self._build_chrome_command(account_config, profile_dir, url)
            self.logger.info(f"Chrome起動コマンド: {chrome_cmd[:3]} ... (省略)")
            
            # Chromeプロセスを開始
            self.logger.info("Chromeプロセス開始中...")
            
            process = subprocess.Popen(
                chrome_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )
            
            self.logger.info(f"プロセス開始完了: PID {process.pid}")
            
            # Chrome起動確認方法を変更：実際のChromeウィンドウの存在を確認
            success = self._verify_chrome_startup(account_id, profile_dir)
            
            if success:
                # ダミープロセスとして記録（実際の子プロセスは別）
                self.active_profiles[account_id] = process
                self.logger.info(f"Chrome起動成功: {account_id}")
                return True
            else:
                self.logger.error(f"Chrome起動確認失敗: {account_id}")
                
                # プロセス情報をデバッグ出力
                poll_result = process.poll()
                if poll_result is not None:
                    stdout, stderr = process.communicate()
                    self.logger.info(f"親プロセス終了コード: {poll_result}")
                    self.logger.info(f"STDOUT: {stdout[:200] if stdout else '(空)'}")
                    self.logger.info(f"STDERR: {stderr[:200] if stderr else '(空)'}")
                
                return False
                
        except Exception as e:
            self.logger.error(f"Chrome起動例外エラー: {account_id} - {str(e)}")
            import traceback
            self.logger.error(f"スタックトレース: {traceback.format_exc()}")
            return False
    
    def _verify_chrome_startup(self, account_id: str, profile_dir: Path) -> bool:
        """Chrome起動を実際のウィンドウ・プロセス存在で確認"""
        try:
            max_attempts = 20  # 最大20秒待機
            
            for attempt in range(max_attempts):
                time.sleep(1)
                
                # 方法1: Chromeプロセスの存在確認
                chrome_processes = self._find_chrome_processes_by_profile(profile_dir)
                
                if chrome_processes:
                    self.logger.info(f"Chrome起動確認: {len(chrome_processes)}個のプロセス発見")
                    return True
                
                # 方法2: リモートデバッグポートの確認
                if self._check_remote_debug_port():
                    self.logger.info("Chrome起動確認: リモートデバッグポート応答")
                    return True
                
                self.logger.debug(f"Chrome起動確認中... ({attempt + 1}/{max_attempts})")
            
            self.logger.warning(f"Chrome起動確認タイムアウト: {max_attempts}秒")
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
                        
                        # プロファイルディレクトリ名で判定
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
            import requests
            
            # ソケット接続確認
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex(('127.0.0.1', 9222))
            sock.close()
            
            if result != 0:
                return False
            
            # HTTP API確認
            try:
                response = requests.get("http://127.0.0.1:9222/json", timeout=3)
                if response.status_code == 200:
                    data = response.json()
                    self.logger.debug(f"Chrome DevTools API: {len(data)}個のタブ")
                    return True
            except Exception:
                pass
            
            return True  # ソケット接続成功なら一応OK
            
        except Exception:
            return False
    
    def is_profile_active(self, account_id: str) -> bool:
        """指定プロファイルがアクティブかどうか確認（実プロセス基準）"""
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
                        # 自分のuser-data-dirのプロセスのみ終了
                        if str(self.user_data_dir) in cmdline:
                            proc.terminate()
                            killed_count += 1
                            self.logger.debug(f"既存Chromeプロセス終了: PID {proc.info['pid']}")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if killed_count > 0:
                self.logger.info(f"既存Chromeプロセス終了: {killed_count}件")
                time.sleep(2)  # 終了完了まで待機
                
        except Exception as e:
            self.logger.warning(f"既存Chromeプロセス終了エラー: {str(e)}")

    
    def _prepare_profile_directory(self, account_id: str, account_config: Dict[str, Any]) -> Path:
        """プロファイルディレクトリを準備"""
        profile_name = account_config.get("chrome_profile", account_id)
        profile_dir = self.user_data_dir / profile_name
        
        if not profile_dir.exists():
            profile_dir.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"新規プロファイルディレクトリ作成: {profile_dir}")
            self._create_default_profile_settings(profile_dir)
        
        return profile_dir
    
    def _create_default_profile_settings(self, profile_dir: Path):
        """デフォルトプロファイル設定を作成"""
        try:
            preferences = {
                "profile": {
                    "default_content_setting_values": {
                        "notifications": 2,
                        "geolocation": 2
                    },
                    "managed_user_id": "",
                    "name": f"Profile_{profile_dir.name}"
                },
                "browser": {
                    "show_home_button": True
                }
            }
            
            prefs_file = profile_dir / "Preferences"
            with open(prefs_file, 'w', encoding='utf-8') as f:
                json.dump(preferences, f, indent=2)
            
            self.logger.debug(f"デフォルト設定作成: {prefs_file}")
            
        except Exception as e:
            self.logger.warning(f"デフォルト設定作成エラー: {str(e)}")
    
    def _build_chrome_command(self, account_config: Dict[str, Any], profile_dir: Path, url: str) -> list:
        """Chrome起動コマンドを構築（独立モード）"""
        cmd = [
            self.chrome_executable,
            f"--user-data-dir={self.user_data_dir}",
            f"--profile-directory={profile_dir.name}",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-default-apps",
            "--remote-debugging-port=9222",  # Selenium接続用
            "--new-window",  # 新しいウィンドウで開く
            "--disable-session-crashed-bubble",  # セッション復旧ダイアログを無効
            "--disable-infobars",  # 情報バーを無効
            "--force-new-process"  # 新しいプロセスを強制
        ]
        
        # ヘッドレスモード
        if self.chrome_config.get("headless", False):
            cmd.extend(["--headless", "--disable-gpu"])
        
        # ウィンドウサイズ
        window_size = self.chrome_config.get("window_size", [1920, 1080])
        cmd.append(f"--window-size={window_size[0]},{window_size[1]}")
        
        # デバッグモード
        debug_config = self.config_manager.get_debug_config()
        if debug_config.get("enabled", False):
            cmd.extend([
                "--enable-logging",
                "--log-level=0"
            ])
        
        # 開始URL
        cmd.append(url)
        
        return cmd
    
    def _wait_for_chrome_startup(self, account_id: str) -> bool:
        """Chrome起動完了を待機"""
        timeout = self.chrome_config.get("startup_timeout", 30)
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.is_profile_active(account_id):
                time.sleep(2)
                if self.is_profile_active(account_id):
                    return True
            time.sleep(1)
        
        return False
    
    def close_chrome_profile(self, account_id: str):
        """指定アカウントのChromeプロファイルを終了"""
        try:
            if account_id not in self.active_profiles:
                self.logger.info(f"終了するChromeプロファイルが見つかりません: {account_id}")
                return
            
            process = self.active_profiles[account_id]
            
            self.logger.info(f"Chrome終了: {account_id}")
            
            try:
                process.terminate()
                process.wait(timeout=10)
                self.logger.debug(f"Chrome正常終了: {account_id}")
            except subprocess.TimeoutExpired:
                self.logger.warning(f"Chrome強制終了: {account_id}")
                process.kill()
                process.wait()
            
            del self.active_profiles[account_id]
            
        except Exception as e:
            self.logger.error(f"Chrome終了エラー: {account_id} - {str(e)}")
    
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
                            self.logger.debug(f"Chromeプロセス終了: PID {proc.info['pid']}")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if killed_count > 0:
                self.logger.info(f"残存Chromeプロセス終了: {killed_count}件")
                
        except Exception as e:
            self.logger.warning(f"Chromeプロセスクリーンアップエラー: {str(e)}")
    
    def is_profile_active(self, account_id: str) -> bool:
        """指定プロファイルがアクティブかどうか確認"""
        if account_id not in self.active_profiles:
            return False
        
        process = self.active_profiles[account_id]
        return process.poll() is None
    
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
    
    def restart_profile(self, account_id: str) -> bool:
        """指定プロファイルを再起動"""
        self.close_chrome_profile(account_id)
        time.sleep(2)
        return self.start_chrome_profile(account_id)
    
    def navigate_to_url(self, account_id: str, url: str) -> bool:
        """指定プロファイルで新しいURLを開く"""
        try:
            if not self.is_profile_active(account_id):
                self.logger.warning(f"非アクティブプロファイル: {account_id}")
                return False
            
            cmd = [
                self.chrome_executable,
                f"--user-data-dir={self.user_data_dir}",
                f"--profile-directory={self.active_profiles[account_id]}",
                "--new-tab",
                url
            ]
            
            subprocess.Popen(cmd, 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL)
            
            self.logger.info(f"URL移動: {account_id} -> {url}")
            return True
            
        except Exception as e:
            self.logger.error(f"URL移動エラー: {account_id} - {str(e)}")
            return False
    
    def get_profile_info(self, account_id: str) -> Dict[str, Any]:
        """プロファイル情報を取得"""
        info = {
            "account_id": account_id,
            "active": self.is_profile_active(account_id),
            "profile_dir": None,
            "process_id": None
        }
        
        account_config = self.config_manager.get_account_config(account_id)
        if account_config:
            profile_name = account_config.get("chrome_profile", account_id)
            info["profile_dir"] = str(self.user_data_dir / profile_name)
        
        if account_id in self.active_profiles:
            process = self.active_profiles[account_id]
            if process.poll() is None:
                info["process_id"] = process.pid
        
        return info
    
    def _debug_chrome_startup_failure(self, chrome_cmd: list, account_id: str):
        """Chrome起動失敗の詳細デバッグ"""
        try:
            self.logger.info("=== Chrome起動失敗デバッグ ===")
            
            chrome_exe = chrome_cmd[0]
            chrome_path = Path(chrome_exe)
            
            self.logger.info(f"Chrome実行ファイル確認:")
            self.logger.info(f"  パス: {chrome_exe}")
            self.logger.info(f"  存在: {chrome_path.exists()}")
            
            if chrome_path.exists():
                try:
                    stat_info = chrome_path.stat()
                    self.logger.info(f"  サイズ: {stat_info.st_size} bytes")
                    self.logger.info(f"  実行可能: {chrome_path.is_file()}")
                except Exception as e:
                    self.logger.info(f"  ファイル情報取得エラー: {e}")
            
            # プロファイルディレクトリ確認
            user_data_dir = None
            profile_dir = None
            
            for arg in chrome_cmd:
                if arg.startswith("--user-data-dir="):
                    user_data_dir = arg.split("=", 1)[1]
                elif arg.startswith("--profile-directory="):
                    profile_dir = arg.split("=", 1)[1]
            
            self.logger.info(f"ディレクトリ確認:")
            if user_data_dir:
                user_data_path = Path(user_data_dir)
                self.logger.info(f"  ユーザーデータディレクトリ: {user_data_dir}")
                self.logger.info(f"  存在: {user_data_path.exists()}")
                
                if profile_dir:
                    profile_path = user_data_path / profile_dir
                    self.logger.info(f"  プロファイルディレクトリ: {profile_path}")
                    self.logger.info(f"  存在: {profile_path.exists()}")
            
            # Chrome バージョンテスト
            self.logger.info("Chrome簡単テスト実行中...")
            try:
                test_cmd = [chrome_exe, "--version"]
                test_result = subprocess.run(
                    test_cmd, 
                    capture_output=True, 
                    text=True, 
                    timeout=10
                )
                
                self.logger.info(f"Chrome --version テスト:")
                self.logger.info(f"  終了コード: {test_result.returncode}")
                self.logger.info(f"  出力: {test_result.stdout.strip() if test_result.stdout else '(空)'}")
                self.logger.info(f"  エラー: {test_result.stderr.strip() if test_result.stderr else '(空)'}")
                
            except Exception as e:
                self.logger.error(f"Chrome簡単テスト失敗: {e}")
            
            self.logger.info("=== デバッグ終了 ===")
            
        except Exception as e:
            self.logger.error(f"デバッグ処理エラー: {e}")
    
    def _check_admin_rights(self) -> bool:
        """管理者権限の確認"""
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False


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