# modules/content_pipeline.py - コンテンツ作成連続実行パイプライン
import time
from pathlib import Path
from typing import List, Tuple, Dict, Any

try:
    from .logger_setup import setup_module_logger
    from .optin_page_automation import OptinPageAutomation
    from .frontend_note_automation import FrontendNoteAutomation
    from .frontend_salesletter_automation import FrontendSalesletterAutomation
    from .daily_mail_automation import DailyMailAutomation
    from .myasp_mail_automation import MyASPMailAutomation
    from .gpt_image_automation import GPTImageAutomation
except ImportError:
    import sys
    sys.path.append('.')
    from modules.logger_setup import setup_module_logger
    from modules.optin_page_automation import OptinPageAutomation
    from modules.frontend_note_automation import FrontendNoteAutomation
    from modules.frontend_salesletter_automation import FrontendSalesletterAutomation
    from modules.daily_mail_automation import DailyMailAutomation
    from modules.myasp_mail_automation import MyASPMailAutomation
    from modules.gpt_image_automation import GPTImageAutomation


class ContentPipeline:
    """コンテンツ作成連続実行パイプライン"""
    
    # タスク定義
    TASKS = {
        1: {
            "name": "オプトインページ作成",
            "duration": "約3分",
            "required_files": ["キャラクターコンセプト.txt", "ターゲット.txt", "市場リサーチ.txt"],
            "dependencies": []
        },
        2: {
            "name": "フロントエンドnote作成",
            "duration": "約30分",
            "required_files": ["キャラクターコンセプト.txt", "ターゲット.txt", "市場リサーチ.txt"],
            "dependencies": []
        },
        3: {
            "name": "セールスレター作成",
            "duration": "約30分",
            "required_files": ["キャラクターコンセプト.txt", "ターゲット.txt", "市場リサーチ.txt"],
            "dependencies": [2]  # フロントエンドnote必須
        },
        4: {
            "name": "デイリーメルマガ作成",
            "duration": "約25分",
            "required_files": ["キャラクターコンセプト.txt", "ターゲット.txt", "市場リサーチ.txt"],
            "dependencies": []
        },
        5: {
            "name": "メルマガ登録",
            "duration": "約10分",
            "required_files": ["url_config.txt"],
            "dependencies": [4]  # デイリーメルマガ必須
        },
        6: {
            "name": "集客ツイート作成",
            "duration": "約90分",
            "required_files": ["キャラクターコンセプト.txt", "ターゲット.txt", "市場リサーチ.txt", "url_config.txt"],
            "dependencies": []
        }
    }
    
    def __init__(self, chrome_manager):
        """初期化"""
        self.logger = setup_module_logger("ContentPipeline")
        self.chrome_manager = chrome_manager
        
        # 各自動化モジュール初期化
        self.optin_automation = OptinPageAutomation(chrome_manager)
        self.frontend_note_automation = FrontendNoteAutomation(chrome_manager)
        self.salesletter_automation = FrontendSalesletterAutomation(chrome_manager)
        self.daily_mail_automation = DailyMailAutomation(chrome_manager)
        self.myasp_automation = MyASPMailAutomation()
        self.gpt_automation = GPTImageAutomation()
        
        self.logger.info("コンテンツ作成パイプライン初期化完了")
    
    def show_task_menu(self) -> List[int]:
        """タスク選択メニュー表示"""
        print("\n" + "━" * 60)
        print("📋 実行するタスクを選択してください")
        print("━" * 60)
        
        for task_id, task_info in self.TASKS.items():
            deps = ""
            if task_info["dependencies"]:
                dep_names = [self.TASKS[d]["name"] for d in task_info["dependencies"]]
                deps = f" [依存: {', '.join(dep_names)}]"
            print(f"  {task_id}. {task_info['name']:<20} ({task_info['duration']}){deps}")
        
        print("\n選択方法:")
        print("  - 個別: 1,3,5")
        print("  - 範囲: 1-4")
        print("  - 全部: all または 1-6")
        print("━" * 60)
        
        while True:
            try:
                user_input = input("\n実行するタスク番号: ").strip().lower()
                
                if not user_input:
                    print("⚠️ タスクを選択してください")
                    continue
                
                selected_tasks = self._parse_task_input(user_input)
                
                if not selected_tasks:
                    print("⚠️ 有効なタスクが選択されていません")
                    continue
                
                # 依存関係チェック・自動補完
                completed_tasks = self._resolve_dependencies(selected_tasks)
                
                # 確認表示
                if self._confirm_tasks(completed_tasks):
                    return completed_tasks
                
            except KeyboardInterrupt:
                print("\n\n❌ キャンセルしました")
                return []
            except Exception as e:
                print(f"⚠️ エラー: {str(e)}")
    
    def _parse_task_input(self, user_input: str) -> List[int]:
        """ユーザー入力をパース"""
        tasks = set()
        
        # "all" の場合
        if user_input == "all":
            return list(range(1, 7))
        
        # カンマで分割
        parts = user_input.split(',')
        
        for part in parts:
            part = part.strip()
            
            # 範囲指定（例: 1-4）
            if '-' in part:
                try:
                    start, end = part.split('-')
                    start_num = int(start.strip())
                    end_num = int(end.strip())
                    
                    if 1 <= start_num <= 6 and 1 <= end_num <= 6:
                        tasks.update(range(start_num, end_num + 1))
                    else:
                        print(f"⚠️ 範囲エラー: {part} (1-6の範囲で指定してください)")
                except ValueError:
                    print(f"⚠️ 無効な範囲: {part}")
            
            # 個別指定
            else:
                try:
                    task_num = int(part)
                    if 1 <= task_num <= 6:
                        tasks.add(task_num)
                    else:
                        print(f"⚠️ 無効な番号: {task_num} (1-6の範囲で指定してください)")
                except ValueError:
                    print(f"⚠️ 無効な入力: {part}")
        
        return sorted(list(tasks))
    
    def _resolve_dependencies(self, selected_tasks: List[int]) -> List[int]:
        """依存関係を解決して実行順序を決定"""
        resolved = set(selected_tasks)
        added_deps = []
        
        # 依存タスクを追加
        for task_id in selected_tasks:
            deps = self.TASKS[task_id]["dependencies"]
            for dep in deps:
                if dep not in resolved:
                    resolved.add(dep)
                    added_deps.append(dep)
        
        # 追加された依存タスクを表示
        if added_deps:
            print("\n⚠️ 依存関係により以下のタスクを自動追加:")
            for dep in added_deps:
                print(f"  + {dep}. {self.TASKS[dep]['name']}")
        
        # 実行順にソート（依存関係を考慮）
        return self._topological_sort(list(resolved))
    
    def _topological_sort(self, tasks: List[int]) -> List[int]:
        """トポロジカルソート（依存関係順）"""
        result = []
        visited = set()
        
        def visit(task_id):
            if task_id in visited:
                return
            visited.add(task_id)
            
            # 依存タスクを先に訪問
            for dep in self.TASKS[task_id]["dependencies"]:
                if dep in tasks:
                    visit(dep)
            
            result.append(task_id)
        
        for task_id in sorted(tasks):
            visit(task_id)
        
        return result
    
    def _confirm_tasks(self, tasks: List[int]) -> bool:
        """タスク実行確認"""
        print("\n✅ 選択されたタスク:")
        total_time = 0
        
        for task_id in tasks:
            task_info = self.TASKS[task_id]
            print(f"  {task_id}. {task_info['name']}")
            
            # 時間計算（簡易版）
            duration_str = task_info['duration']
            if "分" in duration_str:
                minutes = int(duration_str.replace("約", "").replace("分", ""))
                total_time += minutes
        
        print(f"\n推定所要時間: 約{total_time}分 ({total_time//60}時間{total_time%60}分)")
        
        confirm = input("\n実行しますか？ (y/n): ").strip().lower()
        return confirm == 'y'
    
    def run_pipeline(self, account_id: str, tasks: List[int]) -> bool:
        """パイプライン実行"""
        try:
            self.logger.info(f"パイプライン開始: {account_id}")
            self.logger.info(f"実行タスク: {tasks}")
            
            # 実行前ファイルチェック
            if not self._check_required_files(account_id, tasks):
                print("\n❌ 必須ファイルが不足しています")
                return False
            
            print("\n" + "=" * 60)
            print("🚀 パイプライン実行開始")
            print("=" * 60)
            print("⚠️ 実行中はPCを操作しないでください")
            
            # カウントダウン
            for i in range(5, 0, -1):
                print(f"⏰ {i}秒後に開始...")
                time.sleep(1)
            
            # 各タスクを順次実行
            for idx, task_id in enumerate(tasks, 1):
                task_info = self.TASKS[task_id]
                
                print("\n" + "=" * 60)
                print(f"📌 タスク {idx}/{len(tasks)}: {task_info['name']}")
                print("=" * 60)
                
                success = self._execute_task(task_id, account_id)
                
                if not success:
                    print(f"\n❌ タスク失敗: {task_info['name']}")
                    print("💔 パイプラインを停止します")
                    return False
                
                print(f"✅ タスク完了: {task_info['name']}")
                
                # 次タスクまで待機
                if idx < len(tasks):
                    print("\n⏳ 次のタスクまで10秒待機...")
                    time.sleep(10)
            
            print("\n" + "=" * 60)
            print("🎉 パイプライン完了！")
            print("=" * 60)
            self._show_results(account_id, tasks)
            
            return True
            
        except Exception as e:
            self.logger.error(f"パイプラインエラー: {str(e)}")
            print(f"\n❌ エラー発生: {str(e)}")
            return False
    
    def _check_required_files(self, account_id: str, tasks: List[int]) -> bool:
        """必須ファイルチェック"""
        print("\n🔍 必須ファイルチェック中...")
        
        base_path = Path(f"C:/Users/shiki/AutoTweet/data/{account_id}")
        
        # 全タスクの必須ファイルを収集
        required_files = set()
        for task_id in tasks:
            required_files.update(self.TASKS[task_id]["required_files"])
        
        # ファイル存在確認
        missing_files = []
        for filename in required_files:
            file_path = base_path / filename
            if not file_path.exists():
                missing_files.append(filename)
        
        if missing_files:
            print("\n❌ 以下のファイルが見つかりません:")
            for filename in missing_files:
                print(f"  - {base_path / filename}")
            return False
        
        print("✅ 必須ファイル確認完了")
        return True
    
    def _execute_task(self, task_id: int, account_id: str) -> bool:
        """個別タスク実行"""
        try:
            # デフォルトパラメータ
            wait_time = 90
            loop_count = 10
            target_count = 300
            
            if task_id == 1:
                # オプトインページ作成
                return self.optin_automation.run_automation(
                    account_id=account_id,
                    wait_time=wait_time
                )
            
            elif task_id == 2:
                # フロントエンドnote作成
                return self.frontend_note_automation.run_automation(
                    account_id=account_id,
                    wait_time=wait_time,
                    loop_count=loop_count
                )
            
            elif task_id == 3:
                # セールスレター作成
                return self.salesletter_automation.run_automation(
                    account_id=account_id,
                    wait_time=wait_time
                )
            
            elif task_id == 4:
                # デイリーメルマガ作成
                return self.daily_mail_automation.run_automation(
                    account_id=account_id,
                    wait_time=wait_time
                )
            
            elif task_id == 5:
                # メルマガ登録
                results = self.myasp_automation.run_automation([account_id])
                return results["success"] > 0
            
            elif task_id == 6:
                # 集客ツイート作成
                return self.gpt_automation.run_automation(
                    selected_accounts=[account_id],
                    wait_time=wait_time,
                    target_count=target_count
                )
            
            else:
                self.logger.error(f"未知のタスクID: {task_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"タスク実行エラー: {str(e)}")
            return False
    
    def _show_results(self, account_id: str, tasks: List[int]):
        """実行結果サマリー表示"""
        print("\n📊 実行結果:")
        
        base_path = Path(f"C:/Users/shiki/AutoTweet/data/{account_id}")
        
        for task_id in tasks:
            task_name = self.TASKS[task_id]["name"]
            
            if task_id == 1:
                file_path = base_path / "オプトインページ" / "オプトインページ.txt"
                if file_path.exists():
                    print(f"  ✅ {task_name}: {file_path}")
            
            elif task_id == 2:
                folder = base_path / "フロントエンドnote"
                if folder.exists():
                    files = list(folder.glob("フロントエンドnote*.txt"))
                    files = [f for f in files if "セールスレター追記済み" not in f.name]
                    print(f"  ✅ {task_name}: {len(files)}件作成")
            
            elif task_id == 3:
                folder = base_path / "フロントエンドnote"
                if folder.exists():
                    files = list(folder.glob("セールスレター追記済み*.txt"))
                    print(f"  ✅ {task_name}: {len(files)}件作成")
            
            elif task_id == 4:
                folder = base_path / "デイリーメルマガ"
                if folder.exists():
                    files = list(folder.glob("デイリーメルマガ*.txt"))
                    print(f"  ✅ {task_name}: {len(files)}件作成")
            
            elif task_id == 5:
                print(f"  ✅ {task_name}: MyASP登録完了")
            
            elif task_id == 6:
                csv_path = base_path / "tweets.csv"
                if csv_path.exists():
                    import csv
                    with open(csv_path, 'r', encoding='utf-8') as f:
                        reader = csv.reader(f)
                        next(reader)  # ヘッダースキップ
                        count = sum(1 for row in reader)
                    print(f"  ✅ {task_name}: {count}件作成")


# テスト関数
def test_content_pipeline():
    """テスト"""
    print("=== Content Pipeline テスト ===")
    
    try:
        from modules.chrome_manager import ChromeManager
        from modules.config_manager import ConfigManager
        
        config = ConfigManager()
        chrome_manager = ChromeManager(config)
        pipeline = ContentPipeline(chrome_manager)
        
        print("✓ 初期化成功")
        
        # タスク入力パーステスト
        test_inputs = ["1,3,5", "1-4", "all"]
        for inp in test_inputs:
            result = pipeline._parse_task_input(inp)
            print(f"✓ 入力テスト '{inp}': {result}")
        
        print("=== テスト完了 ===")
        return True
        
    except Exception as e:
        print(f"✗ テストエラー: {str(e)}")
        return False


if __name__ == "__main__":
    test_content_pipeline()
