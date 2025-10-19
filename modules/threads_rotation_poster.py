# modules/threads_rotation_poster.py - Threads循環投稿
import time
import random
import pyautogui
import csv  
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

try:
    from .logger_setup import setup_module_logger
except ImportError:
    import sys
    sys.path.append('.')
    from modules.logger_setup import setup_module_logger

class ThreadsRotationPoster:
    def __init__(self, config_manager, vpn_manager, chrome_manager, discord_notifier=None):
        """Threads循環投稿クラス"""
        self.discord_notifier = discord_notifier
        self.config_manager = config_manager
        self.vpn_manager = vpn_manager
        self.chrome_manager = chrome_manager
        self.logger = setup_module_logger("ThreadsRotationPoster")
        # 基本データパス追加
        self.base_data_path = Path("C:/Users/shiki/AutoTweet/data")
        
        # 画像認識設定
        self.images_config = config_manager.get_images_config()
        self.image_dir = Path(self.images_config.get("image_dir", "images"))
        self.confidence = self.images_config.get("confidence", 0.8)
        
        # PyAutoGUI設定
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 1
        
        self.logger.info("Threads循環投稿を初期化しました")

    def _get_csv_path(self, account_id: str) -> Path:
        """アカウントのCSVファイルパスを取得"""
        return self.base_data_path / account_id / "tweets.csv"
    
    def count_unused_tweets(self, account_id: str) -> int:
        """未使用ツイート数をカウント"""
        csv_path = self._get_csv_path(account_id)
        if not csv_path.exists():
            return 0
        
        count = 0
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('used', '').lower() in ['false', '0', '']:
                    count += 1
        return count
    
    def get_random_unused_tweet(self, account_id: str) -> Optional[Dict[str, str]]:
        """ランダムに未使用ツイートを取得"""
        csv_path = self._get_csv_path(account_id)
        if not csv_path.exists():
            return None
        
        unused_tweets = []
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('used', '').lower() in ['false', '0', '']:
                    unused_tweets.append(row)
        
        if unused_tweets:
            return random.choice(unused_tweets)
        return None
    
    def mark_tweet_as_used(self, account_id: str, tweet_id: str) -> bool:
        """ツイートを使用済みにマーク"""
        csv_path = self._get_csv_path(account_id)
        if not csv_path.exists():
            return False
        
        rows = []
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            for row in reader:
                if row['id'] == tweet_id:
                    row['used'] = 'True'
                rows.append(row)
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        return True
    
    def run_rotation_posting(self, account_ids: List[str], min_wait: int = 30, max_wait: int = 60) -> bool:
            """循環投稿実行（VPN切り替え対応版）"""
            try:
                self.logger.info(f"Threads循環投稿開始: {account_ids}")
                
                # 枯渇スキップ用のアクティブアカウントリスト
                active_accounts = account_ids.copy()
                
                while len(active_accounts) > 0:
                    for account_id in active_accounts.copy():
                        # 未使用ツイート数チェック
                        unused_count = self.count_unused_tweets(account_id)
                        if unused_count == 0:
                            self.logger.info(f"❌ {account_id} 枯渇により除外")
                            active_accounts.remove(account_id)
                            continue
                        
                        self.logger.info(f"🔄 {account_id} 投稿開始 (残り{unused_count}件)")
                        
                        # アカウント投稿実行（VPN切り替え含む）
                        success = self._post_for_account_with_vpn_switch(account_id)
                        
                        if success is True:
                            self.logger.info(f"✅ {account_id} 投稿成功")
                            # 🆕 Discord通知: 投稿成功
                            if self.discord_notifier:
                                self.discord_notifier.notify_account_complete(account_id, 1, "投稿：成功")
                        elif success is None:
                            self.logger.info(f"⏰ {account_id} 時間外")
                            if self.discord_notifier:
                                self.discord_notifier.notify_account_complete(account_id, 1, "投稿：時間外")                            
                        else:  # success is False
                            self.logger.warning(f"❌ {account_id} 投稿失敗")
                            if self.discord_notifier:
                                self.discord_notifier.notify_account_complete(account_id, 1, "投稿：失敗")

                        # 次のアカウントまで待機（○○分）
                        if len(active_accounts) > 1:  # 最後のアカウント以外
                            wait_minutes = random.randint(min_wait, max_wait)
                            self.logger.info(f"⏳ 次のアカウントまで{wait_minutes}分待機...")
                            time.sleep(wait_minutes * 60)
                
                self.logger.info("🎉 全アカウント枯渇により循環投稿終了")
                return True
                
            except KeyboardInterrupt:
                self.logger.info("⚠️ ユーザーによる中断")
                return False
            except Exception as e:
                self.logger.error(f"循環投稿エラー: {str(e)}")
                return False
            finally:
                # 最終VPN切断
                try:
                    self.vpn_manager.disconnect()
                    self.logger.info("最終VPN切断完了")
                except:
                    pass

    def _post_for_account_with_vpn_switch(self, account_id: str) -> bool:
        """VPN切り替え付きアカウント投稿処理（スマート切り替え版）"""
        tweet_data = None

        # ⏰ 時間帯チェック（ここに追加）
        current_hour = datetime.now().hour
        allowed_start = self.config_manager.config.get('posting_hours', {}).get('start', 6)
        allowed_end = self.config_manager.config.get('posting_hours', {}).get('end', 24)
        
        if not (allowed_start <= current_hour < allowed_end):
            self.logger.info(f"⏰ 投稿時間外: {current_hour}時 (許可: {allowed_start}-{allowed_end}時)")
            return None
        
        try:
            # 1. 現在のIPを記録
            current_ip_before = self.vpn_manager._get_current_ip()
            self.logger.info(f"🔄 VPN切り替え開始: {account_id} (現在IP: {current_ip_before})")
            
            # 2. 既存VPN接続を確実に切断
            self.vpn_manager.disconnect()
            time.sleep(10)  # 切断完了待機（VPNプロセス終了確保）
            
            # 3. 指定アカウント専用VPNに接続
            max_attempts = 3
            for attempt in range(max_attempts):
                vpn_success = self.vpn_manager.connect_account_vpn(account_id)
                if not vpn_success:
                    if attempt < max_attempts - 1:
                        self.logger.warning(f"VPN接続失敗、リトライ中... ({attempt + 1}/{max_attempts})")
                        time.sleep(15)  # リトライ前待機時間延長
                        continue
                    else:
                        raise Exception(f"VPN接続失敗: {account_id}")
                
                # 接続安定化待機
                time.sleep(8)  # VPN接続安定化待機
                
                # 4. IP変化確認
                vpn_info = self.vpn_manager.get_connection_info()
                current_ip_after = vpn_info['current_ip']
                
                if current_ip_after != current_ip_before:
                    self.logger.info(f"✅ VPN切り替え成功: {account_id} → {current_ip_after}")
                    break
                else:
                    if attempt < max_attempts - 1:
                        self.logger.warning(f"IP変化なし、再試行中... ({current_ip_after})")
                        self.vpn_manager.disconnect()
                        time.sleep(10)
                    else:
                        self.logger.warning(f"⚠️ IP変化なし、継続実行: {current_ip_after}")
                        # IP変化がなくても処理続行（同一サーバーの可能性）
                        
            # 5. Threads PWA起動（プロファイル指定）
            import subprocess
            cmd = f'"C:\\Program Files\\Google\\Chrome\\Application\\chrome_proxy.exe" --profile-directory={account_id} --app-id=jhfafgojnlneaffmkkjbcpnadneeocbk'
            subprocess.run(cmd, shell=True)
            time.sleep(10)  # PWA起動待機
            
            # 6. ページ準備
            # ウィンドウ最大化ボタン（あれば押す）
            maximize_image = self.image_dir / "window_maximize_button.png"
            try:
                location = pyautogui.locateOnScreen(str(maximize_image), confidence=self.confidence)
                if location:
                    center = pyautogui.center(location)
                    pyautogui.click(center.x, center.y)
                    self.logger.info(f"ウィンドウ最大化クリック")
                    time.sleep(2)
            except:
                pass  # なければスキップ            

            # 7. ツイート取得（まだ使用済みにしない）
            tweet_data = self.get_random_unused_tweet(account_id)
            if not tweet_data:
                raise Exception("投稿可能ツイートなし")
            
            self.logger.info(f"ツイート選択: {tweet_data['text'][:30]}...")
            
            # 8. Threads投稿実行
            post_success = self._execute_threads_post(tweet_data['text'])
            
            # 9. 投稿成功した場合のみ使用済みマーク
            if post_success:
                self.mark_tweet_as_used(account_id, tweet_data['id'])
                self.logger.info("✅ 投稿成功・使用済み化完了")
                return True
            else:
                self.logger.warning("⚠️ 投稿失敗（ツイートは未使用のまま保持）")
                return False
            
        except Exception as e:
            self.logger.error(f"投稿処理エラー: {account_id} - {str(e)}")
            return False
            
        finally:
            # 必須クリーンアップ: Chrome終了 → VPN切断
            try:
                self.logger.info(f"🧹 クリーンアップ開始: {account_id}")
                
                # 閉じる時（finallyブロック内）
                close_image = self.image_dir / "close_button_PWA.png"
                try:
                    location = pyautogui.locateOnScreen(str(close_image), confidence=self.confidence)
                    if location:
                        center = pyautogui.center(location)
                        pyautogui.click(center.x, center.y)
                        time.sleep(2)
                except:
                    pass
                
                # VPN切断
                self.vpn_manager.disconnect()
                
            except Exception as cleanup_error:
                self.logger.warning(f"⚠ クリーンアップエラー: {account_id} - {str(cleanup_error)}")

    def _execute_threads_post(self, content: str) -> bool:
        """Threads投稿実行（デバッグ強化版）"""
        try:
            self.logger.info("📝 Threads投稿プロセス開始")
            
            # テキストエリア認識・クリック
            if not self._click_threads_textarea():
                self.logger.error("❌ テキストエリアが見つかりませんでした")
                return False
            self.logger.info("✅ テキストエリアクリック成功")
            
            # 投稿内容入力
            import pyperclip
            pyperclip.copy(content)
            time.sleep(2)
            
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(5)
            
            # 投稿ボタンクリック
            if not self._click_threads_post_button():
                self.logger.error("❌ 投稿ボタンが見つかりませんでした")
                return False
            self.logger.info("✅ 投稿ボタンクリック成功")
            
            time.sleep(5)
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Threads投稿エラー: {str(e)}")
            import traceback
            self.logger.error(f"詳細: {traceback.format_exc()}")
            return False
        
    def _click_threads_textarea(self) -> bool:
        """Threadsテキストエリアクリック（デバッグ強化版）"""
        try:
            textarea_image = self.image_dir / "threads_textarea.png"
            if not textarea_image.exists():
                self.logger.error(f"❌ 画像ファイルが存在しません: {textarea_image}")
                return False
                        
            for attempt in range(3):
                try:
                    location = pyautogui.locateOnScreen(str(textarea_image), confidence=self.confidence)
                    if location:
                        center = pyautogui.center(location)
                        pyautogui.click(center.x, center.y)
                        time.sleep(1)
                        return True
                    else:
                        self.logger.warning(f"⚠️ 試行{attempt + 1}: テキストエリアが見つかりません")
                except pyautogui.ImageNotFoundException:
                    self.logger.warning(f"⚠️ 試行{attempt + 1}: ImageNotFoundException")
                
                if attempt < 2:
                    self.logger.info("⏳ 2秒待機して再試行...")
                    time.sleep(2)
            
            self.logger.error("❌ 3回の試行すべて失敗")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ テキストエリア認識エラー: {str(e)}")
            import traceback
            self.logger.error(f"詳細: {traceback.format_exc()}")
            return False
        
    def _click_threads_post_button(self) -> bool:
        """Threads投稿ボタンクリック（デバッグ強化版）"""
        try:
            post_image = self.image_dir / "threads_post_button.png"
            if not post_image.exists():
                self.logger.error(f"❌ 画像ファイルが存在しません: {post_image}")
                return False
                        
            for attempt in range(3):
                try:
                    location = pyautogui.locateOnScreen(str(post_image), confidence=0.95)
                    if location:
                        center = pyautogui.center(location)
                        pyautogui.click(center.x, center.y)
                        time.sleep(5)
                        return True
                    else:
                        self.logger.warning(f"⚠️ 試行{attempt + 1}: 投稿ボタンが見つかりません")
                except pyautogui.ImageNotFoundException:
                    self.logger.warning(f"⚠️ 試行{attempt + 1}: ImageNotFoundException")
                
                if attempt < 2:
                    self.logger.info("⏳ 2秒待機して再試行...")
                    time.sleep(2)
            
            self.logger.error("❌ 3回の試行すべて失敗")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ 投稿ボタン認識エラー: {str(e)}")
            import traceback
            self.logger.error(f"詳細: {traceback.format_exc()}")
            return False