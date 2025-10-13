# modules/config_manager.py - 設定管理（CSV対応版）
import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional
import csv

try:
    from .logger_setup import setup_module_logger
except ImportError:
    # 直接実行時の対応
    import sys
    sys.path.append('.')
    from modules.logger_setup import setup_module_logger

class ConfigManager:
    def __init__(self, config_path: str = "config/config.json"):
        """
        設定管理クラス
        
        Args:
            config_path: 設定ファイルのパス
        """
        self.logger = setup_module_logger("ConfigManager")
        self.config_path = Path(config_path)
        
        try:
            self.config_data = self._load_config()
            self.account_data = self._load_account_database()
            self.logger.info("設定管理を初期化しました")
        except Exception as e:
            self.logger.error(f"設定管理の初期化に失敗: {str(e)}")
            raise
    
    def _load_config(self) -> Dict[str, Any]:
        """
        設定ファイルを読み込み
        """
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.logger.info(f"設定ファイル読み込み完了: {self.config_path}")
                    return config
            else:
                self.logger.info("設定ファイルが存在しないため、デフォルト設定を作成します")
                return self._create_default_config()
                
        except json.JSONDecodeError as e:
            self.logger.error(f"設定ファイルのJSON形式が不正: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"設定ファイル読み込みエラー: {str(e)}")
            raise
    
    def _create_default_config(self) -> Dict[str, Any]:
        """
        デフォルト設定を作成
        """
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
                "startup_timeout": 30
            },
            "gpt": {
                "prompt": "n",
                "max_tweets_per_fetch": 20,
                "fetch_timeout": 300,
                "retry_count": 3,
                "wait_between_requests": 2
            },
            "posting": {
                "schedule": ["09:00", "15:00", "21:00"],
                "account_interval": 300,
                "retry_count": 3,
                "post_delay": 5
            },
            "csv": {
                "data_dir": "data",
                "min_unused_tweets": 10
            },
            "images": {
                "image_dir": "images",
                "confidence": 0.8,
                "timeout": 10
            },
            "debug": {
                "enabled": False,
                "screenshot_on_error": True,
                "log_level": "INFO"
            }
        }
        
        self._save_config(default_config)
        self.logger.info("デフォルト設定ファイルを作成しました")
        return default_config
    
    def _save_config(self, config: Dict[str, Any]):
        """
        設定ファイルを保存
        """
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            self.logger.debug(f"設定ファイル保存完了: {self.config_path}")
        except Exception as e:
            self.logger.error(f"設定ファイル保存エラー: {str(e)}")
            raise
    
    def _load_account_database(self) -> pd.DataFrame:
        """
        アカウントデータベースを読み込み（CSV形式対応）
        """
        csv_path = Path("config/account_database.csv")
        excel_path = Path("config/account_database.xlsx")
        
        try:
            # CSVファイルを優先して読み込み
            if csv_path.exists():
                self.logger.info(f"CSVファイルからアカウントデータを読み込み: {csv_path}")
                df = pd.read_csv(csv_path, encoding='utf-8')
                
                # 列名をマッピング（日本語列名から英語に変換）
                column_mapping = {
                    "アカウント名": "account_id",
                    "VPNサーバー": "vpn_file", 
                    "Chromeプロファイル": "chrome_profile",
                    "GPTs URL": "gpt_url",
                    "ツイートCSV": "csv_file",
                    "googleアドレス": "google_address",
                    "PassWord": "password",
                    "再設定用アドレス": "recovery_address",
                    "2FA token": "tfa_token"
                }
                
                # 列名を変換（存在する列のみ）
                df = df.rename(columns=column_mapping)
                
            # Excelファイルも確認（後方互換性）
            elif excel_path.exists():
                self.logger.info(f"Excelファイルからアカウントデータを読み込み: {excel_path}")
                
                # シート名を動的に取得
                excel_file = pd.ExcelFile(excel_path)
                sheet_names = excel_file.sheet_names
                self.logger.info(f"利用可能なシート: {sheet_names}")
                
                # 最初のシートを使用
                df = pd.read_excel(excel_path, sheet_name=sheet_names[0])
                
                # 列名をマッピング
                column_mapping = {
                    "アカウント名": "account_id",
                    "VPNサーバー": "vpn_file", 
                    "Chromeプロファイル": "chrome_profile",
                    "GPTs URL": "gpt_url",
                    "ツイートCSV": "csv_file",
                    "googleアドレス": "google_address",
                    "PassWord": "password",
                    "再設定用アドレス": "recovery_address",
                    "2FA token": "tfa_token"
                }
                
                df = df.rename(columns=column_mapping)
                
                # ExcelをCSVに変換して保存
                self._convert_excel_to_csv(df, csv_path)
                
            else:
                self.logger.info("アカウントデータベースが存在しないため、デフォルトを作成します")
                return self._create_default_account_database()
            
            # データの後処理
            df = self._process_account_dataframe(df)
            
            self.logger.info(f"アカウントデータベース読み込み完了: {len(df)}件")
            self.logger.info(f"読み込まれたアカウント: {df['account_id'].tolist()}")
            
            return df
                
        except Exception as e:
            self.logger.error(f"アカウントデータベース読み込みエラー: {str(e)}")
            raise
    
    def _process_account_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        アカウントデータフレームの後処理
        """
        # 必要な列が存在することを確認
        required_columns = ["account_id", "vpn_file", "chrome_profile", "gpt_url", "csv_file"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            self.logger.error(f"必要な列が不足: {missing_columns}")
            raise ValueError(f"必要な列が不足: {missing_columns}")
        
        # 空の行を除去
        df = df.dropna(subset=["account_id"])
        
        # account_idが文字列であることを確認
        df["account_id"] = df["account_id"].astype(str)
        
        # activeカラムを追加（デフォルトTrue）
        if "active" not in df.columns:
            df["active"] = True
        
        # アカウント名からプロファイル名を正規化（chrome_profiles/acc1 -> acc1）
        df["chrome_profile"] = df["chrome_profile"].apply(
            lambda x: x.split("/")[-1] if "/" in str(x) else str(x)
        )
        
        # CSVファイルパスの正規化
        df["csv_file"] = df["csv_file"].apply(
            lambda x: x if x.startswith("data/") else f"data/{x}" if not x.endswith(".csv") else f"data/{x}"
        )
        
        return df
    
    def _convert_excel_to_csv(self, df: pd.DataFrame, csv_path: Path):
        """
        ExcelデータをCSVに変換して保存
        """
        try:
            # 日本語ヘッダーで保存
            japanese_columns = {
                "account_id": "アカウント名",
                "vpn_file": "VPNサーバー",
                "chrome_profile": "Chromeプロファイル", 
                "gpt_url": "GPTs URL",
                "csv_file": "ツイートCSV",
                "google_address": "googleアドレス",
                "password": "PassWord",
                "recovery_address": "再設定用アドレス",
                "tfa_token": "2FA token"
            }
            
            # 存在する列のみを変換
            csv_columns = {k: v for k, v in japanese_columns.items() if k in df.columns}
            csv_df = df[list(csv_columns.keys())].copy()
            csv_df = csv_df.rename(columns=csv_columns)
            
            # CSVとして保存
            csv_df.to_csv(csv_path, index=False, encoding='utf-8')
            self.logger.info(f"ExcelデータをCSVに変換: {csv_path}")
            
        except Exception as e:
            self.logger.warning(f"CSV変換エラー: {str(e)}")
    
    def _create_default_account_database(self) -> pd.DataFrame:
        """
        デフォルトのアカウントデータベースを作成（CSV形式）
        """
        default_accounts = pd.DataFrame({
            "account_id": ["acc1", "acc2"],
            "vpn_file": ["jp429.nordvpn.com.udp.ovpn", "jp454.nordvpn.com.udp.ovpn"],
            "chrome_profile": ["acc1", "acc2"],
            "gpt_url": [
                "https://chatgpt.com/g/your_gpt_url_acc1",
                "https://chatgpt.com/g/your_gpt_url_acc2"
            ],
            "csv_file": ["data/acc1.csv", "data/acc2.csv"],
            "google_address": ["example1@gmail.com", "example2@gmail.com"],
            "password": ["", ""],
            "recovery_address": ["", ""],
            "tfa_token": ["", ""],
            "active": [True, True]
        })
        
        csv_path = Path("config/account_database.csv")
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 日本語ヘッダーで保存
        japanese_columns = {
            "account_id": "アカウント名",
            "vpn_file": "VPNサーバー",
            "chrome_profile": "Chromeプロファイル", 
            "gpt_url": "GPTs URL",
            "csv_file": "ツイートCSV",
            "google_address": "googleアドレス",
            "password": "PassWord",
            "recovery_address": "再設定用アドレス",
            "tfa_token": "2FA token"
        }
        
        # 日本語ヘッダー用のDataFrameを作成
        japanese_df = default_accounts[list(japanese_columns.keys())].copy()
        japanese_df = japanese_df.rename(columns=japanese_columns)
        
        # CSVとして保存
        japanese_df.to_csv(csv_path, index=False, encoding='utf-8')
        
        self.logger.info(f"デフォルトアカウントデータベースを作成: {csv_path}")
        return default_accounts
    
    def get_all_accounts(self) -> List[str]:
        """
        アクティブなアカウントIDリストを取得
        """
        try:
            active_accounts = self.account_data[self.account_data["active"] == True]
            account_list = active_accounts["account_id"].tolist()
            self.logger.debug(f"アクティブアカウント: {account_list}")
            return account_list
        except Exception as e:
            self.logger.error(f"アカウント一覧取得エラー: {str(e)}")
            return []
    
    def get_account_config(self, account_id: str) -> Optional[Dict[str, Any]]:
        """
        特定アカウントの設定を取得
        """
        try:
            account_row = self.account_data[self.account_data["account_id"] == account_id]
            if account_row.empty:
                self.logger.warning(f"アカウントが見つかりません: {account_id}")
                return None
            
            account_info = account_row.iloc[0].to_dict()
            self.logger.debug(f"アカウント設定取得: {account_id}")
            return account_info
            
        except Exception as e:
            self.logger.error(f"アカウント設定取得エラー: {account_id} - {str(e)}")
            return None
    
    def validate_account_config(self, account_id: str) -> bool:
        """
        アカウント設定の妥当性をチェック
        """
        config = self.get_account_config(account_id)
        if not config:
            return False
        
        # 必須項目のチェック
        required_fields = ["vpn_file", "chrome_profile", "gpt_url", "csv_file"]
        for field in required_fields:
            if not config.get(field):
                self.logger.error(f"必須フィールドが空: {account_id}.{field}")
                return False
        
        # VPNファイルの存在チェック
        vpn_path = Path(self.get_vpn_config()["ovpn_dir"]) / config["vpn_file"]
        if not vpn_path.exists():
            self.logger.error(f"VPNファイルが存在しません: {vpn_path}")
            return False
        
        return True
    
    def get_vpn_config(self) -> Dict[str, Any]:
        """VPN設定を取得"""
        return self.config_data.get("vpn", {})
    
    def get_chrome_config(self) -> Dict[str, Any]:
        """Chrome設定を取得"""
        return self.config_data.get("chrome", {})
    
    def get_gpt_config(self) -> Dict[str, Any]:
        """GPT設定を取得"""
        return self.config_data.get("gpt", {})
    
    def get_posting_config(self) -> Dict[str, Any]:
        """投稿設定を取得"""
        return self.config_data.get("posting", {})
    
    def get_csv_config(self) -> Dict[str, Any]:
        """CSV設定を取得"""
        return self.config_data.get("csv", {})
    
    def get_images_config(self) -> Dict[str, Any]:
        """画像設定を取得"""
        return self.config_data.get("images", {})
    
    def get_debug_config(self) -> Dict[str, Any]:
        """デバッグ設定を取得"""
        return self.config_data.get("debug", {})
    
    def get_posting_schedule(self) -> List[str]:
        """投稿スケジュールを取得"""
        return self.get_posting_config().get("schedule", [])
    
    def get_account_interval(self) -> int:
        """アカウント間の待機時間を取得"""
        return self.get_posting_config().get("account_interval", 300)
    
    def update_account_status(self, account_id: str, active: bool):
        """
        アカウントのアクティブ状態を更新
        """
        try:
            self.account_data.loc[
                self.account_data["account_id"] == account_id, "active"
            ] = active
            
            # CSVファイルに保存
            csv_path = Path("config/account_database.csv")
            
            # 日本語ヘッダーで保存
            japanese_columns = {
                "account_id": "アカウント名",
                "vpn_file": "VPNサーバー",
                "chrome_profile": "Chromeプロファイル", 
                "gpt_url": "GPTs URL",
                "csv_file": "ツイートCSV",
                "google_address": "googleアドレス",
                "password": "PassWord",
                "recovery_address": "再設定用アドレス",
                "tfa_token": "2FA token"
            }
            
            save_df = self.account_data[list(japanese_columns.keys())].copy()
            save_df = save_df.rename(columns=japanese_columns)
            save_df.to_csv(csv_path, index=False, encoding='utf-8')
            
            self.logger.info(f"アカウント状態更新: {account_id} -> {active}")
            
        except Exception as e:
            self.logger.error(f"アカウント状態更新エラー: {str(e)}")
            raise
    
    def update_last_post_time(self, account_id: str, timestamp: str):
        """
        最終投稿時刻を更新
        """
        try:
            self.account_data.loc[
                self.account_data["account_id"] == account_id, "last_post"
            ] = timestamp
            
            # CSVファイルに保存
            csv_path = Path("config/account_database.csv")
            self.account_data.to_csv(csv_path, index=False, encoding='utf-8')
                
            self.logger.debug(f"最終投稿時刻更新: {account_id} -> {timestamp}")
            
        except Exception as e:
            self.logger.error(f"最終投稿時刻更新エラー: {str(e)}")


# ユーティリティ関数
def convert_excel_to_csv():
    """
    既存のExcelファイルをCSVに変換するユーティリティ
    """
    print("=== Excel → CSV 変換ユーティリティ ===")
    
    try:
        excel_path = Path("config/account_database.xlsx")
        csv_path = Path("config/account_database.csv")
        
        if excel_path.exists():
            print(f"📁 Excelファイル発見: {excel_path}")
            
            # Excelファイルを読み込み
            excel_file = pd.ExcelFile(excel_path)
            sheet_names = excel_file.sheet_names
            print(f"📋 利用可能なシート: {sheet_names}")
            
            # 最初のシートを読み込み
            df = pd.read_excel(excel_path, sheet_name=sheet_names[0])
            
            print(f"📊 データ行数: {len(df)}行")
            print(f"📋 列名: {list(df.columns)}")
            
            # CSVとして保存
            df.to_csv(csv_path, index=False, encoding='utf-8')
            
            print(f"✅ CSV変換完了: {csv_path}")
            print(f"📝 内容確認:")
            
            # 最初の3行を表示
            with open(csv_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for i, line in enumerate(lines[:5]):
                    print(f"  {i+1}: {line.strip()}")
            
            # Excelファイルをバックアップ
            backup_path = excel_path.with_suffix('.xlsx.backup')
            excel_path.rename(backup_path)
            print(f"📦 Excelファイルをバックアップ: {backup_path}")
            
        else:
            print(f"❌ Excelファイルが見つかりません: {excel_path}")
            
        print("=== 変換完了 ===")
        
    except Exception as e:
        print(f"❌ 変換エラー: {str(e)}")
        import traceback
        traceback.print_exc()


def create_sample_csv():
    """
    サンプルCSVファイルを作成
    """
    print("=== サンプルCSV作成 ===")
    
    try:
        csv_path = Path("config/account_database.csv")
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        
        # サンプルデータ
        sample_data = [
            ["アカウント名", "VPNサーバー", "Chromeプロファイル", "GPTs URL", "ツイートCSV", "googleアドレス", "PassWord", "再設定用アドレス", "2FA token"],
            ["acc1", "jp429.nordvpn.com.udp.ovpn", "acc1", "https://chatgpt.com/g/your_gpt_url_acc1", "data/acc1.csv", "imetecuqodu47@gmail.com", "", "", ""],
            ["acc2", "jp454.nordvpn.com.udp.ovpn", "acc2", "https://chatgpt.com/g/your_gpt_url_acc2", "data/acc2.csv", "ucajowo570@gmail.com", "", "", ""],
            ["acc3", "jp514.nordvpn.com.udp.ovpn", "acc3", "https://chatgpt.com/g/your_gpt_url_acc1", "data/acc3.csv", "icasasemo60@gmail.com", "", "", ""],
            ["acc4", "jp515.nordvpn.com.udp.ovpn", "acc4", "https://chatgpt.com/g/your_gpt_url_acc2", "data/acc4.csv", "ogaqagiwa457@gmail.com", "", "", ""],
            ["acc5", "jp516.nordvpn.com.udp.ovpn", "acc5", "https://chatgpt.com/g/your_gpt_url_acc1", "data/acc5.csv", "ejidutiracam20@gmail.com", "", "", ""],
        ]
        
        # CSVファイルに書き込み
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(sample_data)
        
        print(f"✅ サンプルCSV作成完了: {csv_path}")
        print(f"📝 内容:")
        
        # 内容を表示
        with open(csv_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for i, line in enumerate(lines):
                print(f"  {i+1}: {line.strip()}")
        
        print("=== 作成完了 ===")
        
    except Exception as e:
        print(f"❌ 作成エラー: {str(e)}")


# テスト関数
def test_config_manager():
    """
    ConfigManagerのテスト
    """
    print("=== ConfigManager テスト開始 ===")
    
    try:
        # ConfigManagerを初期化
        config = ConfigManager()
        print("✓ ConfigManager初期化成功")
        
        # 設定取得テスト
        vpn_config = config.get_vpn_config()
        print(f"✓ VPN設定取得: {vpn_config.get('auth_file')}")
        
        # アカウント一覧取得
        accounts = config.get_all_accounts()
        print(f"✓ アカウント一覧: {accounts}")
        
        # 個別アカウント設定取得
        if accounts:
            account_config = config.get_account_config(accounts[0])
            print(f"✓ アカウント設定取得: {accounts[0]}")
            
            # 設定検証
            is_valid = config.validate_account_config(accounts[0])
            print(f"✓ 設定検証: {is_valid}")
        
        print("=== ConfigManager テスト完了 ===")
        return True
        
    except Exception as e:
        print(f"✗ テストエラー: {str(e)}")
        return False

if __name__ == "__main__":
    # ユーティリティ選択
    print("=== ConfigManager ユーティリティ ===")
    print("1. テスト実行")
    print("2. Excel→CSV変換")
    print("3. サンプルCSV作成")
    
    choice = input("選択 (1-3): ")
    
    if choice == "1":
        test_config_manager()
    elif choice == "2":
        convert_excel_to_csv()
    elif choice == "3":
        create_sample_csv()
    else:
        print("❌ 無効な選択です")