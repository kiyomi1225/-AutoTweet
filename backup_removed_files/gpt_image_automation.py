# modules/gpt_image_automation.py - GPT画像認識自動化（PyAutoGUI版）
import time
import cv2
import numpy as np
import pyautogui
import pyperclip
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import csv
from datetime import datetime
import re

try:
    from .logger_setup import setup_module_logger
except ImportError:
    import sys
    sys.path.append('.')
    from modules.logger_setup import setup_module_logger

class GPTImageAutomation:
    def __init__(self, config_manager, vpn_manager=None, chrome_manager=None):
        """GPT画像認識自動化クラス（PyAutoGUI版）"""
        self.config_manager = config_manager
        self.vpn_manager = vpn_manager
        self.chrome_manager = chrome_manager
        self.logger = setup_module_logger("GPTImageAutomation")
        
        # 画像認識設定
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.5
        
        # 設定値
        self.image_dir = Path("images")
        self.image_dir.mkdir(exist_ok=True)
        self.recognition_threshold = 0.8
        self.max_retries = 3
        self.wait_after_input = 45
        self.scroll_duration = 3  # スクロール時間
        
        self.logger.info("GPT画像認識自動化を初期化しました（PyAutoGUI版）")
    
    def run_multiple_accounts_automation(self, target_accounts: List[str], target_count: int = 100) -> bool:
        """複数アカウント分のツイート作成（各アカウントごとにChrome開閉）"""
        try:
            self.logger.info(f"複数アカウント自動化開始")
            self.logger.info(f"対象アカウント: {target_accounts}")
            
            # 事前チェック
            if not self._pre_check():
                return False
            
            # 各アカウントのツイートを順番に作成
            success_count = 0
            total_accounts = len(target_accounts)
            
            for i, target_account_id in enumerate(target_accounts, 1):
                self.logger.info(f"=" * 60)
                self.logger.info(f"🎯 アカウント {i}/{total_accounts}: {target_account_id}")
                self.logger.info(f"=" * 60)
                
                vpn_success = False
                try:
                    # アカウント設定を取得
                    account_config = self.config_manager.get_account_config(target_account_id)
                    if not account_config:
                        self.logger.error(f"アカウント設定が見つかりません: {target_account_id}")
                        continue
                    
                    # アカウント専用のGPTs URLを取得
                    gpt_url = account_config.get("gpt_url", "https://chatgpt.com")
                    self.logger.info(f"📍 GPTs URL: {gpt_url}")
                    
                    # スマートVPN接続（アカウント個別）
                    vpn_success = self._connect_vpn(target_account_id)
                    if not vpn_success:
                        self.logger.error(f"VPN制御に失敗: {target_account_id}")
                        continue
                    
                    # Chrome起動（アカウント個別）
                    if not self._start_chrome_simple(target_account_id, gpt_url):
                        self.logger.error(f"Chrome起動失敗: {target_account_id}")
                        continue
                    
                    # 対象アカウントのCSVファイル準備
                    csv_file = self._prepare_csv_file(target_account_id)
                    
                    # 自動化ループ実行
                    total_collected = self._run_automation_loop_pyautogui(target_account_id, csv_file, target_count)
                    
                    if total_collected > 0:
                        success_count += 1
                        final_count = self._get_current_tweet_count(csv_file)
                        self.logger.info(f"✅ {target_account_id} 完了: {final_count}件取得")
                    else:
                        self.logger.warning(f"⚠️ {target_account_id} ツイート取得失敗")
                    
                    # Chrome終了（アカウント個別）
                    self.logger.info(f"🚪 {target_account_id} Chrome終了中...")
                    self._click_close_button()
                    time.sleep(3)
                    
                except Exception as e:
                    self.logger.error(f"❌ {target_account_id} 処理エラー: {str(e)}")
                
                finally:
                    # アカウント個別のクリーンアップ
                    self._cleanup_account(target_account_id, vpn_success)
                    
                    # 次のアカウントへの準備（最後以外）
                    if i < total_accounts:
                        self.logger.info(f"⏳ 次のアカウント準備中...")
                        time.sleep(5)
            
            self.logger.info(f"🎉 複数アカウント自動化完了: {success_count}/{total_accounts}件成功")
            return success_count > 0
            
        except Exception as e:
            self.logger.error(f"複数アカウント自動化エラー: {str(e)}")
            return False
    
    def _cleanup_account(self, account_id: str, vpn_success: bool):
        """アカウント個別のクリーンアップ"""
        try:
            self.logger.info(f"🧹 {account_id} クリーンアップ開始...")
            
            # Chrome終了
            if self.chrome_manager and self.chrome_manager.is_profile_active(account_id):
                self.chrome_manager.close_chrome_profile(account_id)
                self.logger.info(f"Chrome終了完了: {account_id}")
            
            # スマートVPN切断
            if self.vpn_manager:
                self.logger.info(f"VPN切断実行: {account_id}...")
                disconnect_success = self.vpn_manager.smart_vpn_disconnect()
                if disconnect_success:
                    self.logger.info(f"VPN切断完了: {account_id}")
                else:
                    self.logger.warning(f"VPN切断で問題発生: {account_id}")
            
            self.logger.info(f"🧹 {account_id} クリーンアップ完了")
            
        except Exception as e:
            self.logger.error(f"クリーンアップエラー: {account_id} - {str(e)}")
        """GPT自動化実行（PyAutoGUI版）"""
        vpn_success = False
        try:
            self.logger.info(f"GPT自動化開始: {account_id} -> {gpt_url}")
            
            # 事前チェック
            if not self._pre_check():
                return False
            
            # スマートVPN接続
            vpn_success = self._connect_vpn(account_id)
            if not vpn_success:
                self.logger.error("VPN制御に失敗しました。処理を中断します。")
                return False
            
            # Chrome起動（Seleniumなし）
            if not self._start_chrome_simple(account_id, gpt_url):
                raise Exception("Chrome起動失敗")
            
            # CSVファイル準備
            csv_file = self._prepare_csv_file(account_id)
            
            # 自動化ループ実行（PyAutoGUI版）
            total_collected = self._run_automation_loop_pyautogui(account_id, csv_file, target_count)
            
            # 目標達成時はChromeを閉じる
            final_count = self._count_existing_tweets(csv_file)
            if final_count >= target_count:
                self.logger.info(f"目標達成のためChromeを閉じます: {final_count}/{target_count}件")
                self._click_close_button()
            
            self.logger.info(f"GPT自動化完了: 合計{total_collected}件取得")
            return total_collected > 0
            
        except Exception as e:
            self.logger.error(f"GPT自動化エラー: {str(e)}")
            return False
        
        finally:
            self._cleanup(account_id, vpn_success)
    
    def _pre_check(self) -> bool:
        """事前チェック（必要画像ファイル確認）"""
        try:
            # 必要な画像ファイル確認
            required_images = ["textarea.png", "copy_button.png", "close_button.png"]
            
            for img_name in required_images:
                img_path = self.image_dir / img_name
                if not img_path.exists():
                    self.logger.error(f"必要な画像ファイルが見つかりません: {img_path}")
                    print(f"❌ 画像ファイルが見つかりません: {img_path}")
                    print(f"📋 準備手順:")
                    if img_name == "textarea.png":
                        print(f"1. GPTsページのテキスト入力エリアをスクリーンショット")
                        print(f"2. images/textarea.png として保存")
                    elif img_name == "copy_button.png":
                        print(f"1. GPT応答右上のコピーマークをスクリーンショット")
                        print(f"2. images/copy_button.png として保存")
                    elif img_name == "close_button.png":
                        print(f"1. Chromeウィンドウ右上の閉じるボタン（×）をスクリーンショット")
                        print(f"2. images/close_button.png として保存")
                    return False
                
                img = cv2.imread(str(img_path))
                if img is None:
                    self.logger.error(f"画像ファイルの読み込みに失敗: {img_path}")
                    return False
                
                h, w = img.shape[:2]
                self.logger.info(f"画像ファイル確認: {img_name} ({w}x{h})")
            
            # pyautogui動作確認
            screen_width, screen_height = pyautogui.size()
            self.logger.info(f"画面サイズ: {screen_width}x{screen_height}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"事前チェックエラー: {str(e)}")
            return False
    
    def _connect_vpn(self, account_id: str) -> bool:
        """VPN接続（スマート制御）"""
        if self.vpn_manager:
            self.logger.info("スマートVPN接続中...")
            
            # 現在の状態確認
            status = self.vpn_manager.get_connection_status_detailed()
            self.logger.info(f"現在のIP: {status['current_ip']}")
            self.logger.info(f"通常のIP: {status['target_ip']}")
            self.logger.info(f"VPN必要: {status['vpn_needed']}")
            
            # スマートVPN接続
            vpn_success = self.vpn_manager.smart_vpn_connect(account_id)
            
            if vpn_success:
                final_status = self.vpn_manager.get_connection_status_detailed()
                self.logger.info(f"VPN制御完了: {final_status['current_ip']}")
                return True
            else:
                self.logger.error(f"VPN制御失敗: {account_id}")
                return False
        else:
            self.logger.error("VPN管理が無効です")
            return False
    
    def _start_chrome_simple(self, account_id: str, gpt_url: str) -> bool:
        """Chrome起動（シンプル版・Seleniumなし）"""
        if self.chrome_manager:
            self.logger.info("Chrome起動中...")
            success = self.chrome_manager.start_chrome_profile(account_id, gpt_url)
            
            if success:
                self.logger.info("Chrome起動成功")
                time.sleep(10)  # ページ読み込み待機
                self._maximize_chrome()
                return True
            else:
                self.logger.error("Chrome起動失敗")
                return False
        else:
            self.logger.warning("Chrome管理が無効")
            print("手動でGPTsページを開いて最大化してください")
            input("準備完了後、Enterキーを押してください...")
            return True
    
    def _maximize_chrome(self):
        """Chrome最大化"""
        try:
            time.sleep(2)
            pyautogui.hotkey('alt', 'space')
            time.sleep(0.5)
            pyautogui.press('x')  # 最大化
            time.sleep(1)
            self.logger.info("Chrome最大化完了")
        except Exception as e:
            self.logger.warning(f"Chrome最大化エラー: {str(e)}")
    
    def _prepare_csv_file(self, account_id: str) -> Path:
        """CSVファイル準備（初期化）- アカウント設定対応"""
        # アカウント設定からCSVファイル名を取得
        account_config = self.config_manager.get_account_config(account_id)
        
        if account_config and 'csv_file' in account_config:
            # 設定からCSVファイルパスを取得
            csv_file_path = account_config['csv_file']
            # data/acc1.csv -> Path("data/acc1.csv")
            csv_file = Path(csv_file_path)
        else:
            # フォールバック: デフォルトの命名規則
            csv_file = Path(f"data/{account_id}.csv")
        
        csv_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 既存ファイルを削除してから新規作成
        if csv_file.exists():
            csv_file.unlink()
            self.logger.info(f"既存CSVファイルを削除: {csv_file}")
        
        # ヘッダーのみのCSVファイルを作成
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["id", "text", "used"])
        
        self.logger.info(f"新規CSVファイル作成: {csv_file}")
        return csv_file
    
    def _run_automation_loop_pyautogui(self, account_id: str, csv_file: Path, target_count: int) -> int:
        """自動化ループ実行（PyAutoGUI版・目標達成まで継続）"""
        total_collected = 0
        session_id = int(time.time())
        iteration = 0
        
        # 既存データ確認
        existing_count = self._count_existing_tweets(csv_file)
        self.logger.info(f"既存ツイート数: {existing_count}件")
        
        if existing_count >= target_count:
            self.logger.info(f"既に目標数に達しています: {existing_count}/{target_count}")
            return existing_count
        
        self.logger.info(f"目標件数: {target_count}件まで「n」ループを継続実行します")
        
        # 目標達成まで「n」ループを継続
        while self._get_current_tweet_count(csv_file) < target_count:
            iteration += 1
            current_count = self._get_current_tweet_count(csv_file)
            remaining = target_count - current_count
            
            self.logger.info(f"=== 📥 第{iteration}回「n」送信 (現在: {current_count}/{target_count}件、残り: {remaining}件) ===")
            
            try:
                # Step 1: textarea画像認識・クリック
                if not self._click_textarea():
                    self.logger.warning(f"第{iteration}回: textarea認識失敗、リトライします")
                    time.sleep(5)
                    continue
                
                # Step 2: 「n」入力 + Enter
                self.logger.info("📥 n を送信中...")
                if not self._input_n():
                    self.logger.warning(f"第{iteration}回: 入力失敗、リトライします")
                    time.sleep(5)
                    continue
                
                # Step 3: GPTレスポンス待機（45秒）
                self.logger.info(f"⏳ GPTレスポンス待機中... ({self.wait_after_input}秒)")
                time.sleep(self.wait_after_input)
                
                # Step 4: 大幅スクロール（100倍強化版）
                self._scroll_down()
                
                # Step 5: コピーマーククリック → クリップボード取得
                clipboard_content = self._click_copy_and_get_clipboard()
                
                if not clipboard_content:
                    self.logger.warning("⚠️ 応答が見つかりません。リトライします。")
                    time.sleep(5)
                    continue
                
                # Step 6: ツイート抽出
                tweets = self._parse_tweets(clipboard_content)
                
                if not tweets:
                    self.logger.warning("⚠️ 有効なツイートがありません。")
                    time.sleep(5)
                    continue
                
                # Step 7: ツイート保存
                saved_count = self._save_tweets_to_csv(
                    account_id, tweets, csv_file, session_id, iteration
                )
                
                if saved_count > 0:
                    total_collected += saved_count
                    current_total = self._get_current_tweet_count(csv_file)
                    self.logger.info(f"✅ {saved_count}件保存 → 現在合計: {current_total}件")
                    
                    # 目標達成確認
                    if current_total >= target_count:
                        self.logger.info(f"🎉 {target_count}件以上のツイート案を保存しました！")
                        break
                else:
                    self.logger.warning("⚠️ 保存されたツイートがありません。")
                
                # 次の実行への待機（10秒）
                self.logger.info("⏳ 次の実行まで10秒待機...")
                time.sleep(10)
                
            except KeyboardInterrupt:
                self.logger.info("ユーザーによる中断")
                break
            except Exception as e:
                self.logger.error(f"第{iteration}回実行エラー: {str(e)}")
                self.logger.info("⚠️ エラーが発生しました。リトライします。")
                time.sleep(5)
                continue
        
        final_count = self._get_current_tweet_count(csv_file)
        self.logger.info(f"自動化ループ完了: 最終取得数 {final_count}件")
        
        return total_collected
    
    def _get_current_tweet_count(self, csv_file: Path) -> int:
        """現在のツイート数を取得（リアルタイム）"""
        return self._count_existing_tweets(csv_file)
    
    def _click_textarea(self) -> bool:
        """textarea画像認識・クリック"""
        for attempt in range(self.max_retries):
            try:
                self.logger.info(f"textarea画像認識 (試行 {attempt + 1}/{self.max_retries})")
                
                # スクリーンショット取得
                screenshot = pyautogui.screenshot()
                screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
                
                # テンプレート画像読み込み
                template_path = self.image_dir / "textarea.png"
                template = cv2.imread(str(template_path))
                
                if template is None:
                    self.logger.error("textarea.png の読み込み失敗")
                    return False
                
                # テンプレートマッチング
                result = cv2.matchTemplate(screenshot_cv, template, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                
                if max_val >= self.recognition_threshold:
                    template_h, template_w = template.shape[:2]
                    center_x = max_loc[0] + template_w // 2
                    center_y = max_loc[1] + template_h // 2
                    
                    # オフセット調整: 20px右、50px上
                    adjusted_x = center_x + 20
                    adjusted_y = center_y - 50
                    
                    self.logger.info(f"textarea発見: ({center_x}, {center_y}), 信頼度: {max_val:.3f}")
                    self.logger.info(f"クリック位置調整: ({adjusted_x}, {adjusted_y}) [+20px右, -50px上]")
                    
                    # 調整されたクリック実行
                    pyautogui.click(adjusted_x, adjusted_y)
                    time.sleep(1)
                    return True
                
                self.logger.warning(f"textarea認識失敗 (試行 {attempt + 1})")
                time.sleep(2)
                    
            except Exception as e:
                self.logger.error(f"textarea認識エラー (試行 {attempt + 1}): {str(e)}")
        
        return False
    
    def _input_n(self) -> bool:
        """「n」入力 + Enter"""
        try:
            self.logger.info("「n」+ Enter入力中...")
            
            # 入力エリアクリア
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.5)
            
            # 「n」入力
            pyautogui.typewrite("n")
            time.sleep(1)
            
            # Enter送信
            pyautogui.press("enter")
            self.logger.info("「n」+ Enter送信完了")
            return True
                
        except Exception as e:
            self.logger.error(f"入力エラー: {str(e)}")
            return False
    
    def _scroll_down(self):
        """下方向への大幅スクロール（100倍強化版）"""
        try:
            self.logger.info(f"大幅スクロール開始 ({self.scroll_duration}秒)")
            
            # 画面中央を取得
            screen_width, screen_height = pyautogui.size()
            center_x = screen_width // 2
            center_y = screen_height // 2
            
            # 画面中央をクリックしてフォーカス
            pyautogui.click(center_x, center_y)
            time.sleep(0.5)
            
            # 大幅スクロール実行（元の100倍の強度）
            # 元の値: -3 × 6回 = -18
            # 新の値: -300 × 6回 = -1800 (100倍)
            scroll_steps = 6
            scroll_amount = -300  # 元の-3から100倍
            
            self.logger.info(f"大幅スクロール実行: {scroll_amount} × {scroll_steps}回")
            
            for i in range(scroll_steps):
                pyautogui.scroll(scroll_amount)
                self.logger.debug(f"スクロール {i+1}/{scroll_steps}: {scroll_amount}")
                time.sleep(0.5)
            
            # さらに追加の超大幅スクロール
            additional_scroll = -500  # さらに大きく
            additional_steps = 5
            
            self.logger.info(f"追加大幅スクロール: {additional_scroll} × {additional_steps}回")
            
            for i in range(additional_steps):
                pyautogui.scroll(additional_scroll)
                self.logger.debug(f"追加スクロール {i+1}/{additional_steps}: {additional_scroll}")
                time.sleep(0.3)
            
            total_scroll = (scroll_amount * scroll_steps) + (additional_scroll * additional_steps)
            self.logger.info(f"大幅スクロール完了: 総スクロール量 {total_scroll}")
            
        except Exception as e:
            self.logger.error(f"大幅スクロールエラー: {str(e)}")
    
    def _click_copy_and_get_clipboard(self) -> Optional[str]:
        """コピーマーククリック → クリップボード取得"""
        try:
            self.logger.info("コピーマーク画像認識・クリック開始")
            
            # クリップボードをクリア
            pyperclip.copy("")
            time.sleep(0.5)
            
            # コピーマーク検索・クリック
            if not self._click_copy_button():
                self.logger.error("コピーマーククリック失敗")
                return None
            
            # クリップボード取得待機
            time.sleep(2)
            
            # クリップボード内容取得
            clipboard_content = pyperclip.paste()
            
            if clipboard_content and len(clipboard_content.strip()) > 10:
                self.logger.info(f"クリップボード取得成功: {len(clipboard_content)}文字")
                self.logger.debug(f"クリップボード内容（最初の100文字）: {clipboard_content[:100]}...")
                return clipboard_content.strip()
            else:
                self.logger.warning("クリップボード内容が空または短すぎます")
                return None
                
        except Exception as e:
            self.logger.error(f"クリップボード取得エラー: {str(e)}")
            return None
    
    def _click_copy_button(self) -> bool:
        """コピーマーク画像認識・クリック"""
        for attempt in range(self.max_retries):
            try:
                self.logger.info(f"コピーマーク画像認識 (試行 {attempt + 1}/{self.max_retries})")
                
                # スクリーンショット取得
                screenshot = pyautogui.screenshot()
                screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
                
                # テンプレート画像読み込み
                template_path = self.image_dir / "copy_button.png"
                template = cv2.imread(str(template_path))
                
                if template is None:
                    self.logger.error("copy_button.png の読み込み失敗")
                    return False
                
                # テンプレートマッチング（全ての候補を取得）
                result = cv2.matchTemplate(screenshot_cv, template, cv2.TM_CCOEFF_NORMED)
                
                # 閾値を超える全ての位置を取得
                locations = np.where(result >= self.recognition_threshold)
                
                if len(locations[0]) > 0:
                    # 最も信頼度の高い位置を選択
                    max_val = result.max()
                    max_loc = np.unravel_index(result.argmax(), result.shape)
                    max_loc = (max_loc[1], max_loc[0])  # (x, y)に変換
                    
                    template_h, template_w = template.shape[:2]
                    center_x = max_loc[0] + template_w // 2
                    center_y = max_loc[1] + template_h // 2
                    
                    self.logger.info(f"コピーマーク発見: ({center_x}, {center_y}), 信頼度: {max_val:.3f}")
                    
                    # クリック実行
                    pyautogui.click(center_x, center_y)
                    time.sleep(1)
                    return True
                
                self.logger.warning(f"コピーマーク認識失敗 (試行 {attempt + 1})")
                
                # 失敗時は少し上にスクロールして再試行
                if attempt < self.max_retries - 1:
                    pyautogui.scroll(2)  # 上にスクロール
                    time.sleep(2)
                    
            except Exception as e:
                self.logger.error(f"コピーマーク認識エラー (試行 {attempt + 1}): {str(e)}")
        
        return False
    
    def _parse_tweets(self, text: str) -> List[str]:
        """テキストからツイートパース"""
        try:
            if not text or len(text) < 10:
                return []
            
            self.logger.info(f"パース対象テキスト: {len(text)}文字")
            
            tweets = []
            lines = text.split('\n')
            
            # 改行区切りで抽出
            for line in lines:
                line = line.strip()
                
                # 空行をスキップ
                if not line:
                    continue
                
                # 番号付きリストの場合、番号を除去
                line = re.sub(r'^\d+[\.\)]\s*', '', line)
                line = line.strip()
                
                # 基本的な長さチェック
                if not (10 <= len(line) <= 280):
                    continue
                
                # 妥当性チェック
                if self._is_valid_tweet(line):
                    tweets.append(line)
            
            # 重複除去
            unique_tweets = []
            seen = set()
            for tweet in tweets:
                normalized = re.sub(r'\s+', ' ', tweet.strip())
                if normalized not in seen:
                    unique_tweets.append(tweet)
                    seen.add(normalized)
            
            self.logger.info(f"抽出結果: {len(unique_tweets)}件")
            if unique_tweets:
                for i, tweet in enumerate(unique_tweets[:3], 1):
                    self.logger.info(f"  {i}. ({len(tweet)}文字) {tweet}")
            
            return unique_tweets[:20]  # 最大20件
            
        except Exception as e:
            self.logger.error(f"ツイートパースエラー: {str(e)}")
            return []
    
    def _is_valid_tweet(self, line: str) -> bool:
        """ツイートの妥当性チェック"""
        try:
            # 除外パターン
            exclude_patterns = [
                r'追加でツイート',
                r'を入力してください',
                r'^[。、\s\n\-\*]+$',
                r'^\d+[\.。\)\s]*$',
                r'^(以下|上記|条件|要件|テーマ|形式|作成|生成)',
                r'ツイート.*案.*です',
                r'です。$',
                r'^.*について.*してくださ',
                r'^こちら.*ツイート',
                r'^どうぞ',
                r'^n$',
                r'^.*よろしく',
                r'何か.*あれば',
                r'参考.*なれば',
                r'お役.*立て',
                r'ご不明.*点',
                r'^.*いかがでしょうか',
                r'コピーしました',  # コピー完了メッセージ除外
                r'クリップボード',  # クリップボード関連除外
            ]
            
            for pattern in exclude_patterns:
                if re.search(pattern, line):
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"ツイート妥当性チェックエラー: {str(e)}")
            return False
    
    def _save_tweets_to_csv(self, account_id: str, tweets: List[str], csv_file: Path, 
                           session_id: int, iteration: int) -> int:
        """ツイートをCSVに保存（シンプル形式・デバッグ強化版）"""
        try:
            saved_count = 0
            
            self.logger.info(f"=== CSV保存処理開始 ===")
            self.logger.info(f"保存対象ツイート数: {len(tweets)}件")
            self.logger.info(f"CSVファイル: {csv_file}")
            
            # 既存データを読み込み
            existing = []
            if csv_file.exists():
                with open(csv_file, 'r', newline='', encoding='utf-8') as f:
                    existing = list(csv.reader(f))[1:]  # ヘッダーをスキップ
                self.logger.info(f"既存データ件数: {len(existing)}件")
            else:
                self.logger.info("CSVファイルが存在しません")
            
            # 既存ツイートのテキストを抽出（重複チェック用）
            existing_texts = set()
            for row in existing:
                if len(row) >= 2:
                    existing_texts.add(row[1].strip())
            self.logger.info(f"重複チェック用既存テキスト数: {len(existing_texts)}件")
            
            # 新しいツイートを追加
            with open(csv_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                start_id = len(existing) + 1
                self.logger.info(f"開始ID: {start_id}")
                
                for i, tweet in enumerate(tweets):
                    tweet_text = tweet.strip()
                    self.logger.info(f"--- ツイート{i+1}処理中 ---")
                    self.logger.info(f"文字数: {len(tweet_text)}文字")
                    self.logger.info(f"内容: {tweet_text[:100]}...")
                    
                    # 280文字チェック
                    if len(tweet_text) > 280:
                        self.logger.info(f"❌ 280文字超過のためスキップ")
                        continue
                    else:
                        self.logger.info(f"✅ 文字数チェック通過")
                    
                    # 重複チェック
                    if tweet_text in existing_texts:
                        self.logger.info(f"❌ 重複のためスキップ")
                        continue
                    else:
                        self.logger.info(f"✅ 重複チェック通過")
                    
                    # CSVに書き込み
                    row_data = [start_id + saved_count, tweet_text, "False"]
                    writer.writerow(row_data)
                    existing_texts.add(tweet_text)
                    saved_count += 1
                    self.logger.info(f"✅ CSV保存成功: ID={start_id + saved_count - 1}")
            
            self.logger.info(f"=== CSV保存処理完了 ===")
            self.logger.info(f"保存成功件数: {saved_count}件")
            return saved_count
            
        except Exception as e:
            self.logger.error(f"CSV保存エラー: {str(e)}")
            import traceback
            self.logger.error(f"スタックトレース: {traceback.format_exc()}")
            return 0
    def _save_tweets_to_csv(self, account_id: str, tweets: List[str], csv_file: Path, 
                           session_id: int, iteration: int) -> int:
        """ツイートをCSVに保存（140文字以下のみ）"""
        try:
            saved_count = 0
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 既存のツイートを読み込んで重複チェック
            existing_tweets = set()
            if csv_file.exists():
                with open(csv_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        existing_tweets.add(row.get('content', ''))
            
            with open(csv_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                for i, tweet in enumerate(tweets):
                    # 140文字チェック（再確認）
                    if len(tweet) > 140:
                        self.logger.debug(f"140文字超過のためスキップ: {len(tweet)}文字 - {tweet[:50]}...")
                        continue
                    
                    # 重複チェック
                    if tweet in existing_tweets:
                        continue
                    
                    writer.writerow([
                        account_id,
                        tweet,
                        len(tweet),
                        "auto_generated",
                        "gpt_pyautogui_automation",
                        timestamp,
                        f"{session_id}_{iteration}_{i+1}"
                    ])
                    saved_count += 1
                    existing_tweets.add(tweet)
            
            self.logger.info(f"CSV保存完了: {saved_count}件（140文字以下のみ）")
            return saved_count
            
        except Exception as e:
            self.logger.error(f"CSV保存エラー: {str(e)}")
            return 0
    
    def _click_close_button(self) -> bool:
        """画像認識でChromeの閉じるボタンをクリック"""
        try:
            self.logger.info("Chromeの閉じるボタンを画像認識でクリック中...")
            
            # スクリーンショット取得
            screenshot = pyautogui.screenshot()
            screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            # 閉じるボタンの画像読み込み
            close_button_path = self.image_dir / "close_button.png"
            template = cv2.imread(str(close_button_path))
            
            if template is None:
                self.logger.error("close_button.png の読み込み失敗")
                self.logger.warning("手動でChromeを閉じてください")
                return False
            
            # テンプレートマッチング
            result = cv2.matchTemplate(screenshot_cv, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= self.recognition_threshold:
                template_h, template_w = template.shape[:2]
                center_x = max_loc[0] + template_w // 2
                center_y = max_loc[1] + template_h // 2
                
                self.logger.info(f"閉じるボタン発見: ({center_x}, {center_y}), 信頼度: {max_val:.3f}")
                
                # クリック実行
                pyautogui.click(center_x, center_y)
                time.sleep(2)
                self.logger.info("閉じるボタンクリック完了")
                return True
            else:
                self.logger.warning(f"閉じるボタン認識失敗: 信頼度 {max_val:.3f}")
                self.logger.warning("手動でChromeを閉じてください")
                return False
                
        except Exception as e:
            self.logger.error(f"閉じるボタンクリックエラー: {str(e)}")
            self.logger.warning("手動でChromeを閉じてください")
            return False
    def _count_existing_tweets(self, csv_file: Path) -> int:
        """既存ツイート数をカウント（シンプル形式）"""
        try:
            if not csv_file.exists():
                return 0
            
            with open(csv_file, 'r', newline='', encoding='utf-8') as f:
                existing = list(csv.reader(f))[1:]  # ヘッダーをスキップ
                return len(existing)
            
        except Exception as e:
            self.logger.error(f"既存ツイートカウントエラー: {str(e)}")
            return 0
    
    def _cleanup(self, account_id: str, vpn_success: bool):
        """リソースクリーンアップ（シンプル版）"""
        try:
            self.logger.info("クリーンアップ開始...")
            
            # Chrome終了
            if self.chrome_manager and self.chrome_manager.is_profile_active(account_id):
                self.chrome_manager.close_chrome_profile(account_id)
                self.logger.info("Chrome終了完了")
            
            # スマートVPN切断
            if self.vpn_manager:
                self.logger.info("スマートVPN切断実行...")
                disconnect_success = self.vpn_manager.smart_vpn_disconnect()
                if disconnect_success:
                    self.logger.info("スマートVPN切断完了")
                else:
                    self.logger.warning("スマートVPN切断で問題発生")
            
            self.logger.info(f"クリーンアップ完了: {account_id}")
            
        except Exception as e:
            self.logger.error(f"クリーンアップエラー: {str(e)}")


def test_gpt_multiple_accounts_automation():
    """複数アカウント自動化テスト（各アカウントごとにChrome開閉版）"""
    print("=== 複数アカウントGPT自動化テスト（各アカウント個別処理）===")
    
    try:
        import sys
        sys.path.append('.')
        from modules.config_manager import ConfigManager
        from modules.vpn_manager import VPNManager
        from modules.chrome_manager import ChromeManager
        
        config = ConfigManager()
        vpn_manager = VPNManager(config)
        chrome_manager = ChromeManager(config)
        
        automation = GPTImageAutomation(config, vpn_manager, chrome_manager)
        
        print("✅ GPT自動化初期化成功（複数アカウント個別処理版）")
        
        # 利用可能なアカウント取得
        all_accounts = config.get_all_accounts()
        if len(all_accounts) < 1:
            print("❌ 利用可能なアカウントがありません")
            return
        
        print(f"📋 利用可能なアカウント:")
        for i, account_id in enumerate(all_accounts, 1):
            account_config = config.get_account_config(account_id)
            if account_config:
                gpt_url = account_config.get("gpt_url", "未設定")
                vpn_file = account_config.get("vpn_file", "未設定")
                csv_file = account_config.get("csv_file", f"data/{account_id}.csv")
                print(f"  {i}. {account_id}")
                print(f"     📍 GPTs URL: {gpt_url}")
                print(f"     🔒 VPN: {vpn_file}")
                print(f"     📁 CSV: {csv_file}")
            else:
                print(f"  {i}. {account_id} (設定エラー)")
        
        # 対象アカウント選択
        print(f"\n対象アカウントを選択してください（複数可）:")
        target_accounts = []
        
        for account_id in all_accounts:
            account_config = config.get_account_config(account_id)
            if account_config:
                gpt_url = account_config.get("gpt_url", "未設定")
                vpn_file = account_config.get("vpn_file", "未設定")
                csv_file = account_config.get("csv_file", f"data/{account_id}.csv")
                
                print(f"\n📋 {account_id}:")
                print(f"   📍 GPTs URL: {gpt_url}")
                print(f"   🔒 VPN: {vpn_file}")
                print(f"   📁 CSV: {csv_file}")
                
                confirm = input(f"   {account_id} のツイートを作成しますか？ (y/n): ")
                if confirm.lower() == 'y':
                    target_accounts.append(account_id)
            else:
                print(f"\n❌ {account_id}: 設定が見つかりません")
        
        if not target_accounts:
            print("❌ 対象アカウントが選択されていません")
            return
        
        # 目標取得数
        target_count = int(input("\n各アカウントの目標取得数を入力してください (デフォルト:50): ") or "50")
        
        print(f"\n📋 実行設定:")
        print(f"  🎯 対象アカウント: {len(target_accounts)}件")
        for account_id in target_accounts:
            account_config = config.get_account_config(account_id)
            gpt_url = account_config.get("gpt_url", "未設定") if account_config else "未設定"
            print(f"    - {account_id}: {gpt_url}")
        print(f"  📊 各アカウント目標: {target_count}件")
        print(f"  📁 出力ファイル: data/{target_accounts[0]}.csv, data/{target_accounts[1] if len(target_accounts) > 1 else 'xxx'}.csv, ...")
        print(f"  🔄 処理方式: アカウントごとにVPN接続→Chrome起動→ツイート収集→Chrome終了→VPN切断")
        print(f"  📷 必要画像: images/textarea.png, images/copy_button.png, images/close_button.png")
        
        confirm = input(f"\n複数アカウント自動化を実行しますか？ (y/n): ")
        if confirm.lower() != 'y':
            print("🚫 実行キャンセル")
            return
        
        # 実行
        success = automation.run_multiple_accounts_automation(target_accounts, target_count)
        
        if success:
            print("🎉 複数アカウント自動化成功")
            print(f"  📁 結果ファイル:")
            for account_id in target_accounts:
                csv_path = f"data/{account_id}.csv"
                print(f"    - {csv_path}")
        else:
            print("❌ 複数アカウント自動化失敗")
        
        print("\n=== テスト完了 ===")
        
    except Exception as e:
        print(f"❌ テストエラー: {str(e)}")
        import traceback
        traceback.print_exc()


def convert_excel_to_csv():
    """
    既存のExcelファイルをCSVに変換するユーティリティ
    """
    print("=== Excel → CSV 変換ユーティリティ ===")
    
    try:
        import sys
        sys.path.append('.')
        from modules.config_manager import ConfigManager
        
        excel_path = Path("config/account_database.xlsx")
        csv_path = Path("config/account_database.csv")
        
        if excel_path.exists():
            print(f"📁 Excelファイル発見: {excel_path}")
            
            # Excelファイルを読み込み
            import pandas as pd
            df = pd.read_excel(excel_path, sheet_name=0)
            
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
        import csv
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


def test_gpt_image_automation():
    """GPT画像認識自動化テスト（PyAutoGUI版）"""
    print("=== GPT画像認識自動化テスト（PyAutoGUI版）===")
    
    try:
        import sys
        sys.path.append('.')
        from modules.config_manager import ConfigManager
        from modules.vpn_manager import VPNManager
        from modules.chrome_manager import ChromeManager
        
        config = ConfigManager()
        vpn_manager = VPNManager(config)
        chrome_manager = ChromeManager(config)
        
        automation = GPTImageAutomation(config, vpn_manager, chrome_manager)
        
        print("✅ GPT自動化初期化成功（PyAutoGUI版）")
        
        # テスト種別選択
        print("\nオプションを選択してください:")
        print("1. 単一アカウント自動化")
        print("2. 複数アカウント自動化")
        print("3. Excel→CSV変換")
        print("4. サンプルCSV作成")
        
        test_choice = input("選択 (1-4): ")
        
        if test_choice == "3":
            convert_excel_to_csv()
            return
        elif test_choice == "4":
            create_sample_csv()
            return
        elif test_choice == "2":
            test_gpt_multiple_accounts_automation()
            return
        
        # 単一アカウントテスト（既存のロジック）
        accounts = config.get_all_accounts()
        if not accounts:
            print("❌ 利用可能なアカウントがありません")
            print("💡 'python gpt_image_automation.py' を実行してオプション4でサンプルCSVを作成してください")
            return
        
        test_account = accounts[0]
        test_url = input("GPTs URL を入力してください: ").strip()
        target_count = int(input("目標取得数を入力してください (デフォルト:50): ") or "50")
        
        print(f"\n📋 実行設定:")
        print(f"  🆔 アカウント: {test_account}")
        print(f"  🌐 URL: {test_url}")
        print(f"  🎯 目標: {target_count}件")
        print(f"  📷 必要画像: images/textarea.png, images/copy_button.png, images/close_button.png")
        print(f"  🔄 処理フロー: n送信 → 45秒待機 → 大幅スクロール(100倍) → コピーマーククリック → クリップボード取得")
        print(f"  📏 保存条件: 10-140文字のツイートのみ保存")
        print(f"  🔁 継続条件: 目標件数達成まで自動継続")
        print(f"  🚪 終了処理: 目標達成時にChromeを自動で閉じる")
        
        confirm = input("\n実行しますか？ (y/n): ")
        if confirm.lower() != 'y':
            print("🚫 実行キャンセル")
            return
        
        # 実行
        success = automation.run_automation(test_account, test_url, target_count)
        
        if success:
            print("🎉 GPT自動化成功（PyAutoGUI版）")
            print(f"  📁 結果ファイル: data/{test_account}.csv")
        else:
            print("❌ GPT自動化失敗")
        
        print("\n=== テスト完了 ===")
        
    except Exception as e:
        print(f"❌ テストエラー: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_gpt_image_automation()