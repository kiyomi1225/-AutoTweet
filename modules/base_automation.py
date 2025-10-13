# modules/base_automation.py - 自動化共通基底クラス
import time
import pyautogui
import pyperclip
from pathlib import Path
from typing import Optional

try:
    from .logger_setup import setup_module_logger
except ImportError:
    import sys
    sys.path.append('.')
    from modules.logger_setup import setup_module_logger

class BaseAutomation:
    """自動化共通基底クラス（全スクリプト共通処理）"""
    
    def __init__(self, module_name: str):
        """初期化"""
        self.logger = setup_module_logger(module_name)
        
        # 画像認識設定
        self.image_dir = Path("images")
        self.confidence = 0.98
        
        # PyAutoGUI設定
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 1
    
    # ==================== AI関連共通処理 ====================
    
    def _detect_ai_type(self, url: str) -> str:
        """AI種別判定（GPT/Claude）"""
        if 'chatgpt.com' in url.lower():
            return 'GPT'
        elif 'claude.ai' in url.lower():
            return 'Claude'
        return 'GPT'
    
    def _click_textarea_first(self, ai_type: str) -> bool:
        """テキストエリアクリック（初回用）"""
        try:
            textarea_image = self.image_dir / f"{ai_type}_textarea_First.png"
            if not textarea_image.exists():
                textarea_image = self.image_dir / f"{ai_type}_textarea.png"
                if not textarea_image.exists():
                    self.logger.error(f"{ai_type}_textarea画像が見つかりません")
                    return False
            
            if ai_type == "Claude":
                screen_w, screen_h = pyautogui.size()
                region = (0, int(screen_h * 0.2), screen_w, int(screen_h * 0.8))
                location = pyautogui.locateOnScreen(str(textarea_image), confidence=self.confidence, region=region)
            else:  # GPT
                location = pyautogui.locateOnScreen(str(textarea_image), confidence=self.confidence)
            
            if location:
                center = pyautogui.center(location)
                pyautogui.click(center.x, center.y)
                self.logger.info(f"テキストエリアクリック完了 ({ai_type})")
                time.sleep(1)
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"テキストエリアクリックエラー: {str(e)}")
            return False
    
    def _click_textarea(self, ai_type: str) -> bool:
        """テキストエリアクリック（通常用）"""
        try:
            textarea_image = self.image_dir / f"{ai_type}_textarea.png"
            if not textarea_image.exists():
                self.logger.error(f"{ai_type}_textarea.png が見つかりません")
                return False
            
            if ai_type == "Claude":
                screen_w, screen_h = pyautogui.size()
                region = (0, int(screen_h * 0.2), screen_w, int(screen_h * 0.8))
                location = pyautogui.locateOnScreen(str(textarea_image), confidence=self.confidence, region=region)
                
                if location:
                    center = pyautogui.center(location)
                    pyautogui.click(center.x, center.y - 30)
                    time.sleep(3)
                    return True
            else:  # GPT
                location = pyautogui.locateOnScreen(str(textarea_image), confidence=self.confidence)
                
                if location:
                    center = pyautogui.center(location)
                    pyautogui.click(center.x, center.y)
                    time.sleep(3)
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"テキストエリアクリックエラー: {str(e)}")
            return False
    
    def _upload_file(self, account_id: str, filename: str, ai_type: str) -> bool:
        """ファイルアップロード（GPT/Claude対応）"""
        try:
            textarea_image = self.image_dir / f"{ai_type}_textarea.png"
            
            if not textarea_image.exists():
                self.logger.error(f"{ai_type}_textarea.png が見つかりません")
                return False
            
            # テキストエリアクリック
            if ai_type == "Claude":
                screen_w, screen_h = pyautogui.size()
                region = (0, int(screen_h * 0.2), screen_w, int(screen_h * 0.8))
                location = pyautogui.locateOnScreen(str(textarea_image), confidence=self.confidence, region=region)
            else:  # GPT
                location = pyautogui.locateOnScreen(str(textarea_image), confidence=self.confidence)
            
            if location:
                center = pyautogui.center(location)
                pyautogui.click(center.x, center.y)
                time.sleep(1)
            else:
                self.logger.warning("textareaが見つかりません")
            
            # ファイルアップロードメニューを開く
            if ai_type == "Claude":
                pyautogui.press('down')
                time.sleep(1)
                pyautogui.press('enter')
            else:  # GPT
                pyautogui.hotkey('ctrl', 'u')
                time.sleep(1)
            
            time.sleep(3)
            
            # ファイルパス入力
            file_path = f"C:\\Users\\shiki\\AutoTweet\\data\\{account_id}\\{filename}"
            pyperclip.copy(file_path)
            pyautogui.hotkey('ctrl', 'v')
            pyautogui.press('enter')
            time.sleep(3)
            
            self.logger.info(f"ファイルアップロード完了: {filename} ({ai_type})")
            return True
            
        except Exception as e:
            self.logger.error(f"ファイルアップロードエラー: {str(e)}")
            return False
    
    def _copy_content(self, ai_type: str) -> str:
        """コピーボタンクリック→内容取得（GPT/Claude対応）"""
        try:
            copy_image = self.image_dir / f"{ai_type}_copy_button.png"
            if not copy_image.exists():
                self.logger.warning(f"{ai_type}_copy_button.png が見つかりません")
                return ""
            
            pyperclip.copy("")  # クリップボードクリア
            
            location = pyautogui.locateOnScreen(str(copy_image), confidence=self.confidence)
            if location:
                center = pyautogui.center(location)
                pyautogui.click(center.x, center.y)
                time.sleep(2)
                
                content = pyperclip.paste()
                return content.strip() if content else ""
            
            return ""
            
        except Exception as e:
            self.logger.error(f"コピーエラー: {str(e)}")
            return ""
    
    # ==================== 汎用処理 ====================
    
    def _scroll_down(self, scroll_amount: int = -1000, scroll_count: int = 11):
        """スクロール（汎用）"""
        try:
            screen_width, screen_height = pyautogui.size()
            pyautogui.click(screen_width // 2, screen_height // 2)
            time.sleep(0.5)
            
            # 前半
            for i in range(6):
                pyautogui.scroll(scroll_amount)
                time.sleep(0.1)
            
            # 後半
            for i in range(scroll_count - 6):
                pyautogui.scroll(scroll_amount)
                time.sleep(0.2)
            
            time.sleep(1)
            
        except Exception as e:
            self.logger.warning(f"スクロールエラー: {str(e)}")
    
    def _close_chrome(self) -> bool:
        """Chrome終了（汎用）"""
        try:
            # OneTabをクリック
            onetab_image = self.image_dir / "OneTab.png"
            if onetab_image.exists():
                try:
                    location = pyautogui.locateOnScreen(str(onetab_image), confidence=self.confidence)
                    if location:
                        center = pyautogui.center(location)
                        pyautogui.click(center.x, center.y)
                        self.logger.info("OneTabクリック成功")
                        time.sleep(2)
                except pyautogui.ImageNotFoundException:
                    self.logger.warning("OneTabが見つかりません")
            
            # Chromeを閉じる
            close_image = self.image_dir / "close_button.png"
            if not close_image.exists():
                self.logger.warning("close_button.png が見つかりません")
                return False
            
            for attempt in range(3):
                try:
                    locations = list(pyautogui.locateAllOnScreen(str(close_image), confidence=self.confidence))
                    if locations:
                        center = pyautogui.center(locations[0])
                        pyautogui.click(center.x, center.y)
                        self.logger.info("Chrome終了成功")
                        time.sleep(3)
                        return True
                        
                except pyautogui.ImageNotFoundException:
                    pass
                
                if attempt < 2:
                    time.sleep(2)
            
            return False
            
        except Exception as e:
            self.logger.error(f"Chrome終了エラー: {e}")
            return False
        
    # ==================== 今後追加する共通処理用スペース ====================
    
    def _wait_for_element(self, image_name: str, ai_type: Optional[str] = None, timeout: int = 30) -> bool:
        """要素が表示されるまで待機
        
        Args:
            image_name: 画像ファイル名（拡張子なし）
            ai_type: AI種別（指定時は {ai_type}_{image_name}.png を探す）
            timeout: タイムアウト秒数
        
        Returns:
            bool: 要素が見つかったらTrue
        """
        try:
            if ai_type:
                image_path = self.image_dir / f"{ai_type}_{image_name}.png"
            else:
                image_path = self.image_dir / f"{image_name}.png"
            
            if not image_path.exists():
                self.logger.error(f"画像が見つかりません: {image_path}")
                return False
            
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    location = pyautogui.locateOnScreen(str(image_path), confidence=self.confidence)
                    if location:
                        self.logger.info(f"要素検出成功: {image_name}")
                        return True
                except pyautogui.ImageNotFoundException:
                    pass
                
                time.sleep(1)
            
            self.logger.warning(f"要素検出タイムアウト: {image_name} ({timeout}秒)")
            return False
            
        except Exception as e:
            self.logger.error(f"要素待機エラー: {str(e)}")
            return False
    
    def _save_screenshot(self, filename: str, region: Optional[tuple] = None):
        """スクリーンショット保存
        
        Args:
            filename: 保存ファイル名（フルパスまたは相対パス）
            region: キャプチャ範囲 (x, y, width, height)
        """
        try:
            screenshot_path = Path(filename)
            screenshot_path.parent.mkdir(parents=True, exist_ok=True)
            
            if region:
                screenshot = pyautogui.screenshot(region=region)
            else:
                screenshot = pyautogui.screenshot()
            
            screenshot.save(str(screenshot_path))
            self.logger.info(f"スクリーンショット保存: {screenshot_path}")
            
        except Exception as e:
            self.logger.error(f"スクリーンショット保存エラー: {str(e)}")
    
    def _check_image_exists(self, image_name: str, ai_type: Optional[str] = None) -> bool:
        """画像ファイル存在確認
        
        Args:
            image_name: 画像ファイル名（拡張子なし）
            ai_type: AI種別（指定時は {ai_type}_{image_name}.png を確認）
        
        Returns:
            bool: ファイルが存在すればTrue
        """
        try:
            if ai_type:
                image_path = self.image_dir / f"{ai_type}_{image_name}.png"
            else:
                image_path = self.image_dir / f"{image_name}.png"
            
            exists = image_path.exists()
            if not exists:
                self.logger.warning(f"画像ファイルが存在しません: {image_path}")
            
            return exists
            
        except Exception as e:
            self.logger.error(f"画像存在確認エラー: {str(e)}")
            return False


# テスト関数
def test_base_automation():
    """基底クラステスト"""
    print("=== BaseAutomation テスト ===")
    
    try:
        automation = BaseAutomation("TestModule")
        print("✓ 初期化成功")
        
        # AI種別判定テスト
        assert automation._detect_ai_type("https://chatgpt.com/g/g-test") == "GPT"
        assert automation._detect_ai_type("https://claude.ai/project/test") == "Claude"
        print("✓ AI種別判定テスト成功")
        
        # 画像存在確認テスト
        automation._check_image_exists("close_button")
        print("✓ 画像存在確認テスト完了")
        
        return True
        
    except Exception as e:
        print(f"✗ テストエラー: {str(e)}")
        return False

if __name__ == "__main__":
    test_base_automation()
