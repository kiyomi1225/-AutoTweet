# modules/csv_manager.py - CSV管理（自動正規化版）
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional

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
        """指定アカウントのCSVファイルパスを取得"""
        return self.data_dir / f"{account_id}.csv"
    
    def _normalize_csv(self, csv_path: Path):
        """CSV正規化（id/used自動補完）"""
        try:
            if not csv_path.exists():
                return
            
            rows = []
            max_id = 0
            
            with open(csv_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if not content.strip():
                    return
                
                # ファイル再読み込み
                f.seek(0)
                reader = csv.reader(f)
                first_row = next(reader, None)
                
                if not first_row:
                    return
                
                # ヘッダー判定
                has_header = False
                if 'id' in first_row or 'text' in first_row or 'used' in first_row:
                    has_header = True
                    rows.append(['id', 'text', 'used'])
                else:
                    # ヘッダーがない場合は追加
                    rows.append(['id', 'text', 'used'])
                    # 最初の行をデータとして処理
                    if len(first_row) == 1:  # textのみ
                        rows.append(['1', first_row[0].strip(), 'False'])
                        max_id = 1
                    elif len(first_row) == 2:  # id,text
                        rows.append([first_row[0], first_row[1].strip(), 'False'])
                        max_id = int(first_row[0]) if first_row[0].isdigit() else 1
                    elif len(first_row) >= 3:  # 完全な行
                        rows.append(first_row[:3])
                        max_id = int(first_row[0]) if first_row[0].isdigit() else 1
                
                # 残りの行を処理
                for row in reader:
                    if not row or (len(row) == 1 and not row[0].strip()):
                        continue  # 空行スキップ
                    
                    if len(row) == 1:  # textのみ
                        max_id += 1
                        rows.append([str(max_id), row[0].strip(), 'False'])
                        self.logger.debug(f"自動補完: ID={max_id}, Text={row[0][:30]}...")
                    elif len(row) == 2:  # id,textのみ
                        if row[0].isdigit():
                            current_id = int(row[0])
                            max_id = max(max_id, current_id)
                            rows.append([row[0], row[1].strip(), 'False'])
                        else:
                            # idが数値でない場合は新規ID割り当て
                            max_id += 1
                            rows.append([str(max_id), row[0].strip(), 'False'])
                        self.logger.debug(f"used列追加: ID={rows[-1][0]}")
                    else:  # 完全な行
                        if row[0].isdigit():
                            current_id = int(row[0])
                            max_id = max(max_id, current_id)
                        rows.append(row[:3])
            
            # 正規化されたデータを書き戻し
            if len(rows) > 1:  # ヘッダー + データがある場合
                with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerows(rows)
                
                data_count = len(rows) - 1
                self.logger.info(f"CSV正規化完了: {csv_path.name} ({data_count}件)")
            
        except Exception as e:
            self.logger.error(f"CSV正規化エラー: {str(e)}")
    
    def create_csv_if_not_exists(self, account_id: str):
        """CSVファイルが存在しない場合は作成"""
        try:
            csv_path = self.get_csv_path(account_id)
            
            if not csv_path.exists():
                with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['id', 'text', 'used'])
                
                self.logger.info(f"CSVファイルを作成: {csv_path}")
            else:
                # 既存ファイルの正規化
                self._normalize_csv(csv_path)
                
        except Exception as e:
            self.logger.error(f"CSVファイル作成エラー: {account_id} - {str(e)}")
            raise
    
    def add_tweets(self, account_id: str, tweets: List[str]) -> int:
        """ツイートをCSVに追加"""
        try:
            self.create_csv_if_not_exists(account_id)
            csv_path = self.get_csv_path(account_id)
            
            # 既存ツイートを取得（重複チェック用）
            existing_tweets = set()
            max_id = 0
            
            if csv_path.exists():
                with open(csv_path, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    next(reader, None)  # ヘッダースキップ
                    for row in reader:
                        if len(row) >= 2:
                            existing_tweets.add(row[1])
                            if len(row) >= 1 and row[0].isdigit():
                                max_id = max(max_id, int(row[0]))
            
            # 新規ツイートのみ追加
            new_tweets = []
            for tweet_text in tweets:
                tweet_text = tweet_text.strip()
                if tweet_text and tweet_text not in existing_tweets:
                    new_tweets.append(tweet_text)
            
            if new_tweets:
                # CSVに追記
                with open(csv_path, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    for i, tweet in enumerate(new_tweets):
                        tweet_id = max_id + i + 1
                        writer.writerow([tweet_id, tweet, False])
                
                self.logger.info(f"ツイート追加完了: {account_id} - {len(new_tweets)}件")
                return len(new_tweets)
            else:
                self.logger.info(f"追加する新規ツイートなし: {account_id}")
                return 0
                
        except Exception as e:
            self.logger.error(f"ツイート追加エラー: {account_id} - {str(e)}")
            raise
    
    def get_unused_tweets(self, account_id: str, limit: int = None) -> List[Dict[str, Any]]:
        """未使用ツイートを取得"""
        try:
            self.create_csv_if_not_exists(account_id)
            csv_path = self.get_csv_path(account_id)
            
            tweets = []
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader, None)  # ヘッダースキップ
                
                for row in reader:
                    if len(row) >= 3:
                        tweet_id, text, used = row[0], row[1], row[2]
                        if used.lower() in ['false', '0', '']:
                            tweets.append({
                                'id': tweet_id,
                                'text': text,
                                'used': False
                            })
            
            # 制限数を適用
            if limit:
                tweets = tweets[:limit]
            
            self.logger.debug(f"未使用ツイート取得: {account_id} - {len(tweets)}件")
            return tweets
            
        except Exception as e:
            self.logger.error(f"未使用ツイート取得エラー: {account_id} - {str(e)}")
            return []
    
    def mark_tweet_as_used(self, account_id: str, tweet_id: str) -> bool:
        """ツイートを使用済みとしてマーク"""
        try:
            csv_path = self.get_csv_path(account_id)
            
            # 全データを読み込み
            rows = []
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = list(reader)
            
            # 該当ツイートを更新
            updated = False
            for i, row in enumerate(rows):
                if len(row) >= 3 and row[0] == tweet_id:
                    rows[i][2] = 'True'  # used を True に
                    updated = True
                    break
            
            if updated:
                # ファイルに書き戻し
                with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerows(rows)
                
                self.logger.info(f"ツイートを使用済みに更新: {account_id} - ID:{tweet_id}")
                return True
            else:
                self.logger.warning(f"ツイートIDが見つかりません: {tweet_id}")
                return False
            
        except Exception as e:
            self.logger.error(f"ツイート使用済み更新エラー: {account_id} - {str(e)}")
            return False
    
    def get_csv_stats(self, account_id: str) -> Dict[str, int]:
        """CSVファイルの統計情報を取得"""
        try:
            self.create_csv_if_not_exists(account_id)
            csv_path = self.get_csv_path(account_id)
            
            total = 0
            used = 0
            
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader, None)  # ヘッダースキップ
                
                for row in reader:
                    if len(row) >= 3:
                        total += 1
                        if row[2].lower() in ['true', '1']:
                            used += 1
            
            unused = total - used
            stats = {"total": total, "used": used, "unused": unused}
            
            self.logger.debug(f"CSV統計: {account_id} - {stats}")
            return stats
            
        except Exception as e:
            self.logger.error(f"CSV統計取得エラー: {account_id} - {str(e)}")
            return {"total": 0, "used": 0, "unused": 0}
    
    # 追加メソッド（互換性のため）
    def count_unused_tweets(self, account_id: str) -> int:
        """未使用ツイート数を取得"""
        stats = self.get_csv_stats(account_id)
        return stats.get("unused", 0)
    
    def get_random_unused_tweet(self, account_id: str) -> Optional[Dict[str, Any]]:
        """ランダムに未使用ツイートを1件取得"""
        import random
        unused_tweets = self.get_unused_tweets(account_id)
        if unused_tweets:
            return random.choice(unused_tweets)
        return None


# テスト関数
def test_csv_manager():
    """CSVManagerのテスト（正規化機能含む）"""
    print("=== CSVManager テスト開始 ===")
    
    try:
        from modules.config_manager import ConfigManager
        
        config = ConfigManager()
        csv_manager = CSVManager(config)
        print("✓ CSVManager初期化成功")
        
        # テスト用アカウント
        test_account = "test_normalize"
        test_csv = csv_manager.get_csv_path(test_account)
        
        # テスト1: 不完全なCSV作成
        print("\n[テスト1] 不完全なCSV作成")
        with open(test_csv, 'w', encoding='utf-8') as f:
            f.write("既存ツイート1\n")
            f.write("既存ツイート2\n")
            f.write("手動で追加したツイート\n")
        
        # 正規化実行
        csv_manager.create_csv_if_not_exists(test_account)
        
        # 結果確認
        with open(test_csv, 'r', encoding='utf-8') as f:
            content = f.read()
            print("正規化後のCSV:")
            print(content)
        
        # テスト2: 部分的なCSV
        print("\n[テスト2] 部分的なCSV（id,textのみ）")
        with open(test_csv, 'w', encoding='utf-8') as f:
            f.write("id,text\n")
            f.write("1,既存ツイート1\n")
            f.write("2,既存ツイート2\n")
            f.write("新規追加ツイート\n")
        
        csv_manager.create_csv_if_not_exists(test_account)
        
        with open(test_csv, 'r', encoding='utf-8') as f:
            content = f.read()
            print("正規化後のCSV:")
            print(content)
        
        # 統計確認
        stats = csv_manager.get_csv_stats(test_account)
        print(f"\n統計情報: {stats}")
        
        # クリーンアップ
        if test_csv.exists():
            test_csv.unlink()
            print("\n✓ テストファイル削除完了")
        
        print("\n=== CSVManager テスト完了 ===")
        return True
        
    except Exception as e:
        print(f"✗ テストエラー: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_csv_manager()