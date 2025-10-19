# modules/config_manager.py - フォルダベース版
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

try:
    from .logger_setup import setup_module_logger
except ImportError:
    import sys
    sys.path.append('.')
    from modules.logger_setup import setup_module_logger

class ConfigManager:
    def __init__(self, config_path: str = "config/config.json"):
        """設定管理クラス（フォルダベース版）"""
        self.logger = setup_module_logger("ConfigManager")
        self.config_path = Path(config_path)
        self.base_data_path = Path("C:/Users/shiki/AutoTweet/data")
        
        try:
            self.config_data = self._load_config()
            self.config = self.config_data
            self.logger.info("設定管理を初期化しました（フォルダベース）")
        except Exception as e:
            self.logger.error(f"設定管理の初期化に失敗: {str(e)}")
            raise
    
    def _load_config(self) -> Dict[str, Any]:
        """設定ファイルを読み込み"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.logger.info(f"設定ファイル読み込み完了: {self.config_path}")
                    return config
            else:
                self.logger.info("設定ファイルが存在しないため、デフォルト設定を作成します")
                return self._create_default_config()
                
        except Exception as e:
            self.logger.error(f"設定ファイル読み込みエラー: {str(e)}")
            raise
    
    def _create_default_config(self) -> Dict[str, Any]:
        """デフォルト設定を作成"""
        default_config = {
            "vpn": {
                "auth_file": "config/auth.txt",
                "ovpn_dir": "config/ovpn",
                "connection_timeout": 30,
                "retry_count": 3
            },
            "chrome": {
                "user_data_dir": "chrome_profiles",
                "headless": False,
                "window_size": [1920, 1080],
                "startup_timeout": 30,
                "executable_path": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
            },
            "gpt": {
                "prompt": "n",
                "wait_after_input": 45
            },
            "csv": {
                "data_dir": "data"
            },
            "images": {
                "image_dir": "images",
                "confidence": 0.8
            },
            "debug": {
                "enabled": False,
                "log_level": "INFO"
            }
        }
        
        self._save_config(default_config)
        self.logger.info("デフォルト設定ファイルを作成しました")
        return default_config
    
    def _save_config(self, config: Dict[str, Any]):
        """設定ファイルを保存"""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            self.logger.debug(f"設定ファイル保存完了: {self.config_path}")
        except Exception as e:
            self.logger.error(f"設定ファイル保存エラー: {str(e)}")
            raise
    
    def _detect_accounts_from_folders(self) -> List[str]:
        """dataフォルダからアカウントを自動検出"""
        accounts = []
        
        if not self.base_data_path.exists():
            self.logger.warning(f"データフォルダが存在しません: {self.base_data_path}")
            return accounts
        
        # accで始まるフォルダを検出
        for folder in self.base_data_path.iterdir():
            if folder.is_dir() and folder.name.startswith("acc"):
                # 最低限VPNファイルが存在するか確認
                vpn_files = list(folder.glob("*.ovpn"))
                if vpn_files:
                    accounts.append(folder.name)
                    self.logger.debug(f"アカウント検出: {folder.name}")
                else:
                    self.logger.warning(f"VPNファイルがないため除外: {folder.name}")
        
        accounts.sort()  # アルファベット順にソート
        self.logger.info(f"自動検出アカウント: {len(accounts)}件 - {accounts}")
        return accounts
    
    def get_all_accounts(self) -> List[str]:
        """アクティブなアカウントIDリストを取得（フォルダベース）"""
        try:
            return self._detect_accounts_from_folders()
        except Exception as e:
            self.logger.error(f"アカウント一覧取得エラー: {str(e)}")
            return []
    
    def get_account_config(self, account_id: str) -> Optional[Dict[str, Any]]:
        """特定アカウントの設定を取得（フォルダベース）"""
        try:
            account_path = self.base_data_path / account_id
            
            if not account_path.exists():
                self.logger.warning(f"アカウントフォルダが見つかりません: {account_id}")
                return None
            
            # VPNファイルを検索
            vpn_files = list(account_path.glob("*.ovpn"))
            vpn_file = vpn_files[0].name if vpn_files else None
            
            # GPT URLファイルを検索
            gpt_url = ""
            url_config = account_path / "URL_Config.txt"
            if url_config.exists():
                with open(url_config, 'r', encoding='utf-8') as f:
                    gpt_url = f.read().strip()
            
            # 動的に設定を生成
            account_info = {
                "account_id": account_id,
                "vpn_file": vpn_file,
                "chrome_profile": account_id,
                "gpt_url": gpt_url,
                "csv_file": f"data/{account_id}/tweets.csv",
                "account_path": str(account_path),
                "active": True
            }
            
            self.logger.debug(f"アカウント設定生成: {account_id}")
            return account_info
            
        except Exception as e:
            self.logger.error(f"アカウント設定取得エラー: {account_id} - {str(e)}")
            return None
    
    def validate_account_config(self, account_id: str) -> bool:
        """アカウント設定の妥当性をチェック"""
        account_path = self.base_data_path / account_id
        
        if not account_path.exists():
            self.logger.error(f"アカウントフォルダが存在しません: {account_path}")
            return False
        
        # VPNファイルの存在チェック
        vpn_files = list(account_path.glob("*.ovpn"))
        if not vpn_files:
            self.logger.error(f"VPNファイルが存在しません: {account_path}")
            return False
        
        return True
    
    # 既存のメソッド（互換性のため）
    def get_vpn_config(self) -> Dict[str, Any]:
        return self.config_data.get("vpn", {})
    
    def get_chrome_config(self) -> Dict[str, Any]:
        return self.config_data.get("chrome", {})
    
    def get_gpt_config(self) -> Dict[str, Any]:
        return self.config_data.get("gpt", {})
    
    def get_csv_config(self) -> Dict[str, Any]:
        return self.config_data.get("csv", {})
    
    def get_images_config(self) -> Dict[str, Any]:
        return self.config_data.get("images", {})
    
    def get_debug_config(self) -> Dict[str, Any]:
        return self.config_data.get("debug", {})


# テスト関数
def test_config_manager():
    """ConfigManagerのテスト（フォルダベース版）"""
    print("=== ConfigManager テスト開始（フォルダベース） ===")
    
    try:
        config = ConfigManager()
        print("✓ ConfigManager初期化成功")
        
        # アカウント一覧取得
        accounts = config.get_all_accounts()
        print(f"✓ 検出アカウント: {accounts}")
        
        # 各アカウントの設定確認
        for account_id in accounts:
            account_config = config.get_account_config(account_id)
            if account_config:
                print(f"✓ {account_id}: VPN={account_config.get('vpn_file')}")
                
                # 設定検証
                is_valid = config.validate_account_config(account_id)
                print(f"  検証結果: {'OK' if is_valid else 'NG'}")
        
        print("=== ConfigManager テスト完了 ===")
        return True
        
    except Exception as e:
        print(f"✗ テストエラー: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_config_manager()