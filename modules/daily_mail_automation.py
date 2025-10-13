# modules/daily_mail_automation.py - デイリーメルマガ自動取得（AIタイプ対応版）
import time
import random
import pyautogui
import pyperclip
from pathlib import Path
import json
import re

try:
    from .logger_setup import setup_module_logger
    from .base_automation import BaseAutomation
except ImportError:
    import sys
    sys.path.append('.')
    from modules.logger_setup import setup_module_logger
    from modules.base_automation import BaseAutomation

class DailyMailAutomation(BaseAutomation):
    def __init__(self, chrome_manager):
        """デイリーメルマガ自動取得クラス（AIタイプ対応版）"""
        super().__init__("DailyMailAutomation")
        self.chrome_manager = chrome_manager
        
        # 設定読み込み
        self.config = self._load_config()
        
        self.logger.info("デイリーメルマガ自動取得を初期化しました（AIタイプ対応版）")
    
    def _load_config(self):
        """設定ファイル読み込み"""
        config_path = Path("config/content_creation_config.json")
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # デフォルト設定作成
            default_config = {
                "daily_mail_ai_url": "https://claude.ai/project/01995cd1-e79f-7485-b9ff-7ed5770bf776",
                "chrome_profile": "コンテンツ作成用プロファイル",
                "wait_time": 45
            }
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            return default_config
    
    def _get_daily_mail_url(self) -> tuple:
        """デイリーメルマガAI URL取得
        
        Returns:
            tuple: (url, ai_type)
        """
        url = self.config.get('daily_mail_ai_url', 'https://claude.ai/project/01995cd1-e79f-7485-b9ff-7ed5770bf776')
        ai_type = self._detect_ai_type(url)
        self.logger.info(f"URL: {url}")
        return url, ai_type
    
    def run_automation(self, account_id: str, wait_time: int = 45) -> bool:
        """メイン自動化実行（AIタイプ対応版）"""
        try:
            # AIタイプ判定（content_creation_config.jsonから）
            url, ai_type = self._get_daily_mail_url()
            self.logger.info(f"🤖 AIタイプ: {ai_type}")
            
            self.logger.info(f"デイリーメルマガ自動取得開始: {account_id}")
            
            # データフォルダパス
            mail_folder = Path(f"C:\\Users\\shiki\\AutoTweet\\data\\{account_id}\\デイリーメルマガ")
            self.logger.info(f"データフォルダ: {mail_folder}")
            
            # 既存ファイル確認
            existing_files = self._check_existing_files(mail_folder)
            self.logger.info(f"既存ファイル: {existing_files}個")
            
            if existing_files >= 7:
                self.logger.info("既に7個のファイルが存在します。処理をスキップ")
                return True
            
            # 必要なファイル数を計算
            needed_count = 7 - existing_files
            self.logger.info(f"必要ファイル数: {needed_count}個")
            
            # 必要ファイル確認
            if not self._check_required_files(account_id):
                return False
            
            # 不足分を生成
            for i in range(needed_count):
                file_number = existing_files + i + 1
                self.logger.info(f"📝 デイリーメルマガ{file_number}.txt 生成開始")
                
                # Chrome起動
                if not self._start_chrome(url):
                    return False
                
                # AI処理実行
                output_file = mail_folder / f"デイリーメルマガ{file_number}.txt"
                success = self._execute_single_mail(account_id, output_file, wait_time, ai_type)
                
                # Chrome終了
                self._close_chrome()
                
                if not success:
                    self.logger.error(f"デイリーメルマガ{file_number}.txt 生成失敗")
                    return False
                                
                # 次のループまで待機
                if i < needed_count - 1:
                    self.logger.info("⏳ 次の生成まで10秒待機...")
                    time.sleep(10)
            
            self.logger.info(f"🎉 全ファイル生成完了: {needed_count}個")
            return True
            
        except Exception as e:
            self.logger.error(f"自動化エラー: {str(e)}")
            return False
        finally:
            self._close_chrome()
    
    def _check_existing_files(self, mail_folder: Path) -> int:
        """既存のデイリーメルマガファイル数を確認"""
        count = 0
        for i in range(1, 8):
            file_path = mail_folder / f"デイリーメルマガ{i}.txt"
            if file_path.exists():
                count += 1
                self.logger.debug(f"存在確認: デイリーメルマガ{i}.txt")
        return count
    
    def _check_required_files(self, account_id: str) -> bool:
        """必要ファイル確認"""
        base_path = Path(f"C:\\Users\\shiki\\AutoTweet\\data\\{account_id}")
        required_files = [
            "キャラクターコンセプト.txt",
            "ターゲット.txt",
            "市場リサーチ.txt"
        ]
        
        for filename in required_files:
            if not (base_path / filename).exists():
                self.logger.error(f"必要ファイルが見つかりません: {base_path / filename}")
                return False
        
        return True
    
    def _start_chrome(self, url: str) -> bool:
        """Chrome起動"""
        try:
            import subprocess
            cmd = [
                "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
                f"--user-data-dir=C:\\Users\\shiki\\AppData\\Local\\Google\\Chrome\\User Data",
                f"--profile-directory={self.config['chrome_profile']}",
                "--new-window",
                url
            ]
            
            subprocess.Popen(cmd)
            time.sleep(10)  # 起動待機
            
            # 全画面表示
            pyautogui.hotkey('alt', 'space')
            time.sleep(3)
            pyautogui.press('x')
            time.sleep(5)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Chrome起動エラー: {str(e)}")
            return False
    
    def _execute_single_mail(self, account_id: str, output_file: Path, wait_time: int, ai_type: str) -> bool:
        """単一メルマガ生成実行（AIタイプ対応版）"""
        try:
            content_parts = []
            
            # # 🆕 AIタイプ別の初期処理
            # if ai_type == "Claude":
            #     # Claude Sonnet4クリック
            #     if not self._click_claude_sonnet4():
            #         return False
            #     time.sleep(3)
                
            #     # Down→EnterでOpus4に切り替え
            #     pyautogui.press('down')
            #     time.sleep(3)
            #     pyautogui.press('enter')
            #     time.sleep(3)
            #     self.logger.info("Opus4切り替え完了")
            # else:
            #     # GPTの場合は特別な準備不要
            #     self.logger.info("GPT使用（モデル選択なし）")
            
            # テキストエリアクリック→「スタート」入力 - BaseAutomationのメソッド使用
            if not self._click_textarea_first(ai_type):
                return False
            time.sleep(3)
            pyperclip.copy("スタート")
            pyautogui.hotkey('ctrl', 'v')
            pyautogui.press('enter')
            time.sleep(15)
            
            # ファイルアップロード（3回） - BaseAutomationのメソッド使用
            upload_files = [
                "キャラクターコンセプト.txt",
                "ターゲット.txt",
                "市場リサーチ.txt"
            ]
            
            for filename in upload_files:
                if not self._upload_file(account_id, filename, ai_type):
                    return False
            
            time.sleep(3)
            
            # テキストエリアクリック→Enter送信 - BaseAutomationのメソッド使用
            if not self._click_textarea(ai_type):
                return False
            pyautogui.press('enter')
            time.sleep(30)
            
            # 1～10のランダム数値入力
            random_num = random.randint(1, 10)
            pyautogui.typewrite(str(random_num))
            pyautogui.press('enter')
            time.sleep(wait_time)
            self.logger.info(f"ランダム数値入力: {random_num}")
            
            # 5章分のコンテンツ収集
            for chapter in range(1, 6):
                
                pyautogui.typewrite("n")
                pyautogui.press('enter')
                time.sleep(wait_time)
                
                # スクロール - BaseAutomationのメソッド使用
                self._scroll_down()
                
                # コピー - BaseAutomationのメソッド使用
                chapter_content = self._copy_content(ai_type)
                if chapter_content:
                    # 最終行削除
                    lines = chapter_content.split('\n')
                    if lines:
                        filtered_lines = lines[:-1] if len(lines) > 1 else lines
                        content_parts.append('\n'.join(filtered_lines))
                        self.logger.info(f"✅ 第{chapter}章 収集完了")
            
            # ファイル保存
            if content_parts:
                self._save_content(content_parts, output_file)
                self.logger.info(f"📁 ファイル保存完了: {output_file.name}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"メルマガ生成エラー: {str(e)}")
            return False
    
    def _click_claude_sonnet4(self) -> bool:
        """Claude Sonnet4ボタンクリック（Claude専用）"""
        try:
            sonnet4_image = self.image_dir / "claude_sonnet4.png"
            if not sonnet4_image.exists():
                self.logger.error("claude_sonnet4.png が見つかりません")
                return False
            
            location = pyautogui.locateOnScreen(str(sonnet4_image), confidence=self.confidence)
            if location:
                center = pyautogui.center(location)
                pyautogui.click(center.x, center.y)
                self.logger.info("Claude Sonnet4クリック成功")
                return True
            else:
                self.logger.error("Claude Sonnet4ボタンが見つかりません")
                return False
                
        except Exception as e:
            self.logger.error(f"Claude Sonnet4クリックエラー: {str(e)}")
            return False
    
    def _save_content(self, content_parts: list, output_file: Path):
        """コンテンツ保存（改行整理版）"""
        cleaned_parts = []
        
        for part in content_parts:
            if part:
                # 連続する改行を単一改行に統一
                cleaned = re.sub(r'\n\s*\n', '\n', part.strip())
                cleaned_parts.append(cleaned)
        
        # 部分間は改行1つで結合
        final_content = '\n'.join(cleaned_parts)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(final_content)


# テスト関数
def test_daily_mail_automation():
    """テスト（AIタイプ対応版）"""
    print("=== Daily Mail Automation テスト (AIタイプ対応版) ===")
    
    try:
        from modules.chrome_manager import ChromeManager
        from modules.config_manager import ConfigManager
        
        config = ConfigManager()
        chrome_manager = ChromeManager(config)
        automation = DailyMailAutomation(chrome_manager)
        
        print("✓ 初期化成功")
        print("\n📋 設定内容:")
        
        url = automation.config.get('daily_mail_ai_url')
        ai_type = automation._detect_ai_type(url)
        
        print(f"  - デフォルトURL: {url}")
        print(f"  - 🤖 AIタイプ: {ai_type}")
        print(f"  - プロファイル: {automation.config['chrome_profile']}")
        print(f"  - デフォルト待機時間: {automation.config['wait_time']}秒")
        
        # AI判定テスト
        test_urls = [
            "https://chatgpt.com/g/g-test",
            "https://claude.ai/project/test"
        ]
        print("\n✓ AI判定テスト:")
        for test_url in test_urls:
            detected = automation._detect_ai_type(test_url)
            print(f"  {test_url} → {detected}")
        
        print("\n✨ 対応機能:")
        print("  - BaseAutomation継承済み")
        print("  - GPT/Claude両対応")
        print("  - content_creation_config.json の daily_mail_ai_url から読み込み")
        print("  - Claude: Sonnet4 → Opus4切り替え")
        print("  - GPT: 直接実行")
        
        print("\n=== テスト完了 ===")
        return True
        
    except Exception as e:
        print(f"✗ テストエラー: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_daily_mail_automation()
