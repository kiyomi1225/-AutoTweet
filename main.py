# main.py - Twitter自動化システム メインエントリーポイント（クリーン版）
"""
Twitter自動化システム
VPN + Chrome + GPT + Twitter投稿の統合システム
"""

import sys
import time
import glob
from pathlib import Path

# モジュールパス追加
sys.path.append('.')

# コアモジュールインポート
try:
    from modules.config_manager import ConfigManager
    from modules.vpn_manager import VPNManager
    from modules.chrome_manager import ChromeManager
    from modules.csv_manager import CSVManager
    from modules.gpt_image_automation import GPTImageAutomation
    from modules.threads_rotation_poster import ThreadsRotationPoster
    from modules.frontend_note_automation import FrontendNoteAutomation
    from modules.frontend_salesletter_automation import FrontendSalesletterAutomation
    from modules.daily_mail_automation import DailyMailAutomation 
    from modules.myasp_mail_automation import MyASPMailAutomation
    from modules.optin_page_automation import OptinPageAutomation

except ImportError as e:
    print(f"❌ モジュールインポートエラー: {e}")
    print("必要なモジュールが不足している可能性があります。")
    print("pip install -r requirements.txt を実行してください。")
    sys.exit(1)

class TwitterAutomationSystem:
    """Twitter自動化システム メインクラス"""
    
    def __init__(self):
        """初期化"""
        print("=" * 60)
        print("🚀 Twitter自動化システム初期化中...")
        print("=" * 60)
        
        try:
            # 設定管理
            print("📋 設定管理初期化中...")
            self.config = ConfigManager()
            print("✅ 設定管理初期化完了")
            
            # VPN管理
            print("🔒 VPN管理初期化中...")
            self.vpn_manager = VPNManager(self.config)
            print("✅ VPN管理初期化完了")
            
            # Chrome管理
            print("🌐 Chrome管理初期化中...")
            self.chrome_manager = ChromeManager(self.config)
            print("✅ Chrome管理初期化完了")
            
            # CSV管理
            print("📊 CSV管理初期化中...")
            self.csv_manager = CSVManager(self.config)
            print("✅ CSV管理初期化完了")
            
            # GPT画像認識自動化(ツイート作成)
            print("📷 GPTツイート取得自動化初期化中...")
            self.gpt_image_automation = GPTImageAutomation()
            print("✅ GPTツイート取得自動化初期化完了")
            
            # Threads循環投稿
            print("🔄 Threads循環投稿初期化中...")
            self.threads_rotation_poster = ThreadsRotationPoster(self.config, self.vpn_manager)  
            print("✅ Threads循環投稿初期化完了")
            
             # フロントエンドnote自動作成
            print("📝 フロントエンドnote自動化初期化中...")
            self.frontend_note_automation = FrontendNoteAutomation(self.chrome_manager)
            print("✅ フロントエンドnote自動化初期化完了")

             # フロントエンドnoteセールスレター自動作成
            print("📄 フロントエンドnoteセールスレター自動化初期化中...")
            self.frontend_salesletter_automation = FrontendSalesletterAutomation(self.chrome_manager)
            print("✅ フロントエンドnoteセールスレター自動化初期化完了")

            # デイリーメルマガ自動作成
            print("📧 デイリーメルマガ自動化初期化中...")
            self.daily_mail_automation = DailyMailAutomation(self.chrome_manager)
            print("✅ デイリーメルマガ自動化初期化完了")

             # MyASPメルマガ自動化登録
            print("📧 MyASPメルマガ自動化初期化中...")
            self.myasp_automation = MyASPMailAutomation()
            print("✅ MyASPメルマガ自動化初期化完了")

             # オプトインページ自動作成
            print("📧 オプトインページ自動作成初期化中...")
            self.optin_automation = OptinPageAutomation(self.chrome_manager)
            print("✅ オプトインページ自動作成初期化中...")

            print("\n🎉 全モジュール初期化完了!")
            
        except Exception as e:
            print(f"❌ 初期化エラー: {str(e)}")
            sys.exit(1)
    
    def run_system_check(self):
        """システム動作確認"""
        print("\n" + "=" * 60)
        print("🔧 システム動作確認開始")
        print("=" * 60)
        
        try:
            # 基本情報表示
            print(f"📍 元のIPアドレス: {self.vpn_manager.original_ip}")
            
            # アカウント確認
            accounts = self.config.get_all_accounts()
            print(f"👥 登録アカウント数: {len(accounts)}")
            for account_id in accounts:
                print(f"   - {account_id}")
            
            if not accounts:
                print("❌ 登録アカウントがありません")
                return False
            
            # テスト用アカウント
            test_account = accounts[0]
            print(f"\n🧪 テストアカウント: {test_account}")
            
            # VPN接続テスト
            print(f"\n[Step 1] VPN接続テスト...")
            vpn_success = self.vpn_manager.smart_vpn_connect(test_account)
            
            if vpn_success:
                info = self.vpn_manager.get_connection_info()
                print(f"✅ VPN接続成功")
                print(f"   🔒 VPN IP: {info['current_ip']}")
                
                # Chrome起動テスト
                print(f"\n[Step 2] Chrome起動テスト...")
                chrome_success = self.chrome_manager.start_chrome_profile(
                    test_account, "https://whatismyipaddress.com/"
                )
                
                if chrome_success:
                    print(f"✅ Chrome起動成功")
                    print(f"   🌐 プロファイル: {test_account}")
                    print(f"   📂 アクティブプロファイル: {self.chrome_manager.get_active_profiles()}")
                    
                    print(f"\n⏳ 5秒間動作確認中...")
                    time.sleep(5)
                    
                    # 終了処理
                    print(f"\n[Step 3] クリーンアップ...")
                    self.chrome_manager._close_chrome_with_image()
                    
                    # VPN切断
                    self.vpn_manager.disconnect()
                    print(f"✅ VPN切断完了")
                    
                    print(f"\n🎉 システム動作確認完了！")
                    return True
                else:
                    print(f"❌ Chrome起動失敗")
                    self.vpn_manager.disconnect()
                    return False
            else:
                print(f"❌ VPN接続失敗")
                return False
                
        except Exception as e:
            print(f"❌ システムチェックエラー: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def show_status(self):
        """システム状態表示"""
        print("\n" + "=" * 60)
        print("📊 システム状態")
        print("=" * 60)
        
        # VPN状態
        try:
            vpn_info = self.vpn_manager.get_connection_info()
            print(f"🔒 VPN状態:")
            print(f"   現在のIP: {vpn_info['current_ip']}")
            print(f"   元のIP: {vpn_info['original_ip']}")
            if vpn_info['current_ip'] != vpn_info['original_ip']:
                print(f"   状態: 🟢 VPN接続中")
            else:
                print(f"   状態: 🔴 VPN未接続")
        except Exception as e:
            print(f"🔒 VPN状態: ❌ 取得エラー ({str(e)})")
        
        # Chrome状態
        try:
            active_profiles = self.chrome_manager.get_active_profiles()
            print(f"\n🌐 Chrome状態:")
            print(f"   アクティブプロファイル数: {len(active_profiles)}")
            for profile in active_profiles:
                print(f"   - {profile}")
        except Exception as e:
            print(f"🌐 Chrome状態: ❌ 取得エラー ({str(e)})")
        
        # 設定情報
        try:
            accounts = self.config.get_all_accounts()
            print(f"\n⚙️ 設定情報:")
            print(f"   登録アカウント数: {len(accounts)}")
            for account_id in accounts:
                account_config = self.config.get_account_config(account_id)
                print(f"   - {account_id}: {account_config.get('gpt_url', 'URL未設定')}")
        except Exception as e:
            print(f"⚙️ 設定情報: ❌ 取得エラー ({str(e)})")
    
    def gpt_image_automation_session(self):
        """GPTツイート取得自動化実行"""
        print("\n" + "=" * 60)
        print("📷 GPTツイート取得自動化セッション開始")
        print("=" * 60)
        
        try:
            # 事前チェック
            required_images = ["gpt_textarea.png", "gpt_copy_button.png", "close_button.png"]
            for img_name in required_images:
                if not Path(f"images/{img_name}").exists():
                    print(f"❌ images/{img_name} が見つかりません")
                    print("\n📋 準備手順:")
                    if img_name == "textarea.png":
                        print("1. GPTsページのテキスト入力エリアをスクリーンショット")
                        print("2. images/textarea.png として保存")
                    elif img_name == "copy_button.png":
                        print("1. GPT応答右上のコピーマークをスクリーンショット")
                        print("2. images/copy_button.png として保存")
                    elif img_name == "close_button.png":
                        print("1. Chromeウィンドウ右上の閉じるボタン（×）をスクリーンショット")
                        print("2. images/close_button.png として保存")
                    return
            
            # アカウント選択
            accounts = self.gpt_image_automation.get_available_accounts()
            if not accounts:
                print("❌ 利用可能なアカウントがありません")
                return
            
            print(f"\n📋 利用可能なアカウント:")
            for i, account_id in enumerate(accounts, 1):
                account_config = self.config.get_account_config(account_id)
                if account_config:
                    gpt_url = account_config.get('gpt_url', '未設定')
                    print(f"  {i}. {account_id} ")
                else:
                    print(f"  {i}. {account_id} (設定エラー)")
                        
            selected_accounts = []
            
            while True:
                selection = input(f"\n選択してください（例: 1,3,5 または 1-5 または all）: ").strip()
                
                if selection.lower() == 'all':
                    selected_accounts = accounts.copy()
                    break
                elif ',' in selection:
                    # 個別選択: 1,3,5
                    try:
                        indices = [int(x.strip()) - 1 for x in selection.split(',')]
                        if all(0 <= i < len(accounts) for i in indices):
                            selected_accounts = [accounts[i] for i in indices]
                            break
                        else:
                            print("❌ 無効な番号が含まれています")
                    except ValueError:
                        print("❌ 数値を入力してください（例: 1,3,5）")
                elif '-' in selection:
                    # 範囲選択: 1-5
                    try:
                        start, end = selection.split('-')
                        start_idx = int(start.strip()) - 1
                        end_idx = int(end.strip()) - 1
                        if 0 <= start_idx <= end_idx < len(accounts):
                            selected_accounts = accounts[start_idx:end_idx+1]
                            break
                        else:
                            print("❌ 無効な範囲です")
                    except ValueError:
                        print("❌ 正しい形式で入力してください（例: 1-5）")
                else:
                    # 単一選択: 1
                    try:
                        index = int(selection) - 1
                        if 0 <= index < len(accounts):
                            selected_accounts = [accounts[index]]
                            break
                        else:
                            print("❌ 無効な番号です")
                    except ValueError:
                        print("❌ 数値を入力してください")
            
            print(f"\n✅ 選択されたアカウント: {selected_accounts}")
            
            # 目標取得数入力
            while True:
                try:
                    target_input = input("\n各アカウントの目標取得数を入力してください (デフォルト:100): ").strip()
                    target_count = int(target_input) if target_input else 100
                    if target_count > 0:
                        break
                    else:
                        print("❌ 1以上の数値を入力してください")
                except ValueError:
                    print("❌ 数値を入力してください")
            
            # 待機時間入力
            while True:
                try:
                    wait_input = input("\nGPT/Claude応答待機時間を入力してください (デフォルト:60秒): ").strip()
                    wait_time = int(wait_input) if wait_input else 60
                    if wait_time > 0:
                        break
                    else:
                        print("❌ 1以上の数値を入力してください")
                except ValueError:
                    print("❌ 数値を入力してください")

            print(f"   ⏱️ 応答待機時間: {wait_time}秒")

            # 設定確認
            print(f"\n📋 実行設定確認:")
            print(f"   🎯 対象アカウント: {len(selected_accounts)}件")
            for account_id in selected_accounts:
                account_config = self.config.get_account_config(account_id)
                gpt_url = account_config.get('gpt_url', '未設定') if account_config else '未設定'
                print(f"     - {account_id}: {gpt_url}")
            print(f"   📊 各アカウント目標: {target_count}件")
            
            confirm = input(f"\n自動化を実行しますか？ (y/n): ")
            if confirm.lower() != 'y':
                print("🚫 実行をキャンセルしました")
                return
            
            print(f"\n🚀 GPT画像認識自動化を開始します...")
            print(f"⚠️ 注意: 実行中はマウス・キーボードを操作しないでください")
            
            # カウントダウン
            for i in range(5, 0, -1):
                print(f"⏰ {i}秒後に開始...")
                time.sleep(1)
            
            # 複数アカウント自動化実行
            success = self.gpt_image_automation.run_automation(
                selected_accounts, wait_time, target_count=target_count
            )
            
            if success:
                print(f"\n🎉 GPT画像認識自動化完了！")
                print(f"   📁 結果ファイル:")
                
            # 各アカウントの結果確認
            for account_id in selected_accounts:
                csv_file = Path(f"C:/Users/shiki/AutoTweet/data/{account_id}/tweets.csv")
                if csv_file.exists():
                    import csv
                    with open(csv_file, 'r', encoding='utf-8') as f:
                        reader = csv.reader(f)
                        next(reader)  # ヘッダースキップ
                        total_count = sum(1 for row in reader)
                    print(f"     - {account_id}/tweets.csv: {total_count}件")
                else:
                    print(f"     - {account_id}/tweets.csv: ファイルなし")       

                # 最新ツイート表示オプション
                show_recent = input(f"\n最新の取得ツイートを表示しますか？ (y/n): ")
                if show_recent.lower() == 'y':
                    for account_id in selected_accounts:
                        csv_file = Path(f"data/{account_id}.csv")
                        if csv_file.exists():
                            print(f"\n📝 {account_id} の最新ツイート:")
                            self._show_recent_tweets(csv_file, 3)
            else:
                print(f"\n❌ GPT画像認識自動化に失敗しました")
                    
        except KeyboardInterrupt:
            print(f"\n⚠️ ユーザーによる中断")
        except Exception as e:
            print(f"❌ GPT画像認識自動化エラー: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def _show_recent_tweets(self, csv_file: Path, count: int = 5):
        """最新のツイートを表示"""
        try:
            import csv
            tweets = []
            
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                header = next(reader)  # ヘッダー取得
                for row in reader:
                    tweets.append(row)
            
            print(f"\n📝 最新 {min(count, len(tweets))} 件のツイート:")
            print("-" * 60)
            
            for i, tweet_row in enumerate(tweets[-count:], 1):
                if len(tweet_row) >= 2:
                    content = tweet_row[1]  # content列
                    length = len(content)
                    print(f"{i}. ({length}文字) {content}")
            
            print("-" * 60)
            
        except Exception as e:
            print(f"❌ ツイート表示エラー: {str(e)}")
    
    def show_logs(self):
        """ログ確認"""
        print("\n" + "=" * 60)
        print("📋 ログ確認")
        print("=" * 60)
        
        log_dir = Path("logs")
        if log_dir.exists():
            log_files = list(log_dir.glob("*.log"))
            if log_files:
                print(f"📁 ログファイル数: {len(log_files)}")
                
                # 最新5件表示
                for log_file in sorted(log_files, key=lambda x: x.stat().st_mtime, reverse=True)[:5]:
                    size = log_file.stat().st_size
                    mtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(log_file.stat().st_mtime))
                    print(f"  📄 {log_file.name} ({size:,} bytes, {mtime})")
                
                # ログ内容表示オプション
                view_log = input(f"\n最新ログの内容を表示しますか？ (y/n): ")
                if view_log.lower() == 'y':
                    latest_log = sorted(log_files, key=lambda x: x.stat().st_mtime, reverse=True)[0]
                    try:
                        with open(latest_log, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                            print(f"\n📋 {latest_log.name} (最新50行)")
                            print("-" * 60)
                            for line in lines[-50:]:
                                print(line.rstrip())
                    except Exception as e:
                        print(f"❌ ログ読み込みエラー: {str(e)}")
            else:
                print("📁 ログファイルがありません")
        else:
            print("📁 ログディレクトリが見つかりません")
    
    def threads_rotation_session(self):
        """Threads循環投稿セッション"""
        print("\n" + "=" * 60)
        print("🔄 Threads循環投稿セッション開始")
        print("=" * 60)
        
        try:
            # 画像ファイル事前チェック
            required_images = ["threads_textarea.png", "threads_post_button.png"]
            for img_name in required_images:
                if not Path(f"images/{img_name}").exists():
                    print(f"❌ images/{img_name} が見つかりません")
                    print("\n📋 準備手順:")
                    if img_name == "threads_textarea.png":
                        print("1. Threadsページの投稿入力エリアをスクリーンショット")
                        print("2. images/threads_textarea.png として保存")
                    elif img_name == "threads_post_button.png":
                        print("1. Threads投稿ボタンをスクリーンショット")
                        print("2. images/threads_post_button.png として保存")
                    return
            
            # アカウント選択（tweets.csvが存在するもののみ）
            accounts = []
            for i in range(1, 100):
                account_id = f"acc{i}"
                csv_path = Path(f"C:/Users/shiki/AutoTweet/data/{account_id}/tweets.csv")
                if csv_path.exists():
                    accounts.append(account_id)

            if not accounts:
                print("❌ 利用可能なアカウントがありません（tweets.csvが存在しません）")
                return

            print(f"\n📋 利用可能なアカウント:")
            for i, account_id in enumerate(accounts, 1):
                unused_count = self.threads_rotation_poster.count_unused_tweets(account_id)
                print(f"  {i}. {account_id} (未使用: {unused_count}件)")    

            # 複数アカウント選択
            print(f"\n対象アカウントを選択してください（複数可）:")
            print("  > 個別: 1,3,5 > 範囲: 1-5  > 全選択: all > 単一: 1")
            
            selected_accounts = []
            
            while True:
                selection = input(f"選択してください: ").strip()
                
                if selection.lower() == 'all':
                    selected_accounts = accounts.copy()
                    break
                elif ',' in selection:
                    try:
                        indices = [int(x.strip()) - 1 for x in selection.split(',')]
                        if all(0 <= i < len(accounts) for i in indices):
                            selected_accounts = [accounts[i] for i in indices]
                            break
                        else:
                            print("❌ 無効な番号が含まれています")
                    except ValueError:
                        print("❌ 数値を入力してください（例: 1,3,5）")
                elif '-' in selection:
                    try:
                        start, end = selection.split('-')
                        start_idx = int(start.strip()) - 1
                        end_idx = int(end.strip()) - 1
                        if 0 <= start_idx <= end_idx < len(accounts):
                            selected_accounts = accounts[start_idx:end_idx+1]
                            break
                        else:
                            print("❌ 無効な範囲です")
                    except ValueError:
                        print("❌ 正しい形式で入力してください（例: 1-5）")
                else:
                    try:
                        index = int(selection) - 1
                        if 0 <= index < len(accounts):
                            selected_accounts = [accounts[index]]
                            break
                        else:
                            print("❌ 無効な番号です")
                    except ValueError:
                        print("❌ 数値を入力してください")
            
            print(f"\n✅ 選択されたアカウント: {selected_accounts}")
            
            # 設定確認
            print(f"\n📋 実行設定確認:")
            print(f"   🎯 対象アカウント: {len(selected_accounts)}件")
            total_tweets = 0
            for account_id in selected_accounts:
                unused_count = self.threads_rotation_poster.count_unused_tweets(account_id)
                total_tweets += unused_count
                print(f"     - {account_id}: {unused_count}件")
            print(f"   📊 合計投稿可能数: {total_tweets}件")
            # 待機時間確認
            while True:
                try:
                    min_wait = input("\n最小待機時間を入力してください (デフォルト:30分): ").strip()
                    min_minutes = int(min_wait) if min_wait else 30
                    
                    max_wait = input("最大待機時間を入力してください (デフォルト:60分): ").strip()
                    max_minutes = int(max_wait) if max_wait else 60
                    
                    if min_minutes > 0 and max_minutes >= min_minutes:
                        break
                    else:
                        print("❌ 最大 >= 最小 > 0 で入力してください")
                except ValueError:
                    print("❌ 数値を入力してください")

            print(f"   ⏰ 待機時間: {min_minutes}-{max_minutes}分のランダム")            
            print(f"   🔄 動作: アカウント順次投稿→枯渇スキップ→全枯渇で終了")
            
            confirm = input(f"\n循環投稿を実行しますか？ (y/n): ")
            if confirm.lower() != 'y':
                print("🚫 実行をキャンセルしました")
                return
            
            print(f"\n🚀 Threads循環投稿を開始します...")
            print(f"⚠️ 注意: 実行中はCtrl+Cで中断できます")
            
            # カウントダウン
            for i in range(3, 0, -1):
                print(f"⏰ {i}秒後に開始...")
                time.sleep(1)
            
            # 循環投稿実行
            success = self.threads_rotation_poster.run_rotation_posting(selected_accounts, min_minutes, max_minutes)
            
            if success:
                print(f"\n🎉 Threads循環投稿完了！")
            else:
                print(f"\n❌ Threads循環投稿が中断されました")
                    
        except KeyboardInterrupt:
            print(f"\n⚠️ ユーザーによる中断")
        except Exception as e:
            print(f"❌ Threads循環投稿エラー: {str(e)}")
            import traceback
            traceback.print_exc()

    def frontend_note_session(self):
        """フロントエンドnote自動取得セッション"""
        print("\n" + "=" * 60)
        print("📝 フロントエンドnote自動取得セッション開始")
        print("=" * 60)
        
        try:
            # 必要画像チェック
            required_images = ["claude_sonnet4.png", "Claude_textarea.png", "Claude_copy_button.png"]
            for img_name in required_images:
                if not Path(f"images/{img_name}").exists():
                    print(f"❌ images/{img_name} が見つかりません")
                    return
                
            # アカウント選択
            base_data_path = Path("C:\\Users\\shiki\\AutoTweet\\data")
            if not base_data_path.exists():
                print("❌ データフォルダが存在しません")
                return

            # accフォルダを検索
            acc_folders = [folder.name for folder in base_data_path.iterdir() 
                        if folder.is_dir() and folder.name.startswith('acc')]

            if not acc_folders:
                print("❌ 利用可能なアカウントがありません（accフォルダが見つかりません）")
                return

            # ソート
            acc_folders.sort()

            print(f"\n📋 利用可能なアカウント:")
            for i, account_id in enumerate(acc_folders, 1):
                print(f"  {i}. {account_id}") 

            # アカウント選択
            while True:
                try:
                    choice = input(f"アカウントを選択してください (1-{len(acc_folders)}): ").strip()
                    choice_num = int(choice)
                    if 1 <= choice_num <= len(acc_folders):
                        account_id = acc_folders[choice_num - 1]
                        break
                    else:
                        print(f"❌ 1-{len(acc_folders)}の数値を入力してください")
                except ValueError:
                    print("❌ 数値を入力してください")
                except KeyboardInterrupt:
                    return     
                       
            # 待機時間入力
            while True:
                try:
                    wait_input = input(f"待機時間を入力してください (デフォルト:90秒): ").strip()
                    wait_time = int(wait_input) if wait_input else 90
                    if wait_time > 0:
                        break
                    else:
                        print("❌ 1以上の数値を入力してください")
                except ValueError:
                    print("❌ 数値を入力してください")
            
            # ループ回数入力
            while True:
                try:
                    loop_input = input(f"ループ回数を入力してください (デフォルト:10回): ").strip()
                    loop_count = int(loop_input) if loop_input else 10
                    if loop_count > 0:
                        break
                    else:
                        print("❌ 1以上の数値を入力してください")
                except ValueError:
                    print("❌ 数値を入力してください")
            
            # 設定確認
            print(f"\n📋 実行設定確認:")
            print(f"   🆔 アカウント: {account_id}")
            print(f"   ⏱️ 待機時間: {wait_time}秒")
            print(f"   🔁 ループ回数: {loop_count}回")
            print(f"   📁 出力先: C:\\Users\\shiki\\AutoTweet\\data\\{account_id}\\")
            print(f"   📄 必要ファイル: キャラクターコンセプト.txt, ターゲット.txt, 市場リサーチ.txt")
            
            confirm = input(f"\n実行しますか？ (y/n): ")
            if confirm.lower() != 'y':
                print("🚫 実行をキャンセルしました")
                return
            
            print(f"\n🚀 フロントエンドnote自動取得を開始します...")
            print(f"⚠️ 注意: 実行中はマウス・キーボードを操作しないでください")
            
            # カウントダウン
            for i in range(5, 0, -1):
                print(f"⏰ {i}秒後に開始...")
                time.sleep(1)
            
            # 自動化実行
            success = self.frontend_note_automation.run_automation(account_id, wait_time, loop_count)
            
            if success:
                print(f"\n🎉 フロントエンドnote自動取得完了！")
                
                # 生成ファイル一覧表示
                output_dir = Path(f"C:\\Users\\shiki\\AutoTweet\\data\\{account_id}")
                note_files = list(output_dir.glob("フロントエンドnote*.txt"))
                if note_files:
                    print(f"📄 生成ファイル: {len(note_files)}件")
                    for note_file in sorted(note_files):
                        size = note_file.stat().st_size
                        print(f"   - {note_file.name} ({size:,} bytes)")
            else:
                print(f"\n❌ フロントエンドnote自動取得に失敗しました")
                
        except KeyboardInterrupt:
            print(f"\n⚠️ ユーザーによる中断")
        except Exception as e:
            print(f"❌ フロントエンドnote自動取得エラー: {str(e)}")

    def frontend_salesletter_session(self):
        """フロントエンドnoteセールスレター自動取得セッション"""
        print("\n" + "=" * 60)
        print("📄 フロントエンドnoteセールスレター自動取得セッション開始")
        print("=" * 60)
        
        try:
            # 必要画像チェック
            required_images = ["claude_sonnet4.png", "Claude_textarea_First.png", "Claude_textarea.png", "Claude_copy_button.png", "close_button.png"]
            for img_name in required_images:
                if not Path(f"images/{img_name}").exists():
                    print(f"❌ images/{img_name} が見つかりません")
                    return
            
            # アカウント選択
            base_data_path = Path("C:\\Users\\shiki\\AutoTweet\\data")
            if not base_data_path.exists():
                print("❌ データフォルダが存在しません")
                return
            
            acc_folders = [folder.name for folder in base_data_path.iterdir() 
                        if folder.is_dir() and folder.name.startswith('acc')]
            
            if not acc_folders:
                print("❌ 利用可能なアカウントがありません（accフォルダが見つかりません）")
                return
            
            acc_folders.sort()
            
            print(f"\n📋 利用可能なアカウント:")
            for i, account_id in enumerate(acc_folders, 1):
                # フロントエンドnoteファイル数を確認
                data_folder = Path(f"C:\\Users\\shiki\\AutoTweet\\data\\{account_id}\\フロントエンドnote")
                note_pattern = str(data_folder / "フロントエンドnote*.txt")
                note_files = [f for f in glob.glob(note_pattern) if "セールスレター追記済み" not in f]
                print(f"  {i}. {account_id} (フロントエンドnoteファイル: {len(note_files)}件)")
            
            while True:
                try:
                    choice = input(f"アカウントを選択してください (1-{len(acc_folders)}): ").strip()
                    choice_num = int(choice)
                    if 1 <= choice_num <= len(acc_folders):
                        account_id = acc_folders[choice_num - 1]
                        break
                    else:
                        print(f"❌ 1-{len(acc_folders)}の数値を入力してください")
                except ValueError:
                    print("❌ 数値を入力してください")
                except KeyboardInterrupt:
                    return
            
            # 待機時間入力
            while True:
                try:
                    wait_input = input(f"待機時間を入力してください (デフォルト:45秒): ").strip()
                    wait_time = int(wait_input) if wait_input else 45
                    if wait_time > 0:
                        break
                    else:
                        print("❌ 1以上の数値を入力してください")
                except ValueError:
                    print("❌ 数値を入力してください")
                        
            # 設定確認
            print(f"\n📋 実行設定確認:")
            print(f"   🆔 アカウント: {account_id}")
            print(f"   ⏱️ 待機時間: {wait_time}秒")
            print(f"   📁 出力先: C:\\Users\\shiki\\AutoTweet\\data\\{account_id}\\")
            print(f"   🗂️ バックアップ: C:\\Users\\shiki\\AutoTweet\\data\\{account_id}\\backup\\")
            print(f"   📄 必要ファイル: キャラクターコンセプト.txt, ターゲット.txt, 市場リサーチ.txt")
            print(f"   🤖 処理内容: 各ファイル1-15行目→AI処理→7章収集→セールスレター追記済みファイル作成")
                        
            confirm = input(f"\n実行しますか？ (y/n): ")
            if confirm.lower() != 'y':
                print("🚫 実行をキャンセルしました")
                return
            
            print(f"\n🚀 セールスレター自動取得を開始します...")
            print(f"⚠️ 注意: 実行中はマウス・キーボードを操作しないでください")
            
            # カウントダウン
            for i in range(5, 0, -1):
                print(f"⏰ {i}秒後に開始...")
                time.sleep(1)
            
            # 自動化実行
            success = self.frontend_salesletter_automation.run_automation(account_id, wait_time)
            
            if success:
                print(f"\n🎉 セールスレター自動取得完了！")
                
                # 生成ファイル一覧表示
                output_dir = Path(f"C:\\Users\\shiki\\AutoTweet\\data\\{account_id}\\フロントエンドnote")
                sales_files = list(output_dir.glob("セールスレター追記済み*.txt"))
                if sales_files:
                    print(f"📄 生成ファイル: {len(sales_files)}件")
                    for sales_file in sorted(sales_files):
                        size = sales_file.stat().st_size
                        print(f"   - {sales_file.name} ({size:,} bytes)")
            else:
                print(f"\n❌ セールスレター自動取得に失敗しました")
                
        except KeyboardInterrupt:
            print(f"\n⚠️ ユーザーによる中断")
        except Exception as e:
            print(f"❌ セールスレター自動取得エラー: {str(e)}")

    def daily_mail_automation_session(self):
        """デイリーメルマガ自動取得セッション"""
        print("\n" + "=" * 60)
        print("📧 デイリーメルマガ自動取得セッション開始")
        print("=" * 60)
        
        try:
            # データフォルダが存在するアカウントを確認
            base_path = Path("C:\\Users\\shiki\\AutoTweet\\data")
            
            if not base_path.exists():
                print("❌ データフォルダが見つかりません: C:\\Users\\shiki\\AutoTweet\\data")
                return
            
            # acc○○フォルダを検索
            acc_folders = [folder.name for folder in base_path.iterdir() 
                        if folder.is_dir() and folder.name.startswith('acc')]
            
            if not acc_folders:
                print("❌ 利用可能なアカウントフォルダが見つかりません")
                return
            
            acc_folders.sort()
            
            print(f"\n📋 利用可能なアカウント（フォルダ作成済み）:")
            for i, account_id in enumerate(acc_folders, 1):
                mail_folder = base_path / account_id / "デイリーメルマガ"
                existing_count = 0
                if mail_folder.exists():
                    for j in range(1, 8):
                        if (mail_folder / f"デイリーメルマガ{j}.txt").exists():
                            existing_count += 1
                print(f"  {i}. {account_id} (既存メルマガ: {existing_count}/7)")
            
            # アカウント選択
            while True:
                try:
                    choice = input(f"\nアカウントを選択してください (1-{len(acc_folders)}): ").strip()
                    choice_num = int(choice)
                    if 1 <= choice_num <= len(acc_folders):
                        selected_account = acc_folders[choice_num - 1]
                        break
                    else:
                        print(f"❌ 1-{len(acc_folders)}の数値を入力してください")
                except ValueError:
                    print("❌ 数値を入力してください")
                except KeyboardInterrupt:
                    return
            
            print(f"\n✅ 選択されたアカウント: {selected_account}")
            
            # 必要ファイル確認
            required_files = [
                "キャラクターコンセプト.txt",
                "ターゲット.txt",
                "市場リサーチ.txt"
            ]
            
            missing_files = []
            account_path = base_path / selected_account
            for filename in required_files:
                if not (account_path / filename).exists():
                    missing_files.append(filename)
            
            if missing_files:
                print(f"\n❌ 必要ファイルが見つかりません:")
                for filename in missing_files:
                    print(f"   - {account_path / filename}")
                return
            
            # 待機時間設定
            while True:
                try:
                    wait_input = input("\n待機時間を入力してください (デフォルト:45秒): ").strip()
                    wait_time = int(wait_input) if wait_input else 45
                    if wait_time > 0:
                        break
                    else:
                        print("❌ 1以上の数値を入力してください")
                except ValueError:
                    print("❌ 数値を入力してください")
            
            # 設定確認
            print(f"\n📋 実行設定確認:")
            print(f"   🎯 対象アカウント: {selected_account}")
            print(f"   ⏱️ 待機時間: {wait_time}秒")
            
            confirm = input(f"\n自動化を実行しますか？ (y/n): ")
            if confirm.lower() != 'y':
                print("🚫 実行をキャンセルしました")
                return
            
            print(f"\n🚀 デイリーメルマガ自動取得を開始します...")
            
            # カウントダウン
            for i in range(3, 0, -1):
                print(f"⏰ {i}秒後に開始...")
                time.sleep(1)
            
            # 実行
            success = self.daily_mail_automation.run_automation(selected_account, wait_time)
            
            if success:
                print(f"\n🎉 デイリーメルマガ自動取得完了！")
            else:
                print(f"\n❌ デイリーメルマガ自動取得に失敗しました")
        
        except KeyboardInterrupt:
            print(f"\n⚠️ ユーザーによる中断")
        except Exception as e:
            print(f"❌ デイリーメルマガ自動取得エラー: {str(e)}")
            import traceback
            traceback.print_exc()

    def myasp_mail_registration_session(self):
        """MyASPメルマガ登録セッション"""
        print("\n" + "=" * 60)
        print("📧 MyASPメルマガ登録セッション開始")
        print("=" * 60)
        
        try:
            # 7ファイル揃っているアカウントのみ取得
            available_accounts = self.myasp_automation.get_available_accounts()
            
            if not available_accounts:
                print("❌ 利用可能なアカウントがありません")
                print("   デイリーメルマガ1～7.txtが揃っているアカウントが必要です")
                return
            
            print(f"\n📋 利用可能なアカウント（デイリーメルマガ完備）:")
            account_list = list(available_accounts.keys())
            for i, (account_id, file_count) in enumerate(available_accounts.items(), 1):
                print(f"  {i}. {account_id} (7/7ファイル) ✅")
            
            # 複数アカウント選択
            print(f"\n対象アカウントを選択してください（複数可）:")
            print("  > 個別: 1,3,5 > 範囲: 1-5  > 全選択: all > 単一: 1")
            
            selected_accounts = []
            
            while True:
                selection = input(f"選択してください: ").strip()
                
                if selection.lower() == 'all':
                    selected_accounts = account_list.copy()
                    break
                elif ',' in selection:
                    try:
                        indices = [int(x.strip()) - 1 for x in selection.split(',')]
                        if all(0 <= i < len(account_list) for i in indices):
                            selected_accounts = [account_list[i] for i in indices]
                            break
                        else:
                            print("❌ 無効な番号が含まれています")
                    except ValueError:
                        print("❌ 数値を入力してください（例: 1,3,5）")
                elif '-' in selection:
                    try:
                        start, end = selection.split('-')
                        start_idx = int(start.strip()) - 1
                        end_idx = int(end.strip()) - 1
                        if 0 <= start_idx <= end_idx < len(account_list):
                            selected_accounts = account_list[start_idx:end_idx+1]
                            break
                        else:
                            print("❌ 無効な範囲です")
                    except ValueError:
                        print("❌ 正しい形式で入力してください（例: 1-5）")
                else:
                    try:
                        index = int(selection) - 1
                        if 0 <= index < len(account_list):
                            selected_accounts = [account_list[index]]
                            break
                        else:
                            print("❌ 無効な番号です")
                    except ValueError:
                        print("❌ 数値を入力してください")
            
            print(f"\n✅ 選択されたアカウント: {selected_accounts}")
            
            # 設定確認
            print(f"\n📋 実行設定確認:")
            print(f"   🎯 対象アカウント: {len(selected_accounts)}件")
            for account_id in selected_accounts:
                print(f"     - {account_id}")
            print(f"   📅 配信設定: 1～7日後の18時")
            print(f"   📝 処理内容: デイリーメルマガ登録")
            print(f"   🏷️ 完了後: ファイル名に'_マイスピー登録済み'追加")
            
            confirm = input(f"\nメルマガ登録を実行しますか？ (y/n): ")
            if confirm.lower() != 'y':
                print("🚫 実行をキャンセルしました")
                return
            
            print(f"\n🚀 MyASPメルマガ登録を開始します...")
            print(f"⚠️ 注意: 実行中はマウス・キーボードを操作しないでください")
            
            # カウントダウン
            for i in range(3, 0, -1):
                print(f"⏰ {i}秒後に開始...")
                time.sleep(1)
            
            # メルマガ登録実行
            results = self.myasp_automation.run_automation(selected_accounts)
            
            if results["success"] > 0:
                print(f"\n🎉 MyASPメルマガ登録完了！")
                print(f"成功: {results['success']}/{results['total']}アカウント")
            else:
                print(f"\n❌ MyASPメルマガ登録失敗")
                    
        except KeyboardInterrupt:
            print(f"\n⚠️ ユーザーによる中断")
        except Exception as e:
            print(f"❌ MyASPメルマガ登録エラー: {str(e)}")
            import traceback
            traceback.print_exc()

    def optin_page_session(self):
        """オプトインページ自動作成セッション"""
        print("\n" + "=" * 60)
        print("🎯 オプトインページ自動作成")
        print("=" * 60)
        
        try:
            # 自動実行（対話式でアカウント選択と待機時間入力）
            success = self.optin_automation.run_automation()
            
            if success:
                print("\n✅ オプトインページ作成が完了しました")
            else:
                print("\n⚠️ オプトインページ作成に失敗しました")
                
        except KeyboardInterrupt:
            print("\n⚠️ オプトインページ作成を中断しました")
        except Exception as e:
            print(f"\n❌ エラー: {str(e)}")
            self.logger.error(f"オプトインページ作成エラー: {str(e)}")

    # 以下既存のコード（待機時間設定、実行など）
    def emergency_cleanup(self):
        """緊急クリーンアップ"""
        print("\n" + "=" * 60)
        print("🆘 緊急クリーンアップ実行")
        print("=" * 60)
        
        try:
            # Chrome全終了
            print("🌐 全Chrome終了中...")
            self.chrome_manager.close_all_profiles()
            print("✅ Chrome終了")
            
            # VPN切断
            print("🔒 VPN切断中...")
            self.vpn_manager.disconnect()
            print("✅ VPN切断完了")
            
            print("🧹 緊急クリーンアップ完了")
            
        except Exception as e:
            print(f"❌ クリーンアップエラー: {str(e)}")
    
    def show_menu(self):
        """メインメニュー表示"""
        print("\n" + "=" * 60)
        print("🚀 Twitter自動化システム - メインメニュー")
        print("=" * 60)
        print("1. 🔧 システム動作確認")
        print("2. 📊 システム状態表示") 
        print("3. 📷 GPTツイート取得自動化")
        print("4. 🔄 Threads循環投稿")
        print("5. 📋 ログ確認")
        print("6. 🆘 緊急クリーンアップ")
        print("7. 📝 フロントエンドnote自動取得")
        print("8. 📄 フロントエンドnoteセールスレター自動取得")
        print("9. 📧 デイリーメルマガ自動取得")
        print("10.📧 MyASPメルマガ登録")
        print("11.🎯 オプトインページ自動作成")
        print("0. 🚪 終了")
        print("-" * 60)
        
        while True:
            try:
                choice = input("選択してください (0-11): ").strip() 
                if choice in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11']:
                    return choice
                else:
                    print("❌ 0-11 の数値を入力してください")
            except KeyboardInterrupt:
                return '0'
    
    def run(self):
        """メインループ"""
        print(f"\n🎉 Twitter自動化システム準備完了")
        
        try:
            while True:
                choice = self.show_menu()
                
                if choice == "1":
                    self.run_system_check()
                elif choice == "2":
                    self.show_status()
                elif choice == "3":
                    self.gpt_image_automation_session()
                elif choice == "4":
                    self.threads_rotation_session()
                elif choice == "5":
                    self.show_logs()
                elif choice == "6":
                    self.emergency_cleanup()
                elif choice == "7":
                    self.frontend_note_session()
                elif choice == "8":
                    self.frontend_salesletter_session()
                elif choice == "9":
                    self.daily_mail_automation_session()
                elif choice == "10":
                    self.myasp_mail_registration_session()
                elif choice == "11":
                    self.optin_page_session()

                elif choice == "0":
                    print("\n👋 システム終了")
                    break
                
                # メニュー間の区切り
                input(f"\nメニューに戻るには何かキーを押してください...")
                
        except KeyboardInterrupt:
            print(f"\n⚠️ システム中断")
        finally:
            # 最終クリーンアップ
            try:
                self.emergency_cleanup()
            except:
                pass

def main():
    """メイン実行"""
    try:
        print("🌟 Twitter自動化システム開始")
        print("-" * 60)
        
        # システム初期化
        system = TwitterAutomationSystem()
        
        # メインループ実行
        system.run()
        
    except KeyboardInterrupt:
        print(f"\n⚠️ システム中断")
    except Exception as e:
        print(f"❌ システムエラー: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        print(f"\n🏁 システム終了")

if __name__ == "__main__":
    main()