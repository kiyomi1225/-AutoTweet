# modules/csv_manager.py - CSV管理
import pandas as pd
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

try:
    from .logger_setup import setup_module_logger
except ImportError:
    # 直接実行時の対応
    import sys
    sys.path.append('.')
    from modules.logger_setup import setup_module_logger

class CSVManager:
    def __init__(self, config_manager):
        """
        CSV管理クラス
        
        Args:
            config_manager: 設定管理インスタンス
        """
        self.config_manager = config_manager
        self.csv_config = config_manager.get_csv_config()
        self.logger = setup_module_logger("CSVManager")
        
        # データディレクトリを作成
        self.data_dir = Path(self.csv_config["data_dir"])
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info("CSV管理を初期化しました")
    
    def get_csv_path(self, account_id: str) -> Path:
        """
        指定アカウントのCSVファイルパスを取得
        
        Args:
            account_id: アカウントID
            
        Returns:
            Path: CSVファイルパス
        """
        account_config = self.config_manager.get_account_config(account_id)
        if not account_config:
            raise ValueError(f"アカウント設定が見つかりません: {account_id}")
        
        csv_filename = account_config["csv_file"]
        return self.data_dir / csv_filename
    
    def create_csv_if_not_exists(self, account_id: str):
        """
        CSVファイルが存在しない場合は作成
        
        Args:
            account_id: アカウントID
        """
        try:
            csv_path = self.get_csv_path(account_id)
            
            if not csv_path.exists():
                # デフォルトのCSV構造を作成
                df = pd.DataFrame(columns=[
                    'id', 'text', 'used', 'created_at', 'used_at', 'category', 'priority'
                ])
                
                df.to_csv(csv_path, index=False, encoding='utf-8-sig')
                self.logger.info(f"CSVファイルを作成: {csv_path}")
            else:
                self.logger.debug(f"CSVファイル存在確認: {csv_path}")
                
        except Exception as e:
            self.logger.error(f"CSVファイル作成エラー: {account_id} - {str(e)}")
            raise
    
    def add_tweets(self, account_id: str, tweets: List[str], category: str = "general") -> int:
        """
        ツイートをCSVに追加
        
        Args:
            account_id: アカウントID
            tweets: ツイートテキストのリスト
            category: ツイートカテゴリ
            
        Returns:
            int: 追加されたツイート数
        """
        try:
            self.create_csv_if_not_exists(account_id)
            csv_path = self.get_csv_path(account_id)
            
            # 既存データを読み込み
            try:
                df = pd.read_csv(csv_path, encoding='utf-8-sig')
            except pd.errors.EmptyDataError:
                df = pd.DataFrame(columns=[
                    'id', 'text', 'used', 'created_at', 'used_at', 'category', 'priority'
                ])
            
            # 新しいツイートを追加
            new_tweets = []
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            for tweet_text in tweets:
                # 重複チェック
                if not df[df['text'] == tweet_text].empty:
                    self.logger.debug(f"重複ツイートをスキップ: {tweet_text[:30]}...")
                    continue
                
                new_tweet = {
                    'id': str(uuid.uuid4()),
                    'text': tweet_text.strip(),
                    'used': False,
                    'created_at': current_time,
                    'used_at': '',
                    'category': category,
                    'priority': 1
                }
                new_tweets.append(new_tweet)
            
            if new_tweets:
                # データフレームに追加
                new_df = pd.DataFrame(new_tweets)
                df = pd.concat([df, new_df], ignore_index=True)
                
                # CSVに保存
                df.to_csv(csv_path, index=False, encoding='utf-8-sig')
                
                self.logger.info(f"ツイート追加完了: {account_id} - {len(new_tweets)}件")
                return len(new_tweets)
            else:
                self.logger.info(f"追加する新規ツイートなし: {account_id}")
                return 0
                
        except Exception as e:
            self.logger.error(f"ツイート追加エラー: {account_id} - {str(e)}")
            raise
    
    def get_unused_tweets(self, account_id: str, limit: int = None) -> List[Dict[str, Any]]:
        """
        未使用ツイートを取得
        
        Args:
            account_id: アカウントID
            limit: 取得件数制限
            
        Returns:
            List[Dict]: 未使用ツイートのリスト
        """
        try:
            self.create_csv_if_not_exists(account_id)
            csv_path = self.get_csv_path(account_id)
            
            try:
                df = pd.read_csv(csv_path, encoding='utf-8-sig')
            except pd.errors.EmptyDataError:
                self.logger.warning(f"CSVファイルが空です: {account_id}")
                return []
            
            # 未使用ツイートを抽出（usedがFalseまたはNaN）
            unused_df = df[(df['used'] == False) | (df['used'].isna())]
            
            # 優先度でソート（高い順）
            if 'priority' in unused_df.columns:
                unused_df = unused_df.sort_values('priority', ascending=False)
            
            # 制限数を適用
            if limit:
                unused_df = unused_df.head(limit)
            
            # 辞書のリストに変換
            tweets = unused_df.to_dict('records')
            
            self.logger.debug(f"未使用ツイート取得: {account_id} - {len(tweets)}件")
            return tweets
            
        except Exception as e:
            self.logger.error(f"未使用ツイート取得エラー: {account_id} - {str(e)}")
            return []
    
    def get_random_unused_tweet(self, account_id: str) -> Optional[Dict[str, Any]]:
        """
        ランダムに未使用ツイートを1件取得
        
        Args:
            account_id: アカウントID
            
        Returns:
            Dict: ツイート情報（見つからない場合はNone）
        """
        try:
            tweets = self.get_unused_tweets(account_id)
            if not tweets:
                return None
            
            # ランダム選択
            import random
            selected_tweet = random.choice(tweets)
            
            self.logger.debug(f"ランダムツイート選択: {account_id} - {selected_tweet['text'][:30]}...")
            return selected_tweet
            
        except Exception as e:
            self.logger.error(f"ランダムツイート取得エラー: {account_id} - {str(e)}")
            return None
    
    def mark_tweet_as_used(self, account_id: str, tweet_id: str) -> bool:
        """
        ツイートを使用済みとしてマーク
        
        Args:
            account_id: アカウントID
            tweet_id: ツイートID
            
        Returns:
            bool: 更新成功可否
        """
        try:
            csv_path = self.get_csv_path(account_id)
            
            df = pd.read_csv(csv_path, encoding='utf-8-sig')
            
            # 該当ツイートを検索
            tweet_mask = df['id'] == tweet_id
            if not tweet_mask.any():
                self.logger.warning(f"ツイートIDが見つかりません: {tweet_id}")
                return False
            
            # 使用済みフラグを更新
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            df.loc[tweet_mask, 'used'] = True
            df.loc[tweet_mask, 'used_at'] = current_time
            
            # CSVに保存
            df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            
            tweet_text = df.loc[tweet_mask, 'text'].iloc[0]
            self.logger.info(f"ツイートを使用済みに更新: {account_id} - {tweet_text[:30]}...")
            return True
            
        except Exception as e:
            self.logger.error(f"ツイート使用済み更新エラー: {account_id} - {str(e)}")
            return False
    
    def count_unused_tweets(self, account_id: str) -> int:
        """
        未使用ツイート数をカウント
        
        Args:
            account_id: アカウントID
            
        Returns:
            int: 未使用ツイート数
        """
        try:
            unused_tweets = self.get_unused_tweets(account_id)
            count = len(unused_tweets)
            self.logger.debug(f"未使用ツイート数: {account_id} - {count}件")
            return count
            
        except Exception as e:
            self.logger.error(f"未使用ツイートカウントエラー: {account_id} - {str(e)}")
            return 0
    
    def get_csv_stats(self, account_id: str) -> Dict[str, int]:
        """
        CSVファイルの統計情報を取得
        
        Args:
            account_id: アカウントID
            
        Returns:
            Dict: 統計情報
        """
        try:
            self.create_csv_if_not_exists(account_id)
            csv_path = self.get_csv_path(account_id)
            
            try:
                df = pd.read_csv(csv_path, encoding='utf-8-sig')
            except pd.errors.EmptyDataError:
                return {"total": 0, "used": 0, "unused": 0}
            
            total = len(df)
            used = len(df[df['used'] == True])
            unused = len(df[(df['used'] == False) | (df['used'].isna())])
            
            stats = {
                "total": total,
                "used": used,
                "unused": unused
            }
            
            self.logger.debug(f"CSV統計: {account_id} - {stats}")
            return stats
            
        except Exception as e:
            self.logger.error(f"CSV統計取得エラー: {account_id} - {str(e)}")
            return {"total": 0, "used": 0, "unused": 0}
    
    def backup_csv(self, account_id: str) -> bool:
        """
        CSVファイルのバックアップを作成
        
        Args:
            account_id: アカウントID
            
        Returns:
            bool: バックアップ成功可否
        """
        try:
            csv_path = self.get_csv_path(account_id)
            if not csv_path.exists():
                self.logger.warning(f"バックアップ対象のCSVファイルが存在しません: {account_id}")
                return False
            
            # バックアップディレクトリを作成
            backup_dir = self.data_dir / "backup"
            backup_dir.mkdir(exist_ok=True)
            
            # バックアップファイル名（タイムスタンプ付き）
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"{csv_path.stem}_backup_{timestamp}.csv"
            backup_path = backup_dir / backup_filename
            
            # ファイルをコピー
            import shutil
            shutil.copy2(csv_path, backup_path)
            
            self.logger.info(f"CSVバックアップ作成: {backup_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"CSVバックアップエラー: {account_id} - {str(e)}")
            return False
    
    def cleanup_old_backups(self, days: int = 30):
        """
        古いバックアップファイルを削除
        
        Args:
            days: 保持日数
        """
        try:
            backup_dir = self.data_dir / "backup"
            if not backup_dir.exists():
                return
            
            from datetime import timedelta
            cutoff_date = datetime.now() - timedelta(days=days)
            
            deleted_count = 0
            for backup_file in backup_dir.glob("*_backup_*.csv"):
                if backup_file.stat().st_mtime < cutoff_date.timestamp():
                    backup_file.unlink()
                    deleted_count += 1
            
            if deleted_count > 0:
                self.logger.info(f"古いバックアップファイルを削除: {deleted_count}件")
                
        except Exception as e:
            self.logger.error(f"バックアップクリーンアップエラー: {str(e)}")

# テスト関数
def test_csv_manager():
    """
    CSVManagerのテスト
    """
    print("=== CSVManager テスト開始 ===")
    
    try:
        # ConfigManagerをインポートしてテスト
        from modules.config_manager import ConfigManager
        
        config = ConfigManager()
        csv_manager = CSVManager(config)
        print("✓ CSVManager初期化成功")
        
        # テスト用アカウント
        test_account = "acc1"
        
        # CSVファイル作成テスト
        csv_manager.create_csv_if_not_exists(test_account)
        print("✓ CSVファイル作成テスト")
        
        # ツイート追加テスト
        test_tweets = [
            "テストツイート1です #test",
            "テストツイート2です #test",
            "テストツイート3です #test"
        ]
        
        added_count = csv_manager.add_tweets(test_account, test_tweets, "test")
        print(f"✓ ツイート追加: {added_count}件")
        
        # 統計情報取得テスト
        stats = csv_manager.get_csv_stats(test_account)
        print(f"✓ CSV統計: {stats}")
        
        # 未使用ツイート取得テスト
        unused_tweets = csv_manager.get_unused_tweets(test_account, limit=2)
        print(f"✓ 未使用ツイート取得: {len(unused_tweets)}件")
        
        # ランダムツイート取得テスト
        random_tweet = csv_manager.get_random_unused_tweet(test_account)
        if random_tweet:
            print(f"✓ ランダムツイート: {random_tweet['text'][:30]}...")
            
            # 使用済みマークテスト
            success = csv_manager.mark_tweet_as_used(test_account, random_tweet['id'])
            print(f"✓ 使用済みマーク: {success}")
        
        # バックアップテスト
        backup_success = csv_manager.backup_csv(test_account)
        print(f"✓ バックアップ作成: {backup_success}")
        
        print("=== CSVManager テスト完了 ===")
        return True
        
    except Exception as e:
        print(f"✗ テストエラー: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_csv_manager()