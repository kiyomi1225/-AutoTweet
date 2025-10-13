# modules/frontend_salesletter_automation.py - フロントエンドnoteセールスレター自動取得
import time
import pyautogui
import pyperclip
from pathlib import Path
import json
import glob
import re
import shutil

try:
    from .logger_setup import setup_module_logger
    from .base_automation import BaseAutomation
except ImportError:
    import sys
    sys.path.append('.')
    from modules.logger_setup import setup_module_logger
    from modules.base_automation import BaseAutomation

class FrontendSalesletterAutomation(BaseAutomation):
    def __init__(self, chrome_manager):
        """初期化"""
        super().__init__("FrontendSalesletterAutomation")
        self.chrome_manager = chrome_manager
        self.config = self._load_config()
        
        self.logger.info("フロントエンドnoteセールスレター自動取得を初期化しました")
    
    def _load_config(self):
        """設定ファイル読み込み"""
        config_path = Path("config/content_creation_config.json")
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            self.logger.error("content_creation_config.json が見つかりません")
            return {}
    
    def run_automation(self, account_id: str, wait_time: int = 45) -> bool:
        """メイン自動化実行"""
        try:
            self.logger.info(f"セールスレター自動取得開始: アカウント={account_id}, 待機時間={wait_time}秒")
            
            # AI種別判定
            url = self.config.get('sales_letter_ai_url', '')
            ai_type = self._detect_ai_type(url)
            self.logger.info(f"AI種別: {ai_type}")

            # データフォルダパス
            data_folder = Path(f"C:\\Users\\shiki\\AutoTweet\\data\\{account_id}\\フロントエンドnote")
            self.logger.info(f"データフォルダ: {data_folder}")
            
            # フロントエンドnoteファイル数確認
            note_files = self._get_frontend_note_files(data_folder)
            if not note_files:
                self.logger.error("フロントエンドnoteファイルが見つかりません")
                return False
            
            self.logger.info(f"処理対象ファイル: {len(note_files)}件")
            
            # バックアップフォルダ作成
            backup_folder = data_folder / "backup"
            backup_folder.mkdir(parents=True, exist_ok=True)
            
            # 必要ファイル確認
            if not self._check_required_files(account_id):
                self.logger.error("必要ファイル確認失敗")
                return False
            
            # 各ファイルを処理
            for i, note_file in enumerate(note_files, 1):
                self.logger.info(f"📝 ファイル {i}/{len(note_files)} 処理開始: {note_file.name}")
                
                success = self._process_single_file(account_id, note_file, backup_folder, wait_time, ai_type)
                
                if not success:
                    self.logger.error(f"❌ ファイル処理失敗: {note_file.name}")
                    return False
                
                self.logger.info(f"✅ ファイル {i} 完了: {note_file.name}")
                
                # 次ファイルまで待機
                if i < len(note_files):
                    self.logger.info(f"⏳ 次ファイルまで10秒待機...")
                    time.sleep(10)
            
            self.logger.info(f"🎉 全ファイル処理完了: {len(note_files)}件")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 自動化エラー: {str(e)}")
            return False
        finally:
            self.logger.info("🧹 最終クリーンアップ実行")
            self._close_chrome()
    
    def _get_frontend_note_files(self, data_folder: Path) -> list:
        """フロントエンドnoteファイル一覧を取得（番号順ソート）"""
        try:
            pattern = str(data_folder / "フロントエンドnote*.txt")
            files = glob.glob(pattern)
            
            # セールスレター追記済みファイルは除外
            files = [f for f in files if "セールスレター追記済み" not in f]
            
            # 番号でソート
            def get_number(filepath):
                match = re.search(r'フロントエンドnote(\d+)\.txt', filepath)
                return int(match.group(1)) if match else 0
            
            files.sort(key=get_number)
            
            return [Path(f) for f in files]
            
        except Exception as e:
            self.logger.error(f"ファイル一覧取得エラー: {str(e)}")
            return []
    
    def _check_required_files(self, account_id: str) -> bool:
        """必要ファイル確認"""
        base_path = Path(f"C:\\Users\\shiki\\AutoTweet\\data\\{account_id}")
        required_files = [
            "キャラクターコンセプト.txt",
            "ターゲット.txt", 
            "市場リサーチ.txt"
        ]
        
        missing_files = []
        for filename in required_files:
            if not (base_path / filename).exists():
                missing_files.append(str(base_path / filename))
        
        if missing_files:
            self.logger.error(f"必要ファイルが見つかりません: {missing_files}")
            return False
        
        self.logger.info("必要ファイル確認完了")
        return True
    
    def _process_single_file(self, account_id: str, note_file: Path, backup_folder: Path, 
                            wait_time: int, ai_type: str) -> bool:
        """単一ファイル処理"""
        try:
            self.logger.info(f"=== ファイル処理開始: {note_file.name} ===")
            
            # 1-15行目読み込み
            target_lines = self._read_file_lines(note_file, 1, 15)
            if not target_lines:
                self.logger.error("1-15行目の読み込みに失敗")
                return False
            
            # Chrome起動
            self.logger.info(f"🌐 Chrome起動")
            if not self._start_chrome():
                self.logger.error("Chrome起動失敗")
                return False
            
            # AI処理実行
            collected_content = self._execute_ai_processing(account_id, target_lines, wait_time, ai_type)
            
            # Chrome終了
            self._close_chrome()
            self.logger.info(f"✅ Chrome終了")
            
            if not collected_content:
                self.logger.error("セールスレター収集失敗")
                return False
            
            # ファイル更新処理
            success = self._update_and_backup_file(note_file, backup_folder, collected_content)
            
            self.logger.info(f"=== ファイル処理完了: {note_file.name} ===")
            return success
            
        except Exception as e:
            self.logger.error(f"ファイル処理エラー: {str(e)}")
            return False
    
    def _read_file_lines(self, file_path: Path, start_line: int, end_line: int) -> str:
        """ファイルの指定行を読み込み"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            if len(lines) < end_line:
                self.logger.warning(f"ファイル行数不足: {len(lines)}行 < {end_line}行")
                return '\n'.join([line.rstrip() for line in lines[start_line-1:]])
            
            target_lines = lines[start_line-1:end_line]
            content = '\n'.join([line.rstrip() for line in target_lines])
            
            self.logger.info(f"{start_line}-{end_line}行目読み込み: {len(content)}文字")
            return content
            
        except Exception as e:
            self.logger.error(f"ファイル読み込みエラー: {str(e)}")
            return ""
    
    def _start_chrome(self) -> bool:
        """Chrome起動"""
        try:
            url = self.config['sales_letter_ai_url']
            
            import subprocess
            cmd = [
                "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
                f"--user-data-dir=C:\\Users\\shiki\\AppData\\Local\\Google\\Chrome\\User Data",
                f"--profile-directory={self.config['chrome_profile']}",
                "--new-window",
                url
            ]
            
            subprocess.Popen(cmd)
            time.sleep(10)
            
            # 全画面表示
            pyautogui.hotkey('alt', 'space')
            time.sleep(3)
            pyautogui.press('x')
            time.sleep(5)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Chrome起動エラー: {str(e)}")
            return False
    
    def _execute_ai_processing(self, account_id: str, target_lines: str, wait_time: int, ai_type: str) -> str:
        """AI処理実行"""
        try:
            self.logger.info("🤖 AI処理開始")
            
            # # AIモデル選択
            # if not self._select_ai_model(ai_type):
            #     return ""
            
            # # Claude専用: Opus4切り替え
            # if ai_type == "Claude":
            #     pyautogui.press('down')
            #     time.sleep(3)
            #     pyautogui.press('enter')
            #     time.sleep(3)
            #     self.logger.info("Step 2: Opus4切り替え完了")
            
            # テキストエリアクリック→「スタート」入力
            if not self._click_textarea_first(ai_type):
                return ""
            
            pyperclip.copy("スタート")
            pyautogui.hotkey('ctrl', 'v')
            pyautogui.press('enter')
            time.sleep(20)
            self.logger.info("Step 3: スタート入力完了")
            
            # ファイルアップロード（3回）
            upload_files = [
                "キャラクターコンセプト.txt",
                "ターゲット.txt", 
                "市場リサーチ.txt"
            ]
            
            for filename in upload_files:
                if not self._upload_file(account_id, filename, ai_type):
                    return ""
            
            time.sleep(3)
            
            # テキストエリアクリック→Enter
            if not self._click_textarea(ai_type):
                return ""
            pyautogui.press('enter')
            time.sleep(30)
            
            # 1-15行目をペースト
            if not self._click_textarea(ai_type):
                return ""
            pyperclip.copy(target_lines)
            pyautogui.hotkey('ctrl', 'v')
            pyautogui.press('enter')
            time.sleep(wait_time)
            self.logger.info("1-15行目ペースト完了")
            
            # 7章分のコンテンツ収集
            content_parts = []
            for chapter in range(1, 8):
                self.logger.info(f"📖 第{chapter}章 収集開始")
                
                pyautogui.typewrite("n")
                pyautogui.press('enter')
                time.sleep(wait_time)
                
                # スクロール
                self._scroll_down()
                
                # コピー
                chapter_content = self._copy_content(ai_type)
                if chapter_content:
                    lines = chapter_content.split('\n')
                    if lines:
                        filtered_lines = lines[:-1] if len(lines) > 1 else lines
                        content_parts.append('\n'.join(filtered_lines))
                        self.logger.info(f"✅ 第{chapter}章 収集完了")
            
            # コンテンツ結合
            if content_parts:
                final_content = self._clean_and_join_content(content_parts)
                self.logger.info(f"🎉 セールスレター収集完了: {len(final_content)}文字")
                return final_content
            
            return ""
            
        except Exception as e:
            self.logger.error(f"AI処理エラー: {str(e)}")
            return ""
    
    def _select_ai_model(self, ai_type: str) -> bool:
        """AIモデル選択（GPT/Claude対応）"""
        try:
            if ai_type == "Claude":
                sonnet4_image = self.image_dir / "claude_sonnet4.png"
                if not sonnet4_image.exists():
                    self.logger.error("claude_sonnet4.png が見つかりません")
                    return False
                
                location = pyautogui.locateOnScreen(str(sonnet4_image), confidence=self.confidence)
                if location:
                    center = pyautogui.center(location)
                    pyautogui.click(center.x - 30, center.y)
                    self.logger.info("Step 1: Claude Sonnet4クリック完了")
                    time.sleep(2)
                    return True
                return False
            else:  # GPT
                self.logger.info("GPTモード: モデル選択スキップ")
                return True
                
        except Exception as e:
            self.logger.error(f"AIモデル選択エラー: {str(e)}")
            return False
    
    def _clean_and_join_content(self, content_parts: list) -> str:
        """コンテンツクリーンアップ・結合"""
        cleaned_parts = []
        
        for part in content_parts:
            if part:
                # 連続する改行を単一改行に統一
                cleaned = re.sub(r'\n\s*\n', '\n', part.strip())
                if cleaned:
                    cleaned_parts.append(cleaned)
        
        return '\n'.join(cleaned_parts)
    
    def _update_and_backup_file(self, note_file: Path, backup_folder: Path, new_content: str) -> bool:
        """ファイル更新・バックアップ（1-15行目のみ置き換え）"""
        try:
            # 元ファイル読み込み
            with open(note_file, 'r', encoding='utf-8') as f:
                original_lines = f.readlines()
            
            # 16行目以降を保持
            remaining_lines = []
            if len(original_lines) > 15:
                remaining_lines = original_lines[15:]
            
            # 元ファイルをバックアップフォルダに移動
            backup_file = backup_folder / note_file.name
            shutil.move(str(note_file), str(backup_file))
            self.logger.info(f"バックアップ作成: {backup_file.name}")
            
            # 新しいファイル名
            new_filename = f"セールスレター追記済み{note_file.name}"
            new_file = note_file.parent / new_filename
            
            # 新しい内容で保存（AI内容 + 16行目以降）
            with open(new_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
                if remaining_lines:
                    f.write('\n')
                    f.writelines(remaining_lines)
            
            self.logger.info(f"新ファイル作成: {new_filename}（1-15行目を置き換え、16行目以降保持）")
            return True
            
        except Exception as e:
            self.logger.error(f"ファイル更新エラー: {str(e)}")
            return False


# テスト関数
def test_frontend_salesletter_automation():
    """テスト"""
    print("=== Frontend Salesletter Automation テスト ===")
    
    try:
        from modules.chrome_manager import ChromeManager
        from modules.config_manager import ConfigManager
        
        config = ConfigManager()
        chrome_manager = ChromeManager(config)
        automation = FrontendSalesletterAutomation(chrome_manager)
        
        print("✓ 初期化成功")
        return True
        
    except Exception as e:
        print(f"✗ テストエラー: {str(e)}")
        return False

if __name__ == "__main__":
    test_frontend_salesletter_automation()
