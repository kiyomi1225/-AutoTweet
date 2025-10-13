# modules/optin_page_automation.py - オプトインページ自動作成（AIタイプ対応・クリーンアップ版）
import time
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

class OptinPageAutomation(BaseAutomation):
    def __init__(self, chrome_manager):
        """オプトインページ自動作成クラス（AIタイプ対応・クリーンアップ版）"""
        super().__init__("OptinPageAutomation")
        self.chrome_manager = chrome_manager
        
        # 設定読み込み
        self.config = self._load_config()
        
        self.logger.info("オプトインページ自動作成を初期化しました（クリーンアップ版）")
    
    def _load_config(self):
        """設定ファイル読み込み"""
        config_path = Path("config/content_creation_config.json")
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # デフォルト設定作成
            default_config = {
                "optin_page_url": "",
                "chrome_profile": "コンテンツ作成用プロファイル",
                "automation": {
                    "default_wait_time": 90,
                    "operation_wait_time": 3
                }
            }
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            return default_config
    
    def select_account(self) -> str:
        """オプトインページ.txtがないアカウントを選択"""
        try:
            base_path = Path("C:\\Users\\shiki\\AutoTweet\\data")
            if not base_path.exists():
                self.logger.error(f"データフォルダが見つかりません: {base_path}")
                return None
            
            # 全アカウントフォルダ取得
            account_folders = [d for d in base_path.iterdir() if d.is_dir()]
            
            # オプトインページ.txtが存在しないアカウントをフィルタ
            available_accounts = []
            for account_folder in account_folders:
                optin_file = account_folder / "オプトインページ" / "オプトインページ.txt"
                if not optin_file.exists():
                    available_accounts.append(account_folder.name)
            
            if not available_accounts:
                self.logger.warning("オプトインページ未作成のアカウントが見つかりません")
                return None
            
            # アカウント選択表示
            print("\n" + "="*50)
            print("📋 オプトインページ未作成アカウント一覧")
            print("="*50)
            for idx, account in enumerate(available_accounts, 1):
                print(f"{idx}. {account}")
            print("="*50)
            
            # ユーザー選択
            while True:
                try:
                    choice = input(f"\nアカウント番号を選択 (1-{len(available_accounts)}): ").strip()
                    choice_num = int(choice)
                    if 1 <= choice_num <= len(available_accounts):
                        selected = available_accounts[choice_num - 1]
                        self.logger.info(f"選択されたアカウント: {selected}")
                        return selected
                    else:
                        print(f"⚠️ 1から{len(available_accounts)}の番号を入力してください")
                except ValueError:
                    print("⚠️ 数値を入力してください")
                except KeyboardInterrupt:
                    self.logger.info("アカウント選択をキャンセルしました")
                    return None
            
        except Exception as e:
            self.logger.error(f"アカウント選択エラー: {str(e)}")
            return None
    
    def run_automation(self, account_id: str = None, wait_time: int = None) -> bool:
        """メイン自動化実行（AIタイプ対応版）"""
        try:
            # アカウント選択
            if account_id is None:
                account_id = self.select_account()
                if account_id is None:
                    return False
            
            # 待機時間入力
            if wait_time is None:
                wait_time = self._input_wait_time()
            
            # AIタイプ判定
            url = self.config.get('optin_page_url', '')
            ai_type = self._detect_ai_type(url)
            self.logger.info(f"🤖 AIタイプ: {ai_type}")
            
            self.logger.info(f"オプトインページ自動作成開始: {account_id}")
            self.logger.info(f"AI応答待機時間: {wait_time}秒")
            
            # データフォルダパス
            data_folder = Path(f"C:\\Users\\shiki\\AutoTweet\\data\\{account_id}\\オプトインページ")
            
            # データフォルダ確認・作成
            if not data_folder.exists():
                data_folder.mkdir(parents=True, exist_ok=True)
                self.logger.info(f"データフォルダ作成: {data_folder}")
            
            # 既存ファイル削除
            self._cleanup_existing_files(data_folder)
            
            # 必要ファイル確認
            if not self._check_required_files(account_id):
                self.logger.error("必要ファイル確認失敗")
                return False
            
            # Chrome起動
            if not self._start_chrome():
                return False
            
            # 自動化実行
            output_file = data_folder / "オプトインページ.txt"
            self.logger.info(f"📄 出力ファイル: {output_file}")
            success = self._execute_automation(account_id, output_file, wait_time, ai_type)
                        
            if success:
                print(f"\n{'='*50}")
                print(f"✅ オプトインページ作成完了")
                print(f"📄 ファイル: {output_file}")
                print(f"🤖 使用AI: {ai_type}")
                print(f"{'='*50}\n")
            else:
                self.logger.error("オプトインページ作成失敗")
            
            return success
            
        except Exception as e:
            self.logger.error(f"自動化エラー: {str(e)}")
            return False
        finally:
            self._close_chrome()
    
    def _input_wait_time(self) -> int:
        """AI応答待機時間入力"""
        default_wait = self.config['automation']['default_wait_time']
        print(f"\n⏱️ AI応答待機時間を入力してください（デフォルト: {default_wait}秒）")
        
        while True:
            try:
                user_input = input(f"待機時間（秒） [Enter={default_wait}]: ").strip()
                if user_input == "":
                    return default_wait
                
                wait_time = int(user_input)
                if wait_time > 0:
                    return wait_time
                else:
                    print("⚠️ 正の整数を入力してください")
            except ValueError:
                print("⚠️ 数値を入力してください")
            except KeyboardInterrupt:
                self.logger.info("デフォルト値を使用します")
                return default_wait
    
    def _cleanup_existing_files(self, data_folder: Path):
        """既存ファイル削除"""
        try:
            pattern = str(data_folder / "オプトインページ.txt")
            existing_files = glob.glob(pattern)
            
            for file_path in existing_files:
                Path(file_path).unlink()
                self.logger.info(f"既存ファイル削除: {Path(file_path).name}")
                
        except Exception as e:
            self.logger.warning(f"ファイル削除エラー: {str(e)}")
    
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
            file_path = base_path / filename
            if not file_path.exists():
                missing_files.append(str(file_path))
        
        if missing_files:
            self.logger.error(f"必要ファイルが見つかりません:")
            for missing in missing_files:
                self.logger.error(f"  - {missing}")
            return False
        
        self.logger.info("必要ファイル確認完了")
        return True
    
    def _start_chrome(self) -> bool:
        """Chrome起動"""
        try:
            url = self.config.get('optin_page_url', 'https://claude.ai/project/0199b980-c35f-77d5-b9f1-87594addbcde')
            profile = self.config['chrome_profile']
            
            import subprocess
            cmd = [
                "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
                f"--user-data-dir=C:\\Users\\shiki\\AppData\\Local\\Google\\Chrome\\User Data",
                f"--profile-directory={profile}",
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
            self.logger.info("Chrome全画面表示完了")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Chrome起動エラー: {str(e)}")
            return False
    
    def _execute_automation(self, account_id: str, output_file: Path, wait_time: int, ai_type: str) -> bool:
        """自動化実行（AIタイプ対応版）"""
        try:
            wait = self.config['automation'].get('operation_wait_time', 3)
            
            # Step 1: テキストエリアクリック（初回用）- BaseAutomationのメソッド使用
            self.logger.info(f"Step 1: テキストエリアクリック ({ai_type})")
            if not self._click_textarea_first(ai_type):
                return False
            
            # Step 2: 「スタート」入力
            self.logger.info("Step 2: 「スタート」入力")
            pyperclip.copy("スタート")
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(wait)
            pyautogui.press('enter')
            time.sleep(15)

            # Step 3: ファイルアップロード（3回）
            upload_files = [
                "キャラクターコンセプト.txt",
                "ターゲット.txt",
                "市場リサーチ.txt"
            ]
            
            for idx, filename in enumerate(upload_files, 1):
                self.logger.info(f"Step 3-{idx}: {filename} アップロード ({ai_type})")
                # BaseAutomationのメソッド使用
                if not self._upload_file(account_id, filename, ai_type):
                    return False
                time.sleep(wait)
            
            # Step 4: Enter送信 - BaseAutomationのメソッド使用
            self.logger.info("Step 4: Enter送信")
            self._click_textarea(ai_type)
            pyautogui.press('enter')
            
            # Step 5: AI応答待機
            self.logger.info(f"Step 5: AI応答待機（{wait_time}秒）")
            time.sleep(wait_time)
            
            # Step 6: コンテンツ収集
            self.logger.info("Step 6: コンテンツ収集開始")
            return self._collect_content(output_file, wait_time, wait, ai_type)
            
        except Exception as e:
            self.logger.error(f"自動化実行エラー: {str(e)}")
            return False
    
    def _collect_content(self, output_file: Path, wait_time: int, operation_wait: int, ai_type: str) -> bool:
        """コンテンツ収集（9回）"""
        try:
            content_parts = []
            
            # 1回目：収集なし
            self.logger.info("収集 1/9: 「n」送信（収集なし）")
            if not self._click_textarea(ai_type):  # BaseAutomationのメソッド
                return False
            time.sleep(operation_wait)
            pyautogui.typewrite("n")
            pyautogui.press('enter')
            time.sleep(wait_time)
            
            # 2～9回目：コンテンツ収集
            for round_num in range(2, 10):
                self.logger.info(f"収集 {round_num}/9: 「n」送信")
                
                # テキストエリアクリック - BaseAutomationのメソッド
                if not self._click_textarea(ai_type):
                    self.logger.warning(f"テキストエリアクリック失敗: {round_num}/9")
                time.sleep(operation_wait)
                
                # 「n」送信
                pyautogui.typewrite("n")
                pyautogui.press('enter')
                time.sleep(wait_time)

                # スクロール - BaseAutomationのメソッド
                self._scroll_down()
                
                # コンテンツコピー - BaseAutomationのメソッド
                content = self._copy_content(ai_type)
                if content:
                    # 最終行削除
                    lines = content.split('\n')
                    if lines:
                        filtered_lines = lines[:-1] if len(lines) > 1 else lines
                        content_parts.append('\n'.join(filtered_lines))
                        self.logger.info(f"収集成功：（{len(filtered_lines)}行）")
                else:
                    self.logger.warning(f"コンテンツ収集失敗")
            
            # ファイル保存
            if content_parts:
                output_file.parent.mkdir(parents=True, exist_ok=True)

                # 改行整理
                cleaned_parts = []
                for part in content_parts:
                    if part:
                        cleaned = re.sub(r'\n\s*\n', '\n', part.strip())
                        cleaned_parts.append(cleaned)
                
                # 部分間は改行1つで結合
                final_content = '\n'.join(cleaned_parts)

                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(final_content)
                
                self.logger.info(f"コンテンツ保存完了: {len(content_parts)}部分")
                return True
            else:
                self.logger.error("収集されたコンテンツがありません")
                return False
            
        except Exception as e:
            self.logger.error(f"コンテンツ収集エラー: {str(e)}")
            return False


# テスト関数
def test_optin_page_automation():
    """テスト（クリーンアップ版）"""
    print("=== Optin Page Automation テスト (クリーンアップ版) ===")
    
    try:
        from modules.chrome_manager import ChromeManager
        from modules.config_manager import ConfigManager
        
        config = ConfigManager()
        chrome_manager = ChromeManager(config)
        automation = OptinPageAutomation(chrome_manager)
        
        print("✓ 初期化成功")
        print("\n📋 設定内容:")
        
        url = automation.config.get('optin_page_url')
        ai_type = automation._detect_ai_type(url)
        
        print(f"  - URL: {url}")
        print(f"  - 🤖 AIタイプ: {ai_type}")
        print(f"  - プロファイル: {automation.config['chrome_profile']}")
        print(f"  - デフォルト待機時間: {automation.config['automation']['default_wait_time']}秒")
        
        # AI判定テスト
        test_urls = [
            "https://chatgpt.com/g/test",
            "https://claude.ai/project/test"
        ]
        print("\n✓ AI判定テスト:")
        for test_url in test_urls:
            detected = automation._detect_ai_type(test_url)
            print(f"  {test_url} → {detected}")
        
        print("\n✨ クリーンアップ情報:")
        print("  - BaseAutomationから継承した共通メソッドを使用")
        print("  - 重複メソッドを削除（_scroll_down, _copy_content, _close_chrome）")
        print("  - コード量を削減し、保守性を向上")
        
        print("\n=== テスト完了 ===")
        return True
        
    except Exception as e:
        print(f"✗ テストエラー: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_optin_page_automation()
