# modules/vpn_manager.py - VPN管理（クリーン版）
import subprocess
import time
import psutil
import requests
from pathlib import Path
from typing import Optional, Dict, Any

try:
    from .logger_setup import setup_module_logger
except ImportError:
    # 直接実行時の対応
    import sys
    sys.path.append('.')
    from modules.logger_setup import setup_module_logger

class VPNManager:
    def __init__(self, config_manager):
        """VPN管理クラス"""
        self.config_manager = config_manager
        self.vpn_config = config_manager.get_vpn_config()
        self.logger = setup_module_logger("VPNManager")
        
        self.current_connection = None
        self.process = None
        self.original_ip = None
        
        # 初期IP記録
        self._record_original_ip()
        
        self.logger.info("VPN管理を初期化しました")
    
    def _record_original_ip(self):
        """VPN接続前の元のIPアドレスを記録"""
        try:
            current_ip = self._get_current_ip()
            if current_ip:
                self.original_ip = current_ip
                self.logger.info(f"元のIPアドレス記録: {current_ip}")
            else:
                self.logger.warning("元のIPアドレスの取得に失敗")
                self.original_ip = None
        except Exception as e:
            self.logger.warning(f"元のIP記録エラー: {str(e)}")
            self.original_ip = None
    
    def _get_current_ip(self) -> Optional[str]:
        """現在のIPアドレスを取得"""
        try:
            ip_services = [
                "https://api.ipify.org",
                "https://ipinfo.io/ip",
                "https://icanhazip.com"
            ]
            
            for service in ip_services:
                try:
                    response = requests.get(service, timeout=10)
                    if response.status_code == 200:
                        ip = response.text.strip()
                        if self._is_valid_ip(ip):
                            return ip
                except Exception:
                    continue
            
            return None
            
        except Exception as e:
            self.logger.error(f"IP取得エラー: {str(e)}")
            return None
    
    def _is_valid_ip(self, ip: str) -> bool:
        """IPアドレス形式の検証"""
        import ipaddress
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
    
    def connect_account_vpn(self, account_id: str) -> bool:
        """指定アカウントのVPNに接続"""
        try:
            # 既存接続を切断
            if self.current_connection:
                self.disconnect()
            
            # アカウント設定を取得
            account_config = self.config_manager.get_account_config(account_id)
            if not account_config:
                self.logger.error(f"アカウント設定が見つかりません: {account_id}")
                return False
            
            # VPNファイルパスを構築
            account_dir = Path(f"C:/Users/shiki/AutoTweet/data/{account_id}")

             # 変数を先に初期化
            ovpn_file = None

            # *.nordvpn.com.udp.ovpnファイルを検索
            ovpn_files = list(account_dir.glob("*.nordvpn.com.udp.ovpn"))

            if not ovpn_files:
                # TCP版も検索
                ovpn_files = list(account_dir.glob("*.nordvpn.com.tcp.ovpn"))
            
            if not ovpn_files:
                # その他の.ovpnファイルも検索
                ovpn_files = list(account_dir.glob("*.ovpn"))
            
            if ovpn_files:
                ovpn_file = ovpn_files[0]  # 最初のファイルを使用
                self.logger.info(f"VPNファイル使用: {ovpn_file.name}")
            else:
                self.logger.error(f"VPNファイルが見つかりません: {account_dir}")
                return False
            
            # 認証ファイルを確認
            auth_file = Path(self.vpn_config["auth_file"])
            if not auth_file.exists():
                self.logger.error(f"認証ファイルが見つかりません: {auth_file}")
                return False
            
            # OpenVPN接続の試行
            retry_count = self.vpn_config.get("retry_count", 3)
            for attempt in range(retry_count):
                if self._attempt_vpn_connection(ovpn_file, auth_file, account_id):
                    self.current_connection = account_id
                    current_ip = self._get_current_ip()
                    return True
                
                if attempt < retry_count - 1:
                    time.sleep(5)
            
            self.logger.error(f"VPN接続失敗: {account_id}")
            return False
                
        except Exception as e:
            self.logger.error(f"VPN接続エラー: {account_id} - {str(e)}")
            return False
    
    def smart_vpn_connect(self, account_id: str) -> bool:
        """スマートVPN接続"""
        try:
            current_ip = self._get_current_ip()
            
            if not current_ip:
                self.logger.error("現在のIP取得に失敗")
                return False
            
            # 元のIPが不明な場合は接続を実行
            if self.original_ip is None:
                return self.connect_account_vpn(account_id)
            
            # 現在のIPが元のIPと同じ場合はVPN接続
            if current_ip == self.original_ip:
                return self.connect_account_vpn(account_id)
            else:
                self.logger.info(f"VPN接続済みと判定: {current_ip}")
                return True
                
        except Exception as e:
            self.logger.error(f"スマートVPN接続エラー: {str(e)}")
            return False
    
    def _attempt_vpn_connection(self, ovpn_file: Path, auth_file: Path, account_id: str) -> bool:
        """VPN接続を試行"""
        try:
            # OpenVPN接続コマンド
            cmd = self._build_openvpn_command(ovpn_file, auth_file)
            
            # OpenVPNプロセスを開始
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )
            time.sleep(15)
            # 接続確認
            return self._wait_for_connection()
                
        except Exception as e:
            self.logger.error(f"VPN接続試行エラー: {str(e)}")
            return False
    
    def _build_openvpn_command(self, ovpn_file: Path, auth_file: Path) -> list:
        """OpenVPNコマンドを構築"""
        openvpn_exe = self._find_openvpn_executable()
        
        cmd = [
            openvpn_exe,
            "--config", str(ovpn_file),
            "--auth-user-pass", str(auth_file),
            "--verb", "3",
            "--log", "logs/openvpn.log",
            "--suppress-timestamps"
        ]
        
        return cmd
    
    def _find_openvpn_executable(self) -> str:
        """OpenVPN実行ファイルを検索"""
        possible_paths = [
            r"C:\Program Files\OpenVPN\bin\openvpn.exe",
            r"C:\Program Files (x86)\OpenVPN\bin\openvpn.exe",
            "openvpn.exe",
            "openvpn"
        ]
        
        for path in possible_paths:
            try:
                if Path(path).exists():
                    return path
            except Exception:
                continue
        
        return "openvpn"
    
    def _wait_for_connection(self) -> bool:
        """VPN接続完了を待機"""
        timeout = self.vpn_config.get("connection_timeout", 30)
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self._verify_ip_change():
                return True
            
            time.sleep(2)
            
            # プロセス状態確認
            if self.process and self.process.poll() is not None:
                break
        
        return False
    
    def _verify_ip_change(self) -> bool:
        """IPアドレスの変化を確認"""
        try:
            current_ip = self._get_current_ip()
            if current_ip and self.original_ip:
                if current_ip != self.original_ip:
                    return True
            
            # 元のIPが不明な場合は接続成功とみなす
            return current_ip is not None
            
        except Exception:
            return False
    
    def disconnect(self):
        """VPN接続を切断"""
        try:
            if self.current_connection:
                self.logger.info(f"VPN切断開始: {self.current_connection}")
            
            # OpenVPNプロセスを終了
            self._kill_openvpn_processes()
            
            self.current_connection = None
            self.process = None
            
            # 切断確認のため待機
            time.sleep(3)
                                    
        except Exception as e:
            self.logger.error(f"VPN切断エラー: {str(e)}")
    
    def _kill_openvpn_processes(self):
        """OpenVPNプロセスを強制終了"""
        try:
            killed_count = 0
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if 'openvpn' in proc.info['name'].lower():
                        proc.kill()
                        killed_count += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
            if killed_count > 0:
                self.logger.info(f"OpenVPNプロセス終了: {killed_count}件")
                
        except Exception as e:
            self.logger.warning(f"OpenVPNプロセス終了エラー: {str(e)}")
    
    def is_connected(self) -> bool:
        """VPN接続状態を確認"""
        return self.current_connection is not None
    
    def get_connection_info(self) -> Dict[str, Any]:
        """接続情報を取得"""
        info = {
            "connected": self.is_connected(),
            "account_id": self.current_connection,
            "current_ip": self._get_current_ip(),
            "original_ip": self.original_ip
        }
        
        return info


# テスト関数
def test_vpn_manager():
    """VPNManagerのテスト"""
    print("=== VPNManager テスト開始 ===")
    
    try:
        from modules.config_manager import ConfigManager
        
        config = ConfigManager()
        vpn_manager = VPNManager(config)
        print("✓ VPNManager初期化成功")
        
        # 接続情報取得テスト
        info = vpn_manager.get_connection_info()
        print(f"✓ 接続情報取得: 接続状態={info['connected']}")
        print(f"  現在IP: {info['current_ip']}")
        print(f"  元IP: {info['original_ip']}")
        
        # 認証ファイル確認
        auth_file = Path(vpn_manager.vpn_config["auth_file"])
        if auth_file.exists():
            print("✓ 認証ファイル存在確認")
        else:
            print("⚠ 認証ファイル未設定（実際のVPN接続には必要）")
        
        # VPNファイル確認
        ovpn_dir = Path(vpn_manager.vpn_config["ovpn_dir"])
        ovpn_files = list(ovpn_dir.glob("*.ovpn")) if ovpn_dir.exists() else []
        print(f"✓ VPNファイル確認: {len(ovpn_files)}件")
        
        print("=== VPNManager テスト完了 ===")
        return True
        
    except Exception as e:
        print(f"✗ テストエラー: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_vpn_manager()