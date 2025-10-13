# modules/gpt_image_automation.py - GPT画像認識自動化（ローカル版）
import time
import pyautogui
import pyperclip
from pathlib import Path
from typing import List, Optional
import csv
import re
import json
import shutil
from datetime import datetime

try:
    from .logger_setup import setup_module_logger
except ImportError:
    import sys
    sys.path.append('.')
    from modules.logger_setup import setup_module_logger

class GPTImageAutomation:
    def __init__(self):
        """GPT画像認識自動化クラス（ローカル版）"""
        self.logger = setup_module_logger("GPTImageAutomation")
        
        # 設定読み込み
        self.config = self._load_config()
        
        # 基本パス設定
        self.base_data_path = Path("C:/Users/shiki/AutoTweet/data")
        self.chrome_profile = self.config.get("chrome_profile", "コンテンツ作成用プロファイル")
        
        # GPT自動化設定
        self.gpt_config = self.config.get("gpt_automation", {})
        self.default_wait_time = self.gpt_config.get("default_wait_time", 70)
        self.default_target_count = self.gpt_config.get("default_target_count", 100)
        self.confidence = self.gpt_config.get("confidence", 0.95)
        
        # 画像認識設定
        self.image_dir = Path("images")
        
        # PyAutoGUI設定
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 1
        
        self.logger.info("GPT画像認識自動化（ローカル版）を初期化しました")
    
    def _load_config(self):
        """設定ファイル読み込み"""
        config_path = Path("config/content_creation_config.json")
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # デフォルト設定作成
            default_config = {
                "chrome_profile": "コンテンツ作成用プロファイル",
                "gpt_automation": {
                    "default_wait_time": 70,
                    "default_target_count": 100,
                    "confidence": 0.95
                }
            }
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            return default_config
    
    def get_available_accounts(self) -> List[str]:
        """利用可能なアカウント（フォルダ）を取得"""
        accounts = []
        
        if not self.base_data_path.exists():
            self.logger.warning(f"データフォルダが存在しません: {self.base_data_path}")
            return accounts
        
        for folder in self.base_data_path.iterdir():
            if folder.is_dir() and folder.name.startswith("acc"):
                # URL_Config.txtの存在確認
                url_config = folder / "url_config.txt"
                if url_config.exists():
                    accounts.append(folder.name)
                    self.logger.debug(f"アカウント検出: {folder.name}")
                else:
                    self.logger.debug(f"url_config.txt未設定: {folder.name}")
        
        return sorted(accounts)
    
    def _get_account_url(self, account_id: str) -> Optional[str]:
        """アカウントのGPT URLを取得（1行目のみ）"""
        url_config_path = self.base_data_path / account_id / "URL_Config.txt"
        
        if not url_config_path.exists():
            self.logger.error(f"URL_Config.txtが見つかりません: {account_id}")
            return None
        
        try:
            with open(url_config_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if lines and len(lines) >= 1:
                    # 1行目を使用（GPT用URL）
                    url = lines[0].strip()
                    if url:
                        self.logger.info(f"{account_id}: URL設定確認OK（1行目）")
                        return url
                    else:
                        self.logger.error(f"URL_Config.txtの1行目が空です: {account_id}")
                        return None
                else:
                    self.logger.error(f"URL_Config.txtが空です: {account_id}")
                    return None
        except Exception as e:
            self.logger.error(f"URL読み込みエラー: {str(e)}")
            return None
    
    def _backup_existing_csv(self, account_id: str):
        """既存のtweets.csvをバックアップ"""
        csv_path = self.base_data_path / account_id / "tweets.csv"
        
        if csv_path.exists():
            backup_dir = self.base_data_path / account_id / "backup"
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # タイムスタンプ付きファイル名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = backup_dir / f"tweets_{timestamp}.csv"
            
            shutil.move(str(csv_path), str(backup_path))
            self.logger.info(f"既存CSVをバックアップ: {backup_path.name}")
    
    def run_automation(self, selected_accounts: List[str], wait_time: int = None, target_count: int = None) -> bool:
        """メイン自動化実行"""
        try:
            wait_time = wait_time or self.default_wait_time
            target_count = target_count or self.default_target_count
            
            successful_accounts = []
            failed_accounts = []
            
            for i, account_id in enumerate(selected_accounts, 1):
                self.logger.info(f"{'='*60}")
                self.logger.info(f"[{i}/{len(selected_accounts)}] {account_id} 処理開始")
                self.logger.info(f"{'='*60}")
                
                try:
                    # URL取得
                    gpt_url = self._get_account_url(account_id)
                    if not gpt_url:
                        failed_accounts.append(account_id)
                        continue
                    
                    # AI種別判定
                    ai_type = self._detect_ai_type(gpt_url)
                    
                    # 既存CSVバックアップ
                    self._backup_existing_csv(account_id)
                    
                    # CSV準備
                    csv_path = self.base_data_path / account_id / "tweets.csv"
                    self._prepare_csv(csv_path)
                    
                    # Chrome起動
                    if not self._start_chrome(gpt_url):
                        failed_accounts.append(account_id)
                        continue
                    
                    # ブラウザ準備
                    self._prepare_browser()
                    
                    # ツイート収集
                    collected_count = self._run_collection_loop(
                        account_id, csv_path, ai_type, target_count, wait_time
                    )
                    
                    # Chrome終了
                    self._close_chrome()
                    
                    if collected_count > 0:
                        successful_accounts.append(account_id)
                    else:
                        self.logger.warning(f"❌ {account_id} 収集失敗")
                        failed_accounts.append(account_id)
                    
                    # 次のアカウントまで待機
                    if i < len(selected_accounts):
                        self.logger.info(f"⏳ 次のアカウントまで10秒待機...")
                        time.sleep(10)
                    
                except Exception as e:
                    self.logger.error(f"アカウント処理エラー: {account_id} - {str(e)}")
                    failed_accounts.append(account_id)
                    self._close_chrome()  # 確実にChrome終了
                        
            return len(successful_accounts) > 0
            
        except Exception as e:
            self.logger.error(f"自動化エラー: {str(e)}")
            return False
    
    def _start_chrome(self, url: str) -> bool:
        """Chrome起動"""
        try:
            import subprocess
            cmd = [
                "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
                f"--user-data-dir=C:\\Users\\shiki\\AppData\\Local\\Google\\Chrome\\User Data",
                f"--profile-directory={self.chrome_profile}",
                "--new-window",
                url
            ]
            
            subprocess.Popen(cmd)
            time.sleep(10)  # 起動待機
            
            return True
            
        except Exception as e:
            self.logger.error(f"Chrome起動エラー: {str(e)}")
            return False
    
    def _prepare_browser(self):
        """ブラウザ準備（最大化）"""
        try:
            pyautogui.hotkey('alt', 'space')
            time.sleep(2)
            pyautogui.press('x')  # 最大化
            time.sleep(3)

        except Exception as e:
            self.logger.warning(f"ブラウザ準備エラー: {str(e)}")
    
    def _prepare_csv(self, csv_path: Path):
        """CSV初期化"""
        try:
            csv_path.parent.mkdir(parents=True, exist_ok=True)
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['id', 'text', 'used'])
            self.logger.info(f"CSV準備完了: {csv_path}")
        except Exception as e:
            self.logger.error(f"CSV準備エラー: {str(e)}")
    
    def _run_collection_loop(self, account_id: str, csv_path: Path, ai_type: str, 
                            target_count: int, wait_time: int) -> int:
        """ツイート収集ループ"""
        try:
            # ========== 初期設定処理（GPT/Claude共通） ==========
            # 1. 初回テキストエリアクリック
            if not self._click_textarea_first(ai_type):
                self.logger.error("初回テキストエリアクリック失敗")
                return 0
            
            # 2. スタート入力
            pyperclip.copy("スタート")
            pyautogui.hotkey('ctrl', 'v')
            pyautogui.press('enter')
            self.logger.info("スタート入力完了")
            time.sleep(10)
            
            # 3. ツイートログ.txtをアップロード
            tweet_log_path = self.base_data_path / account_id / "ツイートログ.txt"
            if tweet_log_path.exists():
                if not self._upload_file(account_id, "ツイートログ.txt", ai_type):
                    self.logger.warning("ツイートログ.txtアップロード失敗")
                else:
                    self.logger.info("ツイートログ.txtアップロード完了")
            else:
                self.logger.warning(f"ツイートログ.txt未検出: {tweet_log_path}")
            
            self._click_textarea(ai_type)
            pyautogui.press('enter')
            time.sleep(30)

            loop_count = 0
            
            while self._get_tweet_count(csv_path) < target_count:
                loop_count += 1
                current_count = self._get_tweet_count(csv_path)
                remaining = target_count - current_count
                
                self.logger.info(f"\n第{loop_count}回実行 (現在: {current_count}/{target_count}件, 残り: {remaining}件)")
                
                # textareaクリック
                if not self._click_textarea(ai_type):
                    self.logger.warning("textareaクリック失敗、リトライ...")
                    time.sleep(5)
                    continue
                
                # プロンプト送信
                pyautogui.typewrite("n")
                pyautogui.press('enter')
                
                # 応答待機
                self.logger.info(f"⏳ AI応答待機中... ({wait_time}秒)")
                time.sleep(wait_time)
                
                # スクロール
                self._scroll_down()
                
                # コンテンツコピー
                content = self._copy_content(ai_type)
                if content:
                    saved_count = self._save_tweets(content, csv_path)
                    current_total = self._get_tweet_count(csv_path)
                    self.logger.info(f"✅ {saved_count}件保存 → 現在合計: {current_total}件")
                    
                    if current_total >= target_count:
                        self.logger.info(f"🎯 目標達成: {current_total}/{target_count}件")
                        break
                else:
                    self.logger.warning("コンテンツ取得失敗")
                
                # 次実行待機
                time.sleep(10)
                
                # 安全装置
                if loop_count >= 50:
                    self.logger.warning("最大ループ回数到達")
                    break
            
            return self._get_tweet_count(csv_path)
            
        except Exception as e:
            self.logger.error(f"収集ループエラー: {str(e)}")
            return self._get_tweet_count(csv_path)
    
    def _detect_ai_type(self, url: str) -> str:
        """AI種別判定"""
        if 'chatgpt.com' in url.lower():
            return 'GPT'
        elif 'claude.ai' in url.lower():
            return 'Claude'
        return 'GPT'  # デフォルト
    
    def _click_textarea(self, ai_type: str) -> bool:
        """textareaクリック"""
        try:
            textarea_image = self.image_dir / f"{ai_type}_textarea.png"
            if not textarea_image.exists():
                self.logger.error(f"{ai_type}_textarea.png が見つかりません")
                return False
            
            for attempt in range(3):
                try:
                    if ai_type == "Claude":
                        screen_w, screen_h = pyautogui.size()
                        region = (0, int(screen_h * 0.2), screen_w, int(screen_h * 0.8))
                        location = pyautogui.locateOnScreen(
                            str(textarea_image), confidence=self.confidence, region=region
                        )
                    else:
                        location = pyautogui.locateOnScreen(
                            str(textarea_image), confidence=self.confidence
                        )
                    
                    if location:
                        center = pyautogui.center(location)
                        if ai_type == "Claude":
                            pyautogui.click(center.x, center.y - 30)
                        else:
                            pyautogui.click(center.x, center.y)
                        time.sleep(1)
                        return True
                        
                except pyautogui.ImageNotFoundException:
                    pass
                
                if attempt < 2:
                    time.sleep(2)
            
            return False
            
        except Exception as e:
            self.logger.error(f"textareaクリックエラー: {str(e)}")
            return False
    
    def _scroll_down(self):
        """スクロール実行"""
        try:
            screen_width, screen_height = pyautogui.size()
            pyautogui.click(screen_width // 2, screen_height // 2)
            time.sleep(0.5)
            
            for i in range(6):
                pyautogui.scroll(-300)
                time.sleep(0.1)
            
            for i in range(5):
                pyautogui.scroll(-500)
                time.sleep(0.2)
            
            time.sleep(1)
            
        except Exception as e:
            self.logger.warning(f"スクロールエラー: {str(e)}")
    
    def _copy_content(self, ai_type: str) -> Optional[str]:
        """コンテンツコピー"""
        try:
            copy_image = self.image_dir / f"{ai_type}_copy_button.png"
            if not copy_image.exists():
                self.logger.error(f"{ai_type}_copy_button.png が見つかりません")
                return None
            
            pyperclip.copy("")  # クリップボードクリア
            
            for attempt in range(3):
                try:
                    locations = list(pyautogui.locateAllOnScreen(
                        str(copy_image), confidence=self.confidence
                    ))
                    
                    if locations:
                        center = pyautogui.center(locations[0])
                        pyautogui.click(center.x, center.y)
                        time.sleep(2)
                        
                        content = pyperclip.paste()
                        if content and len(content.strip()) > 0:
                            self.logger.info(f"📋 クリップボード取得成功: {len(content)}文字")
                            return content.strip()
                        
                except pyautogui.ImageNotFoundException:
                    pass
                
                if attempt < 2:
                    time.sleep(3)
            
            return None
            
        except Exception as e:
            self.logger.error(f"コピーエラー: {str(e)}")
            return None
    
    def _save_tweets(self, content: str, csv_path: Path) -> int:
        """ツイート保存（行単位処理版）"""
        try:
            if not content:
                return 0
            
            # 既存ツイート取得（重複チェック用）
            existing_tweets = set()
            if csv_path.exists():
                with open(csv_path, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    next(reader, None)  # ヘッダースキップ
                    for row in reader:
                        if len(row) >= 2:
                            existing_tweets.add(row[1])
            
            # 行単位で処理
            lines = content.split('\n')
            tweets = []
            
            for line in lines:
                line = line.strip()
                
                # 空行スキップ
                if not line:
                    continue
                
                # 不要な行を個別にチェック（削除対象）
                if self._is_unwanted_line(line):
                    continue
                
                # 番号付きリストの処理
                match = re.match(r'^\d+\.\s*(.+)', line)
                if match:
                    tweet_text = match.group(1).strip()
                else:
                    tweet_text = line
                
                # 有効なツイートかチェック
                if tweet_text and tweet_text not in existing_tweets:
                    tweets.append(tweet_text)
            
            # 新規ツイートを保存
            if tweets:
                with open(csv_path, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    existing_count = len(existing_tweets)
                    for i, tweet in enumerate(tweets):
                        tweet_id = existing_count + i + 1
                        writer.writerow([tweet_id, tweet, False])
                
                return len(tweets)
            
            return 0
            
        except Exception as e:
            self.logger.error(f"保存エラー: {str(e)}")
            return 0
        
    def _is_unwanted_line(self, line: str) -> bool:
        """不要な行かどうか判定"""
        unwanted_keywords = [
            '▶ 出力後の案内',
            '入力してください',
            '```'
        ]
        
        # いずれかのキーワードを含む場合はTrue（削除対象）
        for keyword in unwanted_keywords:
            if keyword in line:
                return True
        
        # 'n'を含む指示文の判定（ただし通常の文章は除外）
        if any(x in line for x in ['`n`', "'n'", '「n」', '"n"']):
            if '入力' in line or '依頼' in line or '追加' in line:
                return True
        
        return False
    
    def _get_tweet_count(self, csv_path: Path) -> int:
        """現在のツイート数取得"""
        try:
            if not csv_path.exists():
                return 0
            
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader, None)  # ヘッダースキップ
                return sum(1 for row in reader)
                
        except Exception:
            return 0
        
    def _click_textarea_first(self, ai_type: str) -> bool:
        """初回テキストエリアクリック（スタート入力用）"""
        try:
            # AI種別に応じた画像選択
            if ai_type == "Claude":
                # Claude_textarea_First.pngがあればそれを使用
                textarea_image = self.image_dir / "Claude_textarea_First.png"
                if not textarea_image.exists():
                    textarea_image = self.image_dir / "Claude_textarea.png"
            else:  # GPT
                # GPT_textarea_First.pngがあればそれを使用
                textarea_image = self.image_dir / "GPT_textarea_First.png"
                if not textarea_image.exists():
                    textarea_image = self.image_dir / "GPT_textarea.png"
            
            if not textarea_image.exists():
                self.logger.error(f"{ai_type}_textarea画像が見つかりません")
                return False
            
            # AI種別に応じた検索範囲とクリック位置
            if ai_type == "Claude":
                # Claudeは画面下部80%を検索
                screen_w, screen_h = pyautogui.size()
                region = (0, int(screen_h * 0.2), screen_w, int(screen_h * 0.8))
                location = pyautogui.locateOnScreen(
                    str(textarea_image), confidence=self.confidence, region=region
                )
                click_offset_y = 0  # 初回は中心クリック
            else:  # GPT
                # GPTは全画面検索
                location = pyautogui.locateOnScreen(
                    str(textarea_image), confidence=self.confidence
                )
                click_offset_y = 0  # 初回は中心クリック
            
            if location:
                center = pyautogui.center(location)
                pyautogui.click(center.x, center.y + click_offset_y)
                time.sleep(1)
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"初回textareaクリックエラー: {str(e)}")
            return False

    def _upload_file(self, account_id: str, filename: str, ai_type: str) -> bool:
        """ファイルアップロード（GPT/Claude対応）"""
        try:
            # AI種別に応じたtextarea画像選択
            textarea_image = self.image_dir / f"{ai_type}_textarea.png"
            
            if not textarea_image.exists():
                self.logger.error(f"{ai_type}_textarea.png が見つかりません")
                return False
            
            # テキストエリアクリック
            if ai_type == "Claude":
                screen_w, screen_h = pyautogui.size()
                region = (0, int(screen_h * 0.2), screen_w, int(screen_h * 0.8))
                location = pyautogui.locateOnScreen(
                    str(textarea_image), confidence=self.confidence, region=region
                )
            else:  # GPT
                location = pyautogui.locateOnScreen(
                    str(textarea_image), confidence=self.confidence
                )
            
            if location:
                center = pyautogui.center(location)
                pyautogui.click(center.x, center.y)
                time.sleep(1)
            else:
                self.logger.warning("textareaが見つかりません")
            
            # ファイルアップロードメニューを開く
            if ai_type == "Claude":
                # Claude: Down→Enter
                pyautogui.press('down')
                time.sleep(1)
                pyautogui.press('enter')

            else:  # GPT
                # GPT: クリップアイコンをクリックする場合
                clip_image = self.image_dir / "GPT_clip_icon.png"
                if clip_image.exists():
                    clip_location = pyautogui.locateOnScreen(
                        str(clip_image), confidence=self.confidence
                    )
                    if clip_location:
                        clip_center = pyautogui.center(clip_location)
                        pyautogui.click(clip_center.x, clip_center.y)

                    else:
                        # クリップアイコンが見つからない場合もDown→Enter試行
                        pyautogui.press('down')
                        time.sleep(1)
                        pyautogui.press('enter')
                else:
                    # クリップアイコン画像がない場合はDown→Enter
                    pyautogui.press('down')
                    time.sleep(1)
                    pyautogui.press('enter')
            
            time.sleep(3)
            
            # ファイルパス入力
            file_path = f"C:\\Users\\shiki\\AutoTweet\\data\\{account_id}\\{filename}"
            pyperclip.copy(file_path)
            pyautogui.hotkey('ctrl', 'v')
            pyautogui.press('enter')
            time.sleep(3)
            
            return True
            
        except Exception as e:
            self.logger.error(f"ファイルアップロードエラー: {str(e)}")
            return False
    
    def _close_chrome(self) -> bool:
        """Chrome終了"""
        try:
            close_image = self.image_dir / "close_button.png"
            if not close_image.exists():
                self.logger.warning("close_button.png が見つかりません")
                return False
            
            for attempt in range(3):
                try:
                    locations = list(pyautogui.locateAllOnScreen(
                        str(close_image), confidence=self.confidence
                    ))
                    
                    if locations:
                        center = pyautogui.center(locations[0])
                        pyautogui.click(center.x, center.y)
                        self.logger.info("👌Chrome終了")
                        time.sleep(3)
                        return True
                        
                except pyautogui.ImageNotFoundException:
                    pass
                
                if attempt < 2:
                    time.sleep(2)
            
            return False
            
        except Exception as e:
            self.logger.error(f"Chrome終了エラー: {str(e)}")
            return False
        
    def _click_textarea_first(self, ai_type: str) -> bool:
        """初回テキストエリアクリック（スタート入力用）"""
        try:
            # AI種別に応じた画像選択
            if ai_type == "Claude":
                # Claude_textarea_First.pngがあればそれを使用
                textarea_image = self.image_dir / "Claude_textarea_First.png"
                if not textarea_image.exists():
                    textarea_image = self.image_dir / "Claude_textarea.png"
            else:  # GPT
                # GPT_textarea_First.pngがあればそれを使用
                textarea_image = self.image_dir / "GPT_textarea_First.png"
                if not textarea_image.exists():
                    textarea_image = self.image_dir / "GPT_textarea.png"
            
            if not textarea_image.exists():
                self.logger.error(f"{ai_type}_textarea画像が見つかりません")
                return False
            
            # AI種別に応じた検索範囲とクリック位置
            if ai_type == "Claude":
                # Claudeは画面下部80%を検索
                screen_w, screen_h = pyautogui.size()
                region = (0, int(screen_h * 0.2), screen_w, int(screen_h * 0.8))
                location = pyautogui.locateOnScreen(
                    str(textarea_image), confidence=self.confidence, region=region
                )
                click_offset_y = 0  # 初回は中心クリック
            else:  # GPT
                # GPTは全画面検索
                location = pyautogui.locateOnScreen(
                    str(textarea_image), confidence=self.confidence
                )
                click_offset_y = 0  # 初回は中心クリック
            
            if location:
                center = pyautogui.center(location)
                pyautogui.click(center.x, center.y + click_offset_y)
                time.sleep(1)
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"初回textareaクリックエラー: {str(e)}")
            return False

    def _upload_file(self, account_id: str, filename: str, ai_type: str) -> bool:
        """ファイルアップロード（GPT/Claude対応）"""
        try:
            # AI種別に応じたtextarea画像選択
            textarea_image = self.image_dir / f"{ai_type}_textarea.png"
            
            if not textarea_image.exists():
                self.logger.error(f"{ai_type}_textarea.png が見つかりません")
                return False
            
            # テキストエリアクリック
            if ai_type == "Claude":
                screen_w, screen_h = pyautogui.size()
                region = (0, int(screen_h * 0.2), screen_w, int(screen_h * 0.8))
                location = pyautogui.locateOnScreen(
                    str(textarea_image), confidence=self.confidence, region=region
                )
            else:  # GPT
                location = pyautogui.locateOnScreen(
                    str(textarea_image), confidence=self.confidence
                )
            
            if location:
                center = pyautogui.center(location)
                pyautogui.click(center.x, center.y)
                time.sleep(1)
            else:
                self.logger.warning("textareaが見つかりません")
            
            # ファイルアップロードメニューを開く
            if ai_type == "Claude":
                # Claude: Down→Enter
                pyautogui.press('down')
                time.sleep(1)
                pyautogui.press('enter')
            else:  # GPT
                # GPT: クリップアイコンをクリックする場合
                clip_image = self.image_dir / "GPT_clip_icon.png"
                if clip_image.exists():
                    clip_location = pyautogui.locateOnScreen(
                        str(clip_image), confidence=self.confidence
                    )
                    if clip_location:
                        clip_center = pyautogui.center(clip_location)
                        pyautogui.click(clip_center.x, clip_center.y)
                    else:
                        # クリップアイコンが見つからない場合もDown→Enter試行
                        pyautogui.press('down')
                        time.sleep(1)
                        pyautogui.press('enter')
                else:
                    # クリップアイコン画像がない場合はDown→Enter
                    pyautogui.press('down')
                    time.sleep(1)
                    pyautogui.press('enter')
            
            time.sleep(3)
            
            # ファイルパス入力
            file_path = f"C:\\Users\\shiki\\AutoTweet\\data\\{account_id}\\{filename}"
            pyperclip.copy(file_path)
            pyautogui.hotkey('ctrl', 'v')
            pyautogui.press('enter')
            time.sleep(3)
            
            return True
            
        except Exception as e:
            self.logger.error(f"ファイルアップロードエラー: {str(e)}")
            return False

# テスト関数
def test_gpt_automation():
    """GPT自動化のテスト"""
    print("=== GPT Image Automation (ローカル版) テスト開始 ===")
    
    try:
        automation = GPTImageAutomation()
        print("✓ 初期化成功")
        
        # 利用可能アカウント確認
        accounts = automation.get_available_accounts()
        print(f"✓ 利用可能アカウント: {accounts}")
        
        if accounts:
            # URL確認テスト
            test_account = accounts[0]
            url = automation._get_account_url(test_account)
            print(f"✓ {test_account} URL: {url}")
        
        print("=== テスト完了 ===")
        return True
        
    except Exception as e:
        print(f"✗ テストエラー: {str(e)}")
        return False

if __name__ == "__main__":
    test_gpt_automation()