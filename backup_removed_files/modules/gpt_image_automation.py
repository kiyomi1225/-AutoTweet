# modules/gpt_image_automation.py - GPT画像認識自動化（最終クリーン版）
import time
import pyautogui
import pyperclip
import cv2
import numpy as np
from pathlib import Path
from typing import List, Optional, Dict, Any
import csv
import re

try:
    from .logger_setup import setup_module_logger
except ImportError:
    import sys
    sys.path.append('.')
    from modules.logger_setup import setup_module_logger

class GPTImageAutomation:
    def __init__(self, config_manager, vpn_manager, chrome_manager):
        """
        GPT画像認識自動化クラス（最終クリーン版）
        """
        self.config_manager = config_manager
        self.vpn_manager = vpn_manager
        self.chrome_manager = chrome_manager
        self.logger = setup_module_logger("GPTImageAutomation")
        
        # 設定読み込み
        self.gpt_config = config_manager.get_gpt_config()
        self.images_config = config_manager.get_images_config()
        
        # 画像認識設定
        self.image_dir = Path(self.images_config.get("image_dir", "images"))
        self.confidence = self.images_config.get("confidence", 0.95)
        self.timeout = self.images_config.get("timeout", 10)
        
        # 自動化設定
        self.wait_after_input = self.gpt_config.get("wait_after_input", 60)
        self.recognition_threshold = 0.95  # 95%まで上げて誤認識防止
        self.max_retries = 3
        
        # PyAutoGUI設定
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 1
        
        self.logger.info("GPT画像認識自動化を初期化しました（最終クリーン版）")
    
    def run_multiple_accounts_automation(self, account_ids: List[str], target_count: int = 100) -> bool:
        """
        複数アカウント自動化実行（acc1統一接続版）
        
        Args:
            account_ids: 対象アカウントIDリスト
            target_count: 各アカウントの目標取得数
            
        Returns:
            bool: 全体成功可否
        """
        try:
            self.logger.info(f"複数アカウント自動化開始（統一接続版）: {len(account_ids)}件")
            
            # ==============================================
            # Phase 1: acc1で統一VPN接続
            # ==============================================
            base_account = "acc1"
            self.logger.info(f"基盤接続開始: {base_account}")
            
            # acc1のVPN接続
            self.logger.info(f"VPN接続: {base_account}")
            vpn_success = self.vpn_manager.smart_vpn_connect(base_account)
            
            if vpn_success:
                vpn_info = self.vpn_manager.get_connection_info()
                self.logger.info(f"VPN接続成功: {vpn_info['current_ip']}")
            else:
                self.logger.warning("VPN接続失敗、通常接続で続行")
            
            self.logger.info(f"基盤接続完了: acc1 VPN")
            
            # ==============================================
            # Phase 2: 各アカウントのツイート収集
            # ==============================================
            successful_accounts = []
            failed_accounts = []
            first_account = True  # 最初のアカウント判定
            
            for i, account_id in enumerate(account_ids, 1):
                self.logger.info(f"[{i}/{len(account_ids)}] アカウント処理開始: {account_id}")
                
                try:
                    # アカウント設定取得
                    account_config = self.config_manager.get_account_config(account_id)
                    if not account_config:
                        self.logger.error(f"アカウント設定取得失敗: {account_id}")
                        failed_accounts.append(account_id)
                        continue
                    
                    gpt_url = account_config.get("gpt_url")
                    if not gpt_url:
                        self.logger.error(f"GPT URL未設定: {account_id}")
                        failed_accounts.append(account_id)
                        continue
                    
                    self.logger.info(f"対象GPT URL: {gpt_url}")
                    
                    # Chrome起動/再起動の判定
                    if first_account:
                        # 最初のアカウント: 新規起動
                        self.logger.info(f"Chrome新規起動: {gpt_url}")
                        success = self.chrome_manager.start_chrome_profile(base_account, gpt_url)
                        first_account = False
                    else:
                        # 2回目以降: 新規起動のみ
                        self.logger.info(f"Chrome新規起動: {gpt_url}")
                        success = self.chrome_manager.start_chrome_profile(base_account, gpt_url)
                    
                    if success:
                        self.logger.info(f"Chrome起動成功: {gpt_url}")
                        
                        # 画面準備とページ安定化
                        self._prepare_browser_for_automation()
                        
                        # 該当アカウントのCSVファイル準備
                        csv_file = Path(f"data/{account_id}.csv")
                        self._reset_csv_for_automation(csv_file)
                        
                        # ツイート自動収集実行
                        self.logger.info(f"ツイート収集開始: {account_id} (目標: {target_count}件)")
                        
                        collected_count = self._run_automation_loop_for_account(
                            account_id, csv_file, target_count
                        )
                        
                        if collected_count > 0:
                            self.logger.info(f"ツイート収集完了: {account_id} - {collected_count}件")
                            successful_accounts.append(account_id)
                        else:
                            self.logger.warning(f"ツイート収集失敗: {account_id}")
                            failed_accounts.append(account_id)
                        
                        # 各アカウント処理完了後にChrome閉じる（最後のアカウント以外）
                        if i < len(account_ids):
                            try:
                                self.logger.info(f"アカウント{account_id}処理完了、Chrome画像認識終了")
                                close_success = self._close_chrome_with_image_click()
                                if close_success:
                                    self.logger.info("アカウント処理完了後Chrome画像認識終了成功")
                                else:
                                    self.logger.warning("画像認識終了失敗、プロセス終了でフォールバック")
                                    self.chrome_manager.close_chrome_profile(base_account)
                                
                                # Chrome完全終了待機
                                self.logger.info("アカウント間Chrome終了待機中...")
                                time.sleep(5)
                                
                            except Exception as e:
                                self.logger.error(f"アカウント間Chrome終了エラー: {str(e)}")
                                # フォールバック: プロセス終了
                                try:
                                    self.chrome_manager.close_chrome_profile(base_account)
                                except Exception:
                                    pass
                    else:
                        self.logger.error(f"Chrome起動失敗: {account_id}")
                        failed_accounts.append(account_id)
                
                except Exception as e:
                    self.logger.error(f"アカウント処理エラー: {account_id} - {str(e)}")
                    failed_accounts.append(account_id)
                
                # アカウント間待機（最後のアカウント以外）
                if i < len(account_ids):
                    wait_time = 10
                    self.logger.info(f"次アカウント処理まで{wait_time}秒待機...")
                    time.sleep(wait_time)
            
            # ==============================================
            # Phase 3: クリーンアップ
            # ==============================================
            self.logger.info("統一接続クリーンアップ開始")
            
            try:
                # Chrome終了（画像認識版）
                self.logger.info("Chrome画像認識終了開始")
                close_success = self._close_chrome_with_image_click()
                if close_success:
                    self.logger.info("Chrome画像認識終了完了")
                else:
                    # 画像認識失敗時は従来方法でフォールバック
                    self.logger.warning("画像認識終了失敗、従来方法でフォールバック")
                    self.chrome_manager.close_chrome_profile(base_account)
                    self.logger.info("Chrome従来方法終了完了")
                
                # VPN切断
                if vpn_success:
                    self.vpn_manager.disconnect()
                    self.logger.info("VPN切断完了")
                    
            except Exception as e:
                self.logger.warning(f"クリーンアップエラー: {str(e)}")
            
            # ==============================================
            # Phase 4: 結果報告
            # ==============================================
            total_accounts = len(account_ids)
            success_count = len(successful_accounts)
            failed_count = len(failed_accounts)
            
            self.logger.info(f"複数アカウント自動化完了:")
            self.logger.info(f"  成功: {success_count}/{total_accounts}件")
            self.logger.info(f"  失敗: {failed_count}/{total_accounts}件")
            
            if successful_accounts:
                self.logger.info(f"  成功アカウント: {successful_accounts}")
            if failed_accounts:
                self.logger.warning(f"  失敗アカウント: {failed_accounts}")
            
            return success_count > 0
            
        except Exception as e:
            self.logger.error(f"複数アカウント自動化エラー: {str(e)}")
            import traceback
            self.logger.error(f"スタックトレース: {traceback.format_exc()}")
            return False
    
    def _prepare_browser_for_automation(self):
        """
        自動化前のブラウザ準備（簡素版）
        """
        try:
            self.logger.info("ブラウザ準備開始")
            
            # 1. Chrome起動後の十分な待機
            self.logger.info("Chrome安定化待機中...")
            time.sleep(8)  # 起動完了まで待機
            
            # 2. 簡単な最大化
            self.logger.info("画面最大化実行")
            pyautogui.hotkey('alt', 'space')
            time.sleep(2)  # メニュー表示待機
            pyautogui.press('x')
            time.sleep(3)  # 最大化完了待機
            
            self.logger.info("ブラウザ準備完了")
            
        except Exception as e:
            self.logger.warning(f"ブラウザ準備エラー: {str(e)}")
    
    def _restart_chrome_with_url(self, base_account: str, gpt_url: str) -> bool:
        """
        Chrome再起動で指定URLに移動（安定方式）
        
        Args:
            base_account: 基盤アカウント（acc1）
            gpt_url: 移動先GPT URL
            
        Returns:
            bool: 再起動成功可否
        """
        try:
            self.logger.info(f"Chrome再起動開始: {gpt_url}")
            
            # 現在のChromeを終了
            self.chrome_manager.close_chrome_profile(base_account)
            time.sleep(3)  # 完全終了待機
            
            # 指定URLでChrome再起動
            chrome_success = self.chrome_manager.start_chrome_profile(base_account, gpt_url)
            
            if chrome_success:
                self.logger.info(f"Chrome再起動成功: {gpt_url}")
                # ページ読み込み完了待機
                time.sleep(8)
                return True
            else:
                self.logger.error(f"Chrome再起動失敗: {gpt_url}")
                return False
                
        except Exception as e:
            self.logger.error(f"Chrome再起動エラー: {str(e)}")
            return False
    
    def _run_automation_loop_for_account(self, account_id: str, csv_file: Path, target_count: int) -> int:
        """
        指定アカウント用の自動化ループ実行
        
        Args:
            account_id: アカウントID
            csv_file: 保存先CSVファイル
            target_count: 目標件数
            
        Returns:
            int: 収集したツイート数
        """
        try:
            loop_count = 0
            total_collected = 0
            
            while self._get_current_tweet_count(csv_file) < target_count:
                loop_count += 1
                current_count = self._get_current_tweet_count(csv_file)
                remaining = target_count - current_count
                
                self.logger.info(f"📥 第{loop_count}回「n」送信 ({account_id}: 現在: {current_count}/{target_count}件、残り: {remaining}件)")
                
                # Step 1: textarea認識・クリック
                if not self._click_textarea():
                    self.logger.warning("textarea認識失敗、次回にリトライ")
                    time.sleep(5)
                    continue
                
                # Step 2: 「n」入力・送信
                pyautogui.typewrite("n")
                pyautogui.press('enter')
                
                # Step 3: GPT応答待機
                self.logger.info(f"⏳ GPTレスポンス待機中... ({self.wait_after_input}秒)")
                time.sleep(self.wait_after_input)
                
                # Step 4: 大幅スクロール
                self.logger.info("📜 大幅スクロール開始")
                self._scroll_down()
                
                # Step 5: コピーマーク認識・クリック・クリップボード取得
                self.logger.info("📋 コピーマーク画像認識・クリック開始")
                content = self._click_copy_and_get_clipboard()
                
                if content:
                    self.logger.info(f"✅ クリップボード取得成功: {len(content)}文字")
                                        
                    # Step 6: ツイート抽出・保存
                    saved_count = self._save_tweets_to_csv(content, csv_file)
                    total_collected += saved_count
                    
                    current_total = self._get_current_tweet_count(csv_file)
                    self.logger.info(f"✅ {saved_count}件保存 → 現在合計: {current_total}件")
                    
                    # 目標達成チェック
                    if current_total >= target_count:
                        self.logger.info(f"🎉 目標達成: {current_total}/{target_count}件")
                        
                        break
                else:
                    self.logger.warning("❌ クリップボード取得失敗")
                
                # Step 7: 次実行待機
                self.logger.info("⏳ 次の実行まで10秒待機...")
                time.sleep(10)
                
                # 安全装置（最大50回）
                if loop_count >= 50:
                    self.logger.warning(f"最大試行回数に到達: {loop_count}回")
                    break
            
            final_count = self._get_current_tweet_count(csv_file)
            self.logger.info(f"アカウント処理完了: {account_id} - 最終取得数: {final_count}件")
            
            return total_collected
            
        except Exception as e:
            self.logger.error(f"自動化ループエラー: {account_id} - {str(e)}")
            return 0
    
    def _click_textarea(self) -> bool:
        """GPT入力エリアを認識・クリック（50px上にオフセット）"""
        try:
            textarea_image = self.image_dir / "textarea.png"
            if not textarea_image.exists():
                self.logger.error(f"textarea画像が見つかりません: {textarea_image}")
                return False
            
            for attempt in range(self.max_retries):
                try:
                    location = pyautogui.locateOnScreen(
                        str(textarea_image), 
                        confidence=self.recognition_threshold
                    )
                    
                    if location:
                        center = pyautogui.center(location)
                        # 50px上にオフセット
                        click_x = center.x
                        click_y = center.y #- 50
                        
                        pyautogui.click(click_x, click_y)
                        self.logger.debug(f"textarea クリック成功")
                        time.sleep(1)
                        return True
                        
                except pyautogui.ImageNotFoundException:
                    pass
                
                if attempt < self.max_retries - 1:
                    self.logger.debug(f"textarea認識リトライ: {attempt + 1}/{self.max_retries}")
                    time.sleep(2)
            
            self.logger.warning("textarea認識失敗（全試行終了）")
            return False
            
        except Exception as e:
            self.logger.error(f"textarea認識エラー: {str(e)}")
            return False
    
    def _scroll_down(self):
        """大幅スクロール（100倍強化版）"""
        try:
            # 画面中央をクリック
            screen_width, screen_height = pyautogui.size()
            center_x = screen_width // 2
            center_y = screen_height // 2
            pyautogui.click(center_x, center_y)
            time.sleep(0.5)  # クリック後の安定化
            
            # 基本スクロール（6回）
            for i in range(6):
                pyautogui.scroll(-300)
                time.sleep(0.1)
            
            # 追加大幅スクロール（5回）
            for i in range(5):
                pyautogui.scroll(-500)
                time.sleep(0.2)
            
            # 最終安定化待機
            time.sleep(1)
            
            self.logger.debug("大幅スクロール完了（総量: -4300）")
            
        except Exception as e:
            self.logger.warning(f"スクロールエラー: {str(e)}")
    
    def _click_copy_and_get_clipboard(self) -> Optional[str]:
        """コピーマーク認識・クリック・クリップボード取得"""
        try:
            copy_image = self.image_dir / "copy_button.png"
            if not copy_image.exists():
                self.logger.error(f"copy_button画像が見つかりません: {copy_image}")
                return None
            
            # クリップボードをクリア
            pyperclip.copy("")
            
            # コピーマーク認識・クリック
            for attempt in range(self.max_retries):
                try:
                    locations = list(pyautogui.locateAllOnScreen(
                        str(copy_image), 
                        confidence=self.recognition_threshold
                    ))
                    
                    if locations:
                        # 最初のコピーマークをクリック
                        location = locations[0]
                        center = pyautogui.center(location)
                        pyautogui.click(center.x, center.y)
                        self.logger.debug(f"コピーマーク クリック: ({center.x}, {center.y})")
                        
                        # クリップボード取得待機
                        time.sleep(2)
                        
                        # クリップボード内容取得
                        content = pyperclip.paste()
                        
                        if content and len(content.strip()) > 0:
                            self.logger.debug(f"クリップボード取得成功: {len(content)}文字")
                            return content.strip()
                        else:
                            self.logger.debug(f"クリップボードが空（試行{attempt + 1}）")
                            
                except pyautogui.ImageNotFoundException:
                    pass
                
                if attempt < self.max_retries - 1:
                    self.logger.debug(f"コピーマーク認識リトライ: {attempt + 1}/{self.max_retries}")
                    time.sleep(3)
            
            self.logger.warning("コピーマーク認識失敗（全試行終了）")
            return None
            
        except Exception as e:
            self.logger.error(f"クリップボード取得エラー: {str(e)}")
            return None
    
    def _save_tweets_to_csv(self, content: str, csv_file: Path) -> int:
        """ツイートをCSVに保存（500文字制限・不要文章除外版）"""
        try:
            if not content or len(content.strip()) == 0:
                return 0
            
            # 不要な文章を除外
            content = self._remove_unwanted_text(content)
                        
            # ツイート抽出パターン
            patterns = [
                r'^\d+\.\s*(.+?)(?=\n\d+\.|$)',
                r'^[\-\*]\s*(.+?)(?=\n[\-\*]|$)', 
                r'^(.{10,500})$'
            ]
            
            tweets = []
            lines = content.split('\n')
                        
            for i, line in enumerate(lines):
                line = line.strip()
                if not line:
                    continue
                
                self.logger.debug(f"行{i}: '{line}' (長さ: {len(line)})")
                
                for j, pattern in enumerate(patterns):
                    matches = re.findall(pattern, line, re.MULTILINE | re.DOTALL)
                    if matches:
                        
                        for match in matches:
                            clean_tweet = match.strip()
                            tweet_length = len(clean_tweet)
                                                        
                            # 長さチェック（10-500文字）
                            if 10 <= tweet_length <= 500:
                                tweets.append(clean_tweet)
                            else:
                                self.logger.warning(f"   ❌ 除外: {tweet_length}文字（範囲外: 10-500文字）")
            
            self.logger.info(f"📊 抽出されたツイート総数: {len(tweets)}")
            
            if not tweets:
                self.logger.warning("有効なツイートが見つかりませんでした")
                return 0
            
            # 既存データ読み込み
            existing_tweets = set()
            if csv_file.exists():
                try:
                    with open(csv_file, 'r', encoding='utf-8') as f:
                        reader = csv.reader(f)
                        next(reader, None)  # ヘッダースキップ
                        for row in reader:
                            if len(row) >= 2:
                                existing_tweets.add(row[1])  # text列
                except Exception as e:
                    self.logger.debug(f"既存CSV読み込みエラー: {str(e)}")
            
            # 新規ツイートを追加
            new_tweets = []
            for tweet in tweets:
                if tweet not in existing_tweets:
                    new_tweets.append(tweet)
            
            if new_tweets:
                # CSVに追記
                file_exists = csv_file.exists()
                with open(csv_file, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    
                    # ヘッダー追加（新規ファイルの場合）
                    if not file_exists:
                        writer.writerow(['id', 'text', 'used'])
                    
                    # データ追加
                    existing_count = len(existing_tweets)  # 既存データ数を取得
                    for i, tweet in enumerate(new_tweets):
                        tweet_id = existing_count + i + 1  # 連番ID（1, 2, 3...）
                        writer.writerow([tweet_id, tweet, False])
                
                return len(new_tweets)
            else:
                return 0
                
        except Exception as e:
            self.logger.error(f"CSV保存エラー: {str(e)}")
            return 0
    
    def _remove_unwanted_text(self, content: str) -> str:
        """
        不要な文章を除外
        
        Args:
            content: 元のクリップボード内容
            
        Returns:
            str: クリーンアップされた内容
        """
        try:
            # 除外するパターン
            unwanted_patterns = [
                r'追加でツイート作成を依頼する場合は n を入力してください。',
                r'追加でツイート作成を依頼する場合は.*?を入力してください。',
                r'何か他にお手伝いできることはありますか？',
                r'他にご質問はありますか？',
                r'Copy code',
                r'```.*?```',  # コードブロック
                r'#.*?#',      # ハッシュタグ行
            ]
            
            cleaned_content = content
            for pattern in unwanted_patterns:
                cleaned_content = re.sub(pattern, '', cleaned_content, flags=re.IGNORECASE | re.DOTALL)
            
            # 連続する空行を単一空行に
            cleaned_content = re.sub(r'\n\s*\n', '\n', cleaned_content)
            
            self.logger.debug(f"不要文章除去: {len(content)} → {len(cleaned_content)}文字")
            
            return cleaned_content.strip()
            
        except Exception as e:
            self.logger.warning(f"不要文章除去エラー: {str(e)}")
            return content
    
    def _close_chrome_with_image_click(self) -> bool:
        """
        画像認識でChromeの閉じるボタン（×）をクリック
        
        Returns:
            bool: 閉じる成功可否
        """
        try:
            self.logger.info("🔄 Chrome画像認識クローズ開始")
            
            close_image = self.image_dir / "close_button.png"
            if not close_image.exists():
                self.logger.error(f"close_button画像が見つかりません: {close_image}")
                return False
            
            # 閉じるボタン認識・クリック
            for attempt in range(self.max_retries):
                try:
                    locations = list(pyautogui.locateAllOnScreen(
                        str(close_image), 
                        confidence=self.recognition_threshold
                    ))
                    
                    if locations:
                        # 最初の閉じるボタンをクリック
                        location = locations[0]
                        center = pyautogui.center(location)
                        pyautogui.click(center.x, center.y)
                        self.logger.info(f"✅ Chrome閉じるボタンクリック成功: ({center.x}, {center.y})")
                        
                        # Chrome終了待機
                        time.sleep(3)
                        return True
                        
                except pyautogui.ImageNotFoundException:
                    pass
                
                if attempt < self.max_retries - 1:
                    self.logger.debug(f"閉じるボタン認識リトライ: {attempt + 1}/{self.max_retries}")
                    time.sleep(2)
            
            self.logger.warning("Chrome閉じるボタン認識失敗（全試行終了）")
            return False
            
        except Exception as e:
            self.logger.error(f"Chrome画像認識クローズエラー: {str(e)}")
            return False
    
    def _wait_for_chrome_complete_shutdown(self):
        """
        Chrome完全終了まで待機
        """
        try:
            self.logger.info("Chromeプロセス完全終了確認中...")
            max_wait_time = 15  # 最大15秒待機
            check_interval = 1   # 1秒間隔でチェック
            
            for i in range(max_wait_time):
                # Chromeプロセスの存在確認
                chrome_processes = []
                try:
                    import psutil
                    for proc in psutil.process_iter(['pid', 'name']):
                        if 'chrome' in proc.info['name'].lower():
                            chrome_processes.append(proc.info['pid'])
                except Exception:
                    pass
                
                if not chrome_processes:
                    self.logger.info(f"Chrome完全終了確認: {i+1}秒で完了")
                    return True
                
                self.logger.debug(f"Chrome終了待機中... ({i+1}/{max_wait_time}秒) プロセス残存: {len(chrome_processes)}件")
                time.sleep(check_interval)
            
            self.logger.warning(f"Chrome完全終了確認タイムアウト: {max_wait_time}秒")
            return False
            
        except Exception as e:
            self.logger.warning(f"Chrome終了確認エラー: {str(e)}")
            return False
    
    def _get_current_tweet_count(self, csv_file: Path) -> int:
        """現在のツイート数を取得"""
        try:
            if not csv_file.exists():
                return 0
            
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader, None)  # ヘッダースキップ
                count = sum(1 for row in reader)
                
            return count
            
        except Exception as e:
            self.logger.debug(f"ツイート数取得エラー: {str(e)}")
            return 0
    
    def _reset_csv_for_automation(self, csv_file: Path):
        """
        自動化開始前にCSVを初期化
        
        Args:
            csv_file: 対象CSVファイル
        """
        try:
            # 既存データのバックアップ作成
            if csv_file.exists():
                backup_dir = csv_file.parent / "backup"
                backup_dir.mkdir(exist_ok=True)
                
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                backup_filename = f"{csv_file.stem}_before_automation_{timestamp}.csv"
                backup_path = backup_dir / backup_filename
                
                import shutil
                shutil.copy2(csv_file, backup_path)
                self.logger.info(f"既存データバックアップ作成: {backup_path}")
            
            # CSVファイルを初期化（空の状態）
            csv_file.parent.mkdir(parents=True, exist_ok=True)
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['id', 'text', 'used'])
            
            self.logger.info(f"CSV初期化完了: {csv_file}")
                
        except Exception as e:
            self.logger.error(f"CSV初期化エラー: {str(e)}")
            # エラー時は既存ファイル確保にフォールバック
            self._ensure_csv_file(csv_file)
    
    def _ensure_csv_file(self, csv_file: Path):
        """CSVファイルの存在を確保"""
        try:
            if not csv_file.exists():
                csv_file.parent.mkdir(parents=True, exist_ok=True)
                with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['id', 'text', 'used'])
                self.logger.debug(f"新規CSVファイル作成: {csv_file}")
                
        except Exception as e:
            self.logger.error(f"CSVファイル作成エラー: {str(e)}")
    
    # 従来の単一アカウント用メソッドは維持
    def run_automation(self, account_id: str, gpt_url: str, target_count: int = 100) -> bool:
        """
        単一アカウント自動化実行（従来互換）
        """
        return self.run_multiple_accounts_automation([account_id], target_count)


# テスト関数
def test_gpt_automation():
    """GPT自動化のテスト"""
    print("=== GPT Image Automation テスト開始 ===")
    
    try:
        from modules.config_manager import ConfigManager
        from modules.vpn_manager import VPNManager
        from modules.chrome_manager import ChromeManager
        
        config = ConfigManager()
        vpn_manager = VPNManager(config)
        chrome_manager = ChromeManager(config)
        
        gpt_automation = GPTImageAutomation(config, vpn_manager, chrome_manager)
        print("✓ GPT自動化初期化成功")
        
        # 画像ファイル確認
        required_images = ["textarea.png", "copy_button.png", "close_button.png"]
        for img_name in required_images:
            img_path = Path(f"images/{img_name}")
            if img_path.exists():
                print(f"✓ 画像ファイル確認: {img_name}")
            else:
                print(f"❌ 画像ファイル未発見: {img_name}")
        
        # アカウント確認
        accounts = config.get_all_accounts()
        print(f"✓ 利用可能アカウント: {accounts}")
        
        print("=== GPT Image Automation テスト完了 ===")
        print("注意: 実際の自動化テストは画像ファイル準備後に実行してください")
        return True
        
    except Exception as e:
        print(f"✗ テストエラー: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_gpt_automation()