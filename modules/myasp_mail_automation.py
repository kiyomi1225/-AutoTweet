# modules/myasp_mail_automation.py - MyASPメルマガ自動登録
import time
import pyautogui
import pyperclip
from pathlib import Path
from typing import List, Dict, Any
import subprocess
import shutil
from datetime import datetime
from tkinter import messagebox
import tkinter as tk

try:
    from .logger_setup import setup_module_logger
except ImportError:
    import sys
    sys.path.append('.')
    from modules.logger_setup import setup_module_logger

class MyASPMailAutomation:
    def __init__(self):
        """MyASPメルマガ自動登録クラス"""
        self.logger = setup_module_logger("MyASPMailAutomation")
        
        # 基本パス設定
        self.base_data_path = Path("C:/Users/shiki/AutoTweet/data")
        self.chrome_profile = "コンテンツ作成用プロファイル"
        
        # 画像認識設定
        self.image_dir = Path("images")
        self.confidence = 0.95
        
        # PyAutoGUI設定
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 1

        # tkinter root作成（msgbox用）
        self.root = tk.Tk()
        self.root.withdraw()
        
        self.logger.info("MyASPメルマガ自動登録を初期化しました")
    
    def get_available_accounts(self) -> Dict[str, int]:
        """7ファイル揃っているアカウントのみ取得"""
        available_accounts = {}
        
        if not self.base_data_path.exists():
            self.logger.warning(f"データフォルダが存在しません: {self.base_data_path}")
            return available_accounts
        
        for folder in self.base_data_path.iterdir():
            if folder.is_dir() and folder.name.startswith("acc"):
                mail_folder = folder / "デイリーメルマガ"
                
                if mail_folder.exists():
                    # 必要なファイルをチェック
                    file_count = 0
                    for i in range(1, 8):
                        mail_file = mail_folder / f"デイリーメルマガ{i}.txt"
                        if mail_file.exists():
                            file_count += 1
                    
                    # 7ファイル揃っているアカウントのみ追加
                    if file_count == 7:
                        available_accounts[folder.name] = file_count
                    else:
                        self.logger.debug(f"❌ {folder.name}: {file_count}/7ファイル（不足）")
        return available_accounts
    
    def run_automation(self, selected_accounts: List[str]) -> Dict[str, Any]:
        """メイン自動化実行"""
        results = {
            "total": len(selected_accounts),
            "success": 0,
            "failed": 0,
            "details": {}
        }
        
        try:
            self.logger.info(f"MyASPメルマガ登録開始: {len(selected_accounts)}アカウント")
            
            for account_id in selected_accounts:
                self.logger.info(f"\n{'='*60}")
                self.logger.info(f"📧 {account_id} 処理開始")
                self.logger.info(f"{'='*60}")
                
                account_result = self._process_account(account_id)
                results["details"][account_id] = account_result
                
                if account_result["success"]:
                    results["success"] += 1
                    self.logger.info(f"✅ {account_id} 完了: {account_result['registered']}/7件登録")
                else:
                    results["failed"] += 1
                    self.logger.error(f"❌ {account_id} 失敗: {account_result.get('error', '不明なエラー')}")
                
                # 次のアカウントまで待機
                if selected_accounts.index(account_id) < len(selected_accounts) - 1:
                    self.logger.info("⏳ 次のアカウントまで10秒待機...")
                    time.sleep(10)
            
            self._show_summary(results)
            return results
            
        except Exception as e:
            self.logger.error(f"自動化エラー: {str(e)}")
            results["error"] = str(e)
            return results
    
    def _process_account(self, account_id: str) -> Dict[str, Any]:
        """単一アカウント処理"""
        result = {
            "success": False,
            "registered": 0,
            "failed_files": []
        }
        
        try:
            # URLファイル確認
            url_config_path = self.base_data_path / account_id / "url_config.txt"
            if not url_config_path.exists():
                raise Exception(f"url_config.txtが見つかりません")
            
            # URL読み込み（2行目を取得）
            with open(url_config_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if len(lines) < 2:
                    raise Exception("url_config.txtに2行目（MyASP URL）がありません")
                myasp_url = lines[1].strip()
                
                # 3行目のnote URL取得
                note_url = ""
                if len(lines) >= 3:
                    note_url = lines[2].strip()
                else:
                    self.logger.warning("url_config.txtに3行目（note URL）がありません")
            
            # Chrome起動
            if not self._start_chrome(myasp_url):
                raise Exception("Chrome起動失敗")
            
            # ブラウザ準備
            self._prepare_browser()
            
            # メルマガ登録ループ
            mail_folder = self.base_data_path / account_id / "デイリーメルマガ"
            
            for day in range(1, 8):
                mail_file = mail_folder / f"デイリーメルマガ{day}.txt"
                processed_file = mail_folder / f"デイリーメルマガ{day}_マイスピー登録済み.txt"
                
                # 既に処理済みの場合スキップ
                if processed_file.exists():
                    self.logger.info(f"⏭️ デイリーメルマガ{day}: 既に登録済み")
                    result["registered"] += 1
                    continue
                
                if not mail_file.exists():
                    self.logger.error(f"❌ デイリーメルマガ{day}.txtが見つかりません")
                    result["failed_files"].append(f"デイリーメルマガ{day}.txt")
                    continue
                
                # メルマガ登録実行
                self.logger.info(f"📝 デイリーメルマガ{day} 登録開始")
                
                if self._register_single_mail(mail_file, day, note_url):
                    # 成功時：ファイル名変更
                    shutil.move(str(mail_file), str(processed_file))
                    result["registered"] += 1
                    self.logger.info(f"✅ デイリーメルマガ{day} 登録完了")
                else:
                    result["failed_files"].append(f"デイリーメルマガ{day}.txt")
                    self.logger.error(f"❌ デイリーメルマガ{day} 登録失敗")
                    break  # （失敗時にループから抜ける）

                # 次の登録まで待機
                if day < 7:
                    time.sleep(5)
            
            # 表示倍率を100%に戻す
            self._reset_zoom()
            
            # Chrome終了
            self._close_chrome()
            
            result["success"] = (result["registered"] == 7)
            return result
            
        except Exception as e:
            self.logger.error(f"アカウント処理エラー: {str(e)}")
            result["error"] = str(e)
            self._close_chrome()
            return result
    
    def _start_chrome(self, url: str) -> bool:
        """Chrome起動"""
        try:
            cmd = [
                "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
                f"--user-data-dir=C:\\Users\\shiki\\AppData\\Local\\Google\\Chrome\\User Data",
                f"--profile-directory={self.chrome_profile}",
                "--new-window",
                url
            ]
            
            subprocess.Popen(cmd)
            time.sleep(10)  # 起動待機
            
            self.logger.info(f"Chrome起動完了: {self.chrome_profile}")
            return True
            
        except Exception as e:
            self.logger.error(f"Chrome起動エラー: {str(e)}")
            return False
    
    def _prepare_browser(self):
        """ブラウザ準備（最大化・ズーム調整）"""
        try:
            # ウィンドウ最大化
            pyautogui.hotkey('alt', 'space')
            time.sleep(2)
            pyautogui.press('x')
            time.sleep(3)
            self.logger.info("ウィンドウ最大化完了")

            # 表示倍率を100%にする
            self._reset_zoom()
            # 表示倍率を67%に（Ctrl+-を4回）
            self.logger.info("表示倍率を67%に変更中...")
            for i in range(4):
                pyautogui.hotkey('ctrl', '-')
                time.sleep(5)
            self.logger.info("表示倍率67%設定完了")
            
        except Exception as e:
            self.logger.warning(f"ブラウザ準備エラー: {str(e)}")
    
    def _register_single_mail(self, mail_file: Path, day_number: int, note_url: str) -> bool:
        """単一メルマガ登録"""
        try:
            # メルマガ内容読み込み
            with open(mail_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            if not lines:
                self.logger.error("メルマガファイルが空です")
                return False
            
            subject = lines[0].strip()  # 1行目：件名
            body_lines = [line.rstrip() for line in lines[1:]]  # 2行目以降：本文
            body = '\n'.join(body_lines)
            
            # 定型文追加
            footer = f"\n\nnoteはこちら↓\n{note_url}\n\n今後の案内が不要な方はこちらから配信停止できます。\n%cancelurl%"
            full_body = body + footer
            
            # 「新規追加」ボタンクリック
            if not self._click_new_add_button():
                return False
            time.sleep(5)
            
            # 「件名」フィールドクリック・入力
            if not self._click_subject_field():
                return False
            time.sleep(2)
            
            pyperclip.copy(subject)
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(2)
            
            # 「今後の案内」フィールドクリック
            if not self._click_future_guide_field():
                return False
            time.sleep(2)
            
            # 全選択
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(2)
            
            # 本文ペースト
            pyperclip.copy(full_body)
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(3)
            
            # 「ページの末尾へ」クリック
            if not self._click_page_bottom_button():
                return False
            time.sleep(3)
            
            # 「短縮URL」クリック
            if not self._click_short_url_button():
                return False
            time.sleep(2)
            
            # 画面スクロール
            pyautogui.scroll(-2000)
            time.sleep(2)

            # 「配信時期」ボタンクリック（追加）
            if not self._click_delivery_timing_button():
                return False
            time.sleep(2)
            # Down→Enter（追加）
            pyautogui.press('down')
            time.sleep(1)
            pyautogui.press('enter')
            time.sleep(1)            
            pyautogui.click()
            time.sleep(1) 

            # 「0日後」フィールドをダブルクリック・入力
            if not self._click_day_field(double_click=True):
                return False
            time.sleep(2)
            
            pyautogui.typewrite(str(day_number))
            time.sleep(2)
            
            # 「0時」フィールドクリック
            if not self._click_hour_field():
                return False
            time.sleep(2)
            
            # スクロールバーをクリックして下へドラッグ
            if not self._drag_scrollbar_down():
                return False
            time.sleep(2)            

            # 「18」をクリック
            if not self._click_18_option():
                return False
            time.sleep(2)
            
            # 「保存する」クリック
            if not self._click_save_button():
                return False
            time.sleep(5)
            
            # 「注意」ダイアログ対応
            self._handle_attention_dialog()
            time.sleep(5)

            return True
            
        except Exception as e:
            self.logger.error(f"メルマガ登録エラー: {str(e)}")
            return False
        
    def _drag_scrollbar_down(self) -> bool:
        """スクロールバーを下へドラッグ"""
        try:
            scrollbar_image = self.image_dir / "myasp_scrollbar.png"
            if not scrollbar_image.exists():
                return False
            
            location = pyautogui.locateOnScreen(str(scrollbar_image), confidence=0.9)
            if location:
                center = pyautogui.center(location)
                # クリックしてホールド、300px下へドラッグ
                pyautogui.moveTo(center.x, center.y)
                pyautogui.dragTo(center.x, center.y + 300, duration=1, button='left')
                self.logger.debug("スクロールバードラッグ完了")
                return True
            return False
        except:
            return False
    
    def _click_new_add_button(self) -> bool:
        """新規追加ボタンクリック"""
        return self._click_image("myasp_new_add_button.png", "新規追加ボタン")
    
    def _click_subject_field(self) -> bool:
        """件名フィールドクリック"""
        return self._click_image("myasp_subject_field.png", "件名フィールド")
    
    def _click_future_guide_field(self) -> bool:
        """今後の案内フィールドクリック"""
        return self._click_image("myasp_future_guide_field.png", "今後の案内フィールド")
    
    def _click_page_bottom_button(self) -> bool:
        """ページの末尾へボタンクリック"""
        return self._click_image("myasp_page_bottom_button.png", "ページの末尾へボタン")
    
    def _click_short_url_button(self) -> bool:
        """短縮URLボタンクリック"""
        return self._click_image("myasp_short_url_button.png", "短縮URLボタン")
    
    def _click_day_field(self, double_click: bool = False) -> bool:
        """日付フィールドクリック"""
        return self._click_image("myasp_day_field.png", "0日後フィールド", double_click=double_click)
    
    def _click_hour_field(self) -> bool:
        """時刻フィールドクリック"""
        return self._click_image("myasp_hour_field.png", "0時フィールド")
    
    def _click_18_option(self) -> bool:
        """18時オプションクリック"""
        return self._click_image("myasp_18_option.png", "18時オプション")
    
    def _click_save_button(self) -> bool:
        """保存ボタンクリック"""
        return self._click_image("myasp_save_button.png", "保存するボタン")
    
    def _click_delivery_timing_button(self) -> bool:
        """配信時期ボタンクリック"""
        return self._click_image("myasp_delivery_timing_button.png", "配信時期ボタン")
    
    def _handle_attention_dialog(self):
        """注意ダイアログ処理"""
        try:
            yes_image = self.image_dir / "myasp_yes_button.png"
            if yes_image.exists():
                location = pyautogui.locateOnScreen(str(yes_image), confidence=0.9)
                if location:
                    self.logger.info("注意ダイアログ検出")
                    # Yesボタンクリック
                    if yes_image.exists():
                        yes_location = pyautogui.locateOnScreen(str(yes_image), confidence=0.9)
                        if yes_location:
                            center = pyautogui.center(yes_location)
                            pyautogui.click(center.x, center.y)
                            self.logger.info("Yesボタンクリック")
                            time.sleep(3)
        except:
            pass  # ダイアログがない場合は無視
    
    def _click_image(self, image_name: str, element_name: str, double_click: bool = False) -> bool:
        """画像認識クリック共通処理"""
        try:
            image_path = self.image_dir / image_name
            if not image_path.exists():
                self.logger.error(f"{image_name} が見つかりません")
                return False
            
            for attempt in range(3):
                try:
                    location = pyautogui.locateOnScreen(str(image_path), confidence=self.confidence)
                    if location:
                        center = pyautogui.center(location)
                        if double_click:
                            pyautogui.doubleClick(center.x, center.y)
                        else:
                            pyautogui.click(center.x, center.y)
                        self.logger.debug(f"{element_name}クリック成功")
                        return True
                except pyautogui.ImageNotFoundException:
                    pass
                
                if attempt < 2:
                    time.sleep(2)
            
            self.logger.warning(f"{element_name}が見つかりません")
            return False
            
        except Exception as e:
            self.logger.error(f"{element_name}クリックエラー: {str(e)}")
            return False
    
    def _reset_zoom(self):
        """表示倍率を100%に戻す"""
        try:
            self.logger.info("表示倍率を100%に戻します")
            pyautogui.hotkey('ctrl', '0')
            time.sleep(5)
        except Exception as e:
            self.logger.warning(f"表示倍率リセットエラー: {str(e)}")
    
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
                        str(close_image), confidence=0.95
                    ))
                    
                    if locations:
                        center = pyautogui.center(locations[0])
                        pyautogui.click(center.x, center.y)
                        self.logger.info("Chrome終了完了")
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
    
    def _show_summary(self, results: Dict[str, Any]):
        """処理結果サマリー表示"""
        self.logger.info("\n" + "="*60)
        self.logger.info("📊 処理結果サマリー")
        self.logger.info("="*60)
        self.logger.info(f"対象アカウント数: {results['total']}")
        self.logger.info(f"✅ 成功: {results['success']}")
        self.logger.info(f"❌ 失敗: {results['failed']}")
        
        for account_id, detail in results["details"].items():
            if detail["success"]:
                self.logger.info(f"  {account_id}: {detail['registered']}/7件登録完了")
            else:
                self.logger.info(f"  {account_id}: 登録失敗 - {detail.get('error', '詳細不明')}")
                if detail.get("failed_files"):
                    self.logger.info(f"    失敗ファイル: {', '.join(detail['failed_files'])}")
        
        self.logger.info("="*60)


# テスト関数
def test_myasp_automation():
    """MyASP自動化のテスト"""
    print("=== MyASP Mail Automation テスト ===")
    
    try:
        automation = MyASPMailAutomation()
        print("✓ 初期化成功")
        
        # 利用可能アカウント確認
        accounts = automation.get_available_accounts()
        print(f"✓ 利用可能アカウント: {accounts}")
        
        print("=== テスト完了 ===")
        return True
        
    except Exception as e:
        print(f"✗ テストエラー: {str(e)}")
        return False

if __name__ == "__main__":
    test_myasp_automation()