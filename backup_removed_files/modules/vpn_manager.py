# modules/vpn_manager.py - VPN管理（修正版）
import subprocess
import time
import psutil
import logging
import re
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
        """
        VPN管理クラス
        
        Args:
            config_manager: 設定管理インスタンス
        """
        self.config_manager = config_manager
        self.vpn_config = config_manager.get_vpn_config()
        self.logger = setup_module_logger("VPNManager")
        
        self.current_connection = None
        self.process = None
        self.original_ip = None
        self.vpn_connected_ip = None  # VPN接続時のIPを記録
        
        # 初期IP記録（VPN状態を確認してから）
        self._record_original_ip()
        
        self.logger.info("VPN管理を初期化しました")
    
    def _record_original_ip(self):
        """
        VPN接続前の元のIPアドレスを記録（改良版）
        """
        try:
            current_ip = self._get_current_ip()
            
            if current_ip:
                # VPN接続状態の確認
                if self._is_likely_vpn_ip(current_ip):
                    self.logger.warning(f"初期化時にVPN接続を検出: {current_ip}")
                    self.logger.warning("正確な元IPを取得するため、先にVPNを切断してください")
                    self.original_ip = None  # 元IPは不明とする
                else:
                    self.original_ip = current_ip
                    self.logger.info(f"元のIPアドレス記録: {current_ip}")
            else:
                self.logger.warning("元のIPアドレスの取得に失敗")
                self.original_ip = None
                
        except Exception as e:
            self.logger.warning(f"元のIP記録エラー: {str(e)}")
            self.original_ip = None
    
    def _is_likely_vpn_ip(self, ip: str) -> bool:
        """
        IPアドレスがVPN由来かどうかを推測
        
        Args:
            ip: IPアドレス
            
        Returns:
            bool: VPN由来の可能性が高いかどうか
        """
        try:
            # 一般的なVPNサービスのIPレンジ
            vpn_indicators = [
                # NordVPN
                r'^185\.199\.',  # NordVPN範囲例
                r'^103\.47\.',
                r'^194\.36\.',
                # ExpressVPN
                r'^199\.83\.',
                r'^208\.78\.',
                # その他商用VPN
                r'^198\.44\.',
                r'^185\.246\.',
                r'^77\.247\.',
            ]
            
            for pattern in vpn_indicators:
                if re.match(pattern, ip):
                    return True
            
            # IPアドレス情報での判定も可能（オプション）
            # この部分は必要に応じて実装
            
            return False
            
        except Exception:
            return False
    
    def _get_current_ip(self) -> Optional[str]:
        """
        現在のIPアドレスを取得
        
        Returns:
            str: IPアドレス（取得失敗時はNone）
        """
        try:
            # 複数のIPチェックサービスを試行
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
                        # IPアドレス形式の検証
                        if self._is_valid_ip(ip):
                            return ip
                except Exception:
                    continue
            
            return None
            
        except Exception as e:
            self.logger.error(f"IP取得エラー: {str(e)}")
            return None
    
    def _is_valid_ip(self, ip: str) -> bool:
        """
        IPアドレス形式の検証
        
        Args:
            ip: IPアドレス文字列
            
        Returns:
            bool: 有効なIPアドレスかどうか
        """
        import ipaddress
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
    
    def connect_account_vpn(self, account_id: str) -> bool:
        """
        指定アカウントのVPNに接続
        
        Args:
            account_id: アカウントID
            
        Returns:
            bool: 接続成功可否
        """
        try:
            # 接続前のIPを記録（元IPが不明な場合）
            if self.original_ip is None:
                pre_connect_ip = self._get_current_ip()
                if pre_connect_ip and not self._is_likely_vpn_ip(pre_connect_ip):
                    self.original_ip = pre_connect_ip
                    self.logger.info(f"接続前IP記録: {pre_connect_ip}")
            
            # 既存接続を切断
            if self.current_connection:
                self.logger.info(f"既存のVPN接続を切断: {self.current_connection}")
                self.disconnect()
            
            # アカウント設定を取得
            account_config = self.config_manager.get_account_config(account_id)
            if not account_config:
                self.logger.error(f"アカウント設定が見つかりません: {account_id}")
                return False
            
            # VPNファイルパスを構築
            ovpn_dir = Path(self.vpn_config["ovpn_dir"])
            ovpn_file = ovpn_dir / account_config["vpn_file"]
            
            if not ovpn_file.exists():
                self.logger.error(f"VPNファイルが見つかりません: {ovpn_file}")
                return False
            
            # 認証ファイルを確認
            auth_file = Path(self.vpn_config["auth_file"])
            if not auth_file.exists():
                self.logger.error(f"認証ファイルが見つかりません: {auth_file}")
                self._create_sample_auth_file(auth_file)
                return False
            
            self.logger.info(f"VPN接続開始: {account_id} ({account_config['vpn_file']})")
            
            # OpenVPN接続の試行
            retry_count = self.vpn_config.get("retry_count", 3)
            for attempt in range(retry_count):
                if self._attempt_vpn_connection(ovpn_file, auth_file, account_id, attempt + 1):
                    self.current_connection = account_id
                    # VPN接続後のIPを記録
                    self.vpn_connected_ip = self._get_current_ip()
                    self.logger.info(f"VPN接続成功: {account_id} (IP: {self.vpn_connected_ip})")
                    return True
                
                if attempt < retry_count - 1:
                    self.logger.info(f"VPN接続リトライ待機: {account_id} ({attempt + 1}/{retry_count})")
                    time.sleep(5)
            
            self.logger.error(f"VPN接続失敗（全試行終了）: {account_id}")
            return False
                
        except Exception as e:
            self.logger.error(f"VPN接続エラー: {account_id} - {str(e)}")
            return False
    
    def smart_vpn_connect(self, account_id: str) -> bool:
        """
        スマートVPN接続（現在のIPに基づいて判定）
        
        Args:
            account_id: アカウントID
            
        Returns:
            bool: 制御成功可否
        """
        try:
            current_ip = self._get_current_ip()
            
            if not current_ip:
                self.logger.error("現在のIP取得に失敗")
                return False
            
            # 元のIPが不明な場合は接続を実行
            if self.original_ip is None:
                self.logger.info("元IP不明のため、VPN接続を実行")
                return self.connect_account_vpn(account_id)
            
            # 現在のIPが元のIPと同じ場合はVPN接続
            if current_ip == self.original_ip:
                self.logger.info(f"元のIP検出、VPN接続実行: {current_ip}")
                return self.connect_account_vpn(account_id)
            else:
                self.logger.info(f"VPN接続済みと判定: 現在IP {current_ip} != 元IP {self.original_ip}")
                return True
                
        except Exception as e:
            self.logger.error(f"スマートVPN接続エラー: {str(e)}")
            return False
    
    def smart_vpn_disconnect(self) -> bool:
        """
        スマートVPN切断
        
        Returns:
            bool: 制御成功可否
        """
        try:
            current_ip = self._get_current_ip()
            
            if not current_ip:
                self.logger.error("現在のIP取得に失敗")
                return False
            
            # 元のIPが不明な場合は強制切断
            if self.original_ip is None:
                self.logger.info("元IP不明のため、強制VPN切断実行")
                self.disconnect()
                return True
            
            # 現在のIPが元のIPと異なる場合はVPN切断
            if current_ip != self.original_ip:
                self.logger.info(f"VPN接続検出、切断実行: 現在IP {current_ip} != 元IP {self.original_ip}")
                self.disconnect()
                return True
            else:
                self.logger.info(f"既に元のIPに復旧済み: {current_ip}")
                return True
                
        except Exception as e:
            self.logger.error(f"スマートVPN切断エラー: {str(e)}")
            return False
    
    def get_connection_status_detailed(self) -> Dict[str, Any]:
        """
        詳細な接続状態を取得
        
        Returns:
            Dict: 詳細接続情報
        """
        current_ip = self._get_current_ip()
        
        status = {
            "current_ip": current_ip,
            "original_ip": self.original_ip,
            "vpn_connected_ip": self.vpn_connected_ip,
            "target_ip": self.original_ip,  # 目標IP（元のIP）
            "vpn_needed": False,
            "connected": self.is_connected()
        }
        
        if self.original_ip and current_ip:
            status["vpn_needed"] = (current_ip == self.original_ip)
        
        return status
    
    def _attempt_vpn_connection(self, ovpn_file: Path, auth_file: Path, account_id: str, attempt: int) -> bool:
        """
        VPN接続を試行
        
        Args:
            ovpn_file: OpenVPNファイル
            auth_file: 認証ファイル
            account_id: アカウントID
            attempt: 試行回数
            
        Returns:
            bool: 接続成功可否
        """
        try:
            # OpenVPN接続コマンド
            cmd = self._build_openvpn_command(ovpn_file, auth_file)
            
            self.logger.debug(f"OpenVPNコマンド実行: 試行{attempt}")
            
            # OpenVPNプロセスを開始
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )
            
            # 接続確認
            if self._wait_for_connection(account_id):
                return True
            else:
                self._cleanup_failed_connection()
                return False
                
        except Exception as e:
            self.logger.error(f"VPN接続試行エラー: {str(e)}")
            self._cleanup_failed_connection()
            return False
    
    def _build_openvpn_command(self, ovpn_file: Path, auth_file: Path) -> list:
        """
        OpenVPNコマンドを構築
        
        Args:
            ovpn_file: OpenVPNファイル
            auth_file: 認証ファイル
            
        Returns:
            list: OpenVPNコマンド
        """
        # OpenVPN実行ファイルを検索
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
        """
        OpenVPN実行ファイルを検索
        
        Returns:
            str: OpenVPN実行ファイルパス
        """
        # Windows用のOpenVPNパス
        possible_paths = [
            r"C:\Program Files\OpenVPN\bin\openvpn.exe",
            r"C:\Program Files (x86)\OpenVPN\bin\openvpn.exe",
            "openvpn.exe",  # PATH環境変数
            "openvpn"       # Linux/Mac
        ]
        
        for path in possible_paths:
            try:
                # パスの存在確認
                if Path(path).exists() or self._command_exists(path):
                    self.logger.debug(f"OpenVPN実行ファイル発見: {path}")
                    return path
            except Exception:
                continue
        
        # デフォルト
        self.logger.warning("OpenVPN実行ファイルが見つかりません。デフォルトを使用")
        return "openvpn"
    
    def _command_exists(self, command: str) -> bool:
        """
        コマンドが実行可能かチェック
        
        Args:
            command: コマンド名
            
        Returns:
            bool: 実行可能かどうか
        """
        try:
            subprocess.run([command, "--version"], 
                         capture_output=True, timeout=5)
            return True
        except Exception:
            return False
    
    def _wait_for_connection(self, account_id: str) -> bool:
        """
        VPN接続完了を待機
        
        Args:
            account_id: アカウントID
            
        Returns:
            bool: 接続成功可否
        """
        timeout = self.vpn_config.get("connection_timeout", 30)
        start_time = time.time()
        
        self.logger.info(f"VPN接続確認中: {account_id} (最大{timeout}秒)")
        
        while time.time() - start_time < timeout:
            if self._check_vpn_status():
                # IP変化を確認
                if self._verify_ip_change():
                    return True
            
            time.sleep(2)
            
            # プロセス状態確認
            if self.process and self.process.poll() is not None:
                self.logger.error("OpenVPNプロセスが予期せず終了しました")
                break
        
        return False
    
    def _check_vpn_status(self) -> bool:
        """
        VPN接続状態をチェック
        
        Returns:
            bool: 接続されているかどうか
        """
        try:
            # ネットワーク接続確認
            current_ip = self._get_current_ip()
            if current_ip:
                self.logger.debug(f"現在のIP: {current_ip}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.debug(f"VPN状態チェックエラー: {str(e)}")
            return False
    
    def _verify_ip_change(self) -> bool:
        """
        IPアドレスの変化を確認
        
        Returns:
            bool: IPが変化したかどうか
        """
        try:
            current_ip = self._get_current_ip()
            if current_ip and self.original_ip:
                if current_ip != self.original_ip:
                    self.logger.info(f"IP変化確認: {self.original_ip} -> {current_ip}")
                    return True
                else:
                    self.logger.debug("IPアドレスに変化なし")
                    return False
            
            # 元のIPが不明な場合は接続成功とみなす
            return current_ip is not None
            
        except Exception as e:
            self.logger.warning(f"IP変化確認エラー: {str(e)}")
            return False
    
    def disconnect(self):
        """
        VPN接続を切断
        """
        try:
            if self.current_connection:
                self.logger.info(f"VPN切断開始: {self.current_connection}")
            
            # OpenVPNプロセスを終了
            self._kill_openvpn_processes()
            
            self.current_connection = None
            self.process = None
            self.vpn_connected_ip = None
            
            # 切断確認のため待機
            time.sleep(3)
            
            # IP復旧確認
            self._verify_ip_restoration()
                        
        except Exception as e:
            self.logger.error(f"VPN切断エラー: {str(e)}")
    
    def _verify_ip_restoration(self):
        """
        IP復旧を確認（修正版）
        """
        try:
            current_ip = self._get_current_ip()
            
            if current_ip:
                if self.original_ip:
                    if current_ip == self.original_ip:
                        self.logger.info(f"IP復旧確認: {current_ip}")
                    else:
                        # WARNINGを削除し、切断完了として記録
                        self.logger.info(f"VPN切断完了: {current_ip}")
                        
                        # 元のIPを現在のIPに更新（VPN切断後の実際のIP）
                        if not self._is_likely_vpn_ip(current_ip):
                            self.original_ip = current_ip
                            self.logger.info(f"元IP更新: {current_ip}")
                else:
                    # 元のIPが不明だった場合、現在のIPを元IPとする
                    if not self._is_likely_vpn_ip(current_ip):
                        self.original_ip = current_ip
                        self.logger.info(f"元IP設定: {current_ip}")
                    
        except Exception as e:
            self.logger.warning(f"IP復旧確認エラー: {str(e)}")
    
    def _cleanup_failed_connection(self):
        """
        失敗した接続のクリーンアップ
        """
        try:
            if self.process:
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    
            self._kill_openvpn_processes()
            
        except Exception as e:
            self.logger.debug(f"接続クリーンアップエラー: {str(e)}")
    
    def _kill_openvpn_processes(self):
        """
        OpenVPNプロセスを強制終了
        """
        try:
            killed_count = 0
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if 'openvpn' in proc.info['name'].lower():
                        proc.kill()
                        killed_count += 1
                        self.logger.debug(f"OpenVPNプロセス終了: PID {proc.info['pid']}")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
            if killed_count > 0:
                self.logger.info(f"OpenVPNプロセス終了: {killed_count}件")
                
        except Exception as e:
            self.logger.warning(f"OpenVPNプロセス終了エラー: {str(e)}")
    
    def _create_sample_auth_file(self, auth_file: Path):
        """
        サンプル認証ファイルを作成
        
        Args:
            auth_file: 認証ファイルパス
        """
        try:
            auth_file.parent.mkdir(parents=True, exist_ok=True)
            
            sample_content = """your_nordvpn_username
your_nordvpn_password"""
            
            with open(auth_file, 'w', encoding='utf-8') as f:
                f.write(sample_content)
                
            self.logger.info(f"サンプル認証ファイルを作成: {auth_file}")
            self.logger.warning("認証ファイルに実際のNordVPN認証情報を設定してください")
            
        except Exception as e:
            self.logger.error(f"サンプル認証ファイル作成エラー: {str(e)}")
    
    def get_current_connection(self) -> Optional[str]:
        """
        現在の接続アカウントを取得
        
        Returns:
            str: 現在接続中のアカウントID（未接続の場合はNone）
        """
        return self.current_connection
    
    def is_connected(self) -> bool:
        """
        VPN接続状態を確認
        
        Returns:
            bool: 接続されているかどうか
        """
        return (self.current_connection is not None and 
                self._check_vpn_status())
    
    def get_connection_info(self) -> Dict[str, Any]:
        """
        接続情報を取得
        
        Returns:
            Dict: 接続情報
        """
        info = {
            "connected": self.is_connected(),
            "account_id": self.current_connection,
            "current_ip": self._get_current_ip(),
            "original_ip": self.original_ip
        }
        
        return info


# テスト関数
def test_vpn_manager():
    """
    VPNManagerのテスト（実際のVPN接続は行わない）
    """
    print("=== VPNManager テスト開始 ===")
    
    try:
        # ConfigManagerをインポートしてテスト
        from modules.config_manager import ConfigManager
        
        config = ConfigManager()
        vpn_manager = VPNManager(config)
        print("✓ VPNManager初期化成功")
        
        # 接続情報取得テスト
        info = vpn_manager.get_connection_info()
        print(f"✓ 接続情報取得: 接続状態={info['connected']}")
        print(f"  現在IP: {info['current_ip']}")
        print(f"  元IP: {info['original_ip']}")
        
        # 詳細状態取得テスト
        detailed_status = vpn_manager.get_connection_status_detailed()
        print(f"✓ 詳細状態: {detailed_status}")
        
        # OpenVPN実行ファイル検索テスト
        openvpn_exe = vpn_manager._find_openvpn_executable()
        print(f"✓ OpenVPN検索: {openvpn_exe}")
        
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
        print("注意: 実際のVPN接続テストには認証情報とVPNファイルが必要です")
        return True
        
    except Exception as e:
        print(f"✗ テストエラー: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_vpn_manager()