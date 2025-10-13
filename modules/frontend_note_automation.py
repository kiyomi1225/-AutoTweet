# modules/frontend_note_automation.py - フロントエンドnote自動取得（既存ファイル保持版）
import time
import random
import pyautogui
import pyperclip
from pathlib import Path
import json
import glob
import re

try:
    from .logger_setup import setup_module_logger
    from .base_automation import BaseAutomation
except ImportError:
    import sys
    sys.path.append('.')
    from modules.logger_setup import setup_module_logger
    from modules.base_automation import BaseAutomation

class FrontendNoteAutomation(BaseAutomation):
    def __init__(self, chrome_manager):
        """フロントエンドnote自動取得クラス（既存ファイル保持版）"""
        super().__init__("FrontendNoteAutomation")
        self.chrome_manager = chrome_manager
        self.config = self._load_config()
        
        self.logger.info("フロントエンドnote自動取得を初期化しました（既存ファイル保持版）")
    
    def _load_config(self):
        """設定ファイル読み込み"""
        config_path = Path("config/content_creation_config.json")
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # デフォルト設定作成
            default_config = {
                "note_ai_url": "https://claude.ai/project/019952bf-5cc7-755b-b674-cd06bb0b76de",
                "chrome_profile": "コンテンツ作成用プロファイル",
                "automation": {
                    "default_wait_time": 90,
                    "default_loop_count": 10,
                    "random_ranges": {
                        "first": [1, 30],
                        "second": [1, 10], 
                        "third": [1, 10]
                    }
                }
            }
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            return default_config
    
    def _count_existing_files(self, data_folder: Path) -> int:
        """既存のフロントエンドnoteファイル数をカウント"""
        try:
            pattern = str(data_folder / "フロントエンドnote*.txt")
            existing_files = glob.glob(pattern)
            
            # セールスレター追記済みファイルは除外
            existing_files = [f for f in existing_files if "セールスレター追記済み" not in f]
            
            count = len(existing_files)
            
            if count > 0:
                self.logger.info(f"📝 既存ファイル検出: {count}件")
                for file_path in sorted(existing_files):
                    self.logger.info(f"  - {Path(file_path).name}")
            
            return count
            
        except Exception as e:
            self.logger.warning(f"ファイルカウントエラー: {str(e)}")
            return 0
    
    def run_automation(self, account_id: str, wait_time: int = 90, loop_count: int = 10) -> bool:
        """メイン自動化実行（既存ファイル保持版）"""
        try:
            self.logger.info(f"フロントエンドnote自動取得開始: {account_id}")

            # AI種別判定
            url = self.config.get('note_ai_url', '')
            ai_type = self._detect_ai_type(url)
            self.logger.info(f"🤖 AI種別: {ai_type}")

            # データフォルダパス
            data_folder = Path(f"C:\\Users\\shiki\\AutoTweet\\data\\{account_id}\\フロントエンドnote")
            self.logger.info(f"📁 データフォルダ: {data_folder}")
            
            # データフォルダ作成（存在しない場合）
            data_folder.mkdir(parents=True, exist_ok=True)
            
            # 🆕 既存ファイルをカウント（削除しない）
            existing_count = self._count_existing_files(data_folder)
            start_num = existing_count + 1  # 次の番号から開始
            
            if existing_count > 0:
                self.logger.info(f"✅ 既存ファイル {existing_count}件を保持")
                self.logger.info(f"🔢 note{start_num}から作成を開始します")
            else:
                self.logger.info(f"🔢 note1から作成を開始します")
            
            # 必要ファイル確認
            if not self._check_required_files(account_id):
                self.logger.error("必要ファイル確認失敗")
                return False
            
            # 🆕 既存ファイル数の次から開始
            end_num = start_num + loop_count - 1
            
            self.logger.info(f"📊 作成予定: note{start_num} ～ note{end_num} ({loop_count}件)")
            
            for loop_num in range(start_num, end_num + 1):
                current_loop = loop_num - start_num + 1
                self.logger.info(f"\n{'='*60}")
                self.logger.info(f"🔄 ループ {current_loop}/{loop_count} 開始 (note{loop_num})")
                self.logger.info(f"{'='*60}")
                
                # Chrome起動
                if not self._start_chrome():
                    self.logger.error(f"Chrome起動失敗: ループ{loop_num}")
                    return False
                
                # 自動化実行
                output_file = data_folder / f"フロントエンドnote{loop_num}.txt"
                self.logger.info(f"📄 出力ファイル: {output_file}")
                success = self._execute_single_loop(account_id, output_file, wait_time, ai_type)
                
                # Chrome終了
                self._close_chrome()
                
                if not success:
                    self.logger.error(f"ループ {loop_num} 失敗")
                    return False
                
                self.logger.info(f"✅ ループ {current_loop} 完了: {output_file.name}")

                # 次ループまで待機
                if loop_num < end_num:
                    self.logger.info(f"⏳ 次ループまで10秒待機...")
                    time.sleep(10)
            
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"🎉 全ループ完了: {loop_count}件作成")
            self.logger.info(f"📁 総ファイル数: {end_num}件 (既存{existing_count}件 + 新規{loop_count}件)")
            self.logger.info(f"{'='*60}")
            return True
            
        except Exception as e:
            self.logger.error(f"自動化エラー: {str(e)}")
            return False
        finally:
            self._close_chrome()
    
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
        
        return True
    
    def _start_chrome(self) -> bool:
        """Chrome起動"""
        try:
            url = self.config['note_ai_url']
            
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
    
    def _execute_single_loop(self, account_id: str, output_file: Path, wait_time: int, ai_type: str) -> bool:
        """単一ループ実行"""
        try:
            # テキストエリアクリック→「スタート」入力
            if not self._click_textarea_first(ai_type):
                return False
            time.sleep(3)
            pyperclip.copy("スタート")
            pyautogui.hotkey('ctrl', 'v')
            pyautogui.press('enter')
            self.logger.info("スタート入力完了")
            time.sleep(20)
            
            # ファイルアップロード（3回）
            upload_files = [
                "キャラクターコンセプト.txt",
                "ターゲット.txt", 
                "市場リサーチ.txt"
            ]
            
            for filename in upload_files:
                if not self._upload_file(account_id, filename, ai_type):
                    return False
            
            time.sleep(3)
            
            # +ボタンクリック→テキストエリア→Enter
            if not self._click_textarea(ai_type):
                return False
            pyautogui.press('enter')
            time.sleep(30)
            
            # ランダム入力シーケンス
            self._random_input_sequence(wait_time, ai_type)
            
            # コンテンツ収集
            return self._collect_content(output_file, wait_time, ai_type)
            
        except Exception as e:
            self.logger.error(f"ループ実行エラー: {str(e)}")
            return False
    
    def _random_input_sequence(self, wait_time: int, ai_type: str):
        """ランダム入力シーケンス"""
        try:
            ranges = self.config['automation']['random_ranges']
            
            # 1～30のランダム数値
            num1 = random.randint(*ranges['first'])
            pyautogui.typewrite(str(num1))
            pyautogui.press('enter')
            pyautogui.press('enter')
            time.sleep(120)
            
            # 1～10のランダム数値
            num2 = random.randint(*ranges['second'])
            pyautogui.typewrite(str(num2))
            pyautogui.press('enter')
            pyautogui.press('enter')
            time.sleep(90)
            
            # 「タイトル」入力
            pyperclip.copy("タイトル")
            pyautogui.hotkey('ctrl', 'v')
            pyautogui.press('enter')
            pyautogui.press('enter')
            time.sleep(90)
            
            # 1～10のランダム数値
            num3 = random.randint(*ranges['third'])
            pyautogui.typewrite(str(num3))
            pyautogui.press('enter')
            pyautogui.press('enter')
            time.sleep(90)

            # スクロール（基底クラスのメソッド使用）
            self._scroll_down()
            
            self.logger.info(f"ランダム入力完了: {num1}, {num2}, タイトル, {num3}")
            
        except Exception as e:
            self.logger.error(f"ランダム入力エラー: {str(e)}")
    
    def _collect_content(self, output_file: Path, wait_time: int, ai_type: str) -> bool:
        """コンテンツ収集"""
        try:
            self.logger.info("📋 コンテンツ収集開始")
            content_parts = []
            
            # タイトル部分コピー
            self.logger.info("📝 タイトル部分コピー")
            title_content = self._copy_content(ai_type)
            if title_content:
                lines = title_content.split('\n')
                self.logger.info(f"タイトル全行数: {len(lines)}")
                
                if len(lines) >= 3:
                    # 1行目と下から3行除去
                    filtered_lines = lines[1:-3] 
                    content_parts.append('\n'.join(filtered_lines))
                    self.logger.info(f"タイトル部分保存: {len(filtered_lines)}行")  

            # 7章分のコンテンツ収集
            for chapter in range(1, 8):
                self._click_textarea(ai_type)
                time.sleep(1)
                pyautogui.typewrite("n")
                pyautogui.press('enter')
                time.sleep(wait_time)
                
                # スクロール（基底クラスのメソッド使用）
                self._scroll_down()
                
                # コピー（基底クラスのメソッド使用）
                chapter_content = self._copy_content(ai_type)
                if chapter_content:
                    # 最終行削除
                    lines = chapter_content.split('\n')
                    if lines:
                        filtered_lines = lines[:-1] if len(lines) > 1 else lines
                        content_parts.append('\n'.join(filtered_lines))
                
                self.logger.info(f"{chapter}章 収集完了")
            
            # ファイル保存
            if content_parts:
                output_file.parent.mkdir(parents=True, exist_ok=True)
                self._save_content(content_parts, output_file)
                
                self.logger.info(f"コンテンツ保存完了: {len(content_parts)}部分")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"コンテンツ収集エラー: {str(e)}")
            return False
        
    def _save_content(self, content_parts, output_file):
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
def test_frontend_note_automation():
    """テスト（既存ファイル保持版）"""
    print("=== Frontend Note Automation テスト（既存ファイル保持版） ===")
    
    try:
        from modules.chrome_manager import ChromeManager
        from modules.config_manager import ConfigManager
        
        config = ConfigManager()
        chrome_manager = ChromeManager(config)
        automation = FrontendNoteAutomation(chrome_manager)
        
        print("✓ 初期化成功")
        
        # 既存ファイルカウントテスト
        test_folder = Path("C:/Users/shiki/AutoTweet/data/acc1/フロントエンドnote")
        if test_folder.exists():
            count = automation._count_existing_files(test_folder)
            print(f"✓ 既存ファイルカウントテスト: {count}件")
        
        print("\n📋 設定内容:")
        url = automation.config.get('note_ai_url')
        ai_type = automation._detect_ai_type(url)
        print(f"  - URL: {url}")
        print(f"  - 🤖 AIタイプ: {ai_type}")
        print(f"  - プロファイル: {automation.config['chrome_profile']}")
        print(f"  - デフォルト待機時間: {automation.config['automation']['default_wait_time']}秒")
        print(f"  - デフォルトループ回数: {automation.config['automation']['default_loop_count']}回")
        
        print("\n✨ 既存ファイル保持機能:")
        print("  - 既存のnoteファイルは削除されません")
        print("  - 既存ファイル数+1から番号付けして作成されます")
        print("  例: note1が存在 → note2から作成開始")
        
        print("\n=== テスト完了 ===")
        return True
        
    except Exception as e:
        print(f"✗ テストエラー: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_frontend_note_automation()
