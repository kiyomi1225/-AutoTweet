# cleanup_project.py - プロジェクトファイル整理・クリーンアップ
import os
import shutil
from pathlib import Path

def analyze_current_files():
    """
    現在のファイル状況を分析
    """
    print("=== 現在のファイル状況分析 ===")
    
    # 必要なファイル（保持）
    essential_files = {
        "main.py": "メインエントリーポイント",
        "final_chrome_manager.py": "最終版Chrome管理（動作確認済み）",
        "requirements.txt": "依存関係",
        "README.md": "プロジェクト説明",
        ".gitignore": "Git設定"
    }
    
    # 必要なディレクトリ（保持）
    essential_dirs = {
        "modules/": "コアモジュール",
        "config/": "設定ファイル", 
        "data/": "データ保存",
        "logs/": "ログファイル"
    }
    
    # テスト・デバッグファイル（削除候補）
    test_debug_files = [
        "test_*.py",
        "debug_*.py", 
        "fix_*.py",
        "chrome_*.py",
        "vpn_*.py",
        "working_chrome_manager.py",
        "simple_*.py",
        "update_*.py",
        "safe_*.py",
        "*_test.py",
        "*_debug.py",
        "check_*.py",
        "verify_*.py"
    ]
    
    # 現在のファイル一覧
    current_files = []
    for file_path in Path(".").glob("*.py"):
        if file_path.is_file():
            current_files.append(file_path.name)
    
    print(f"\n現在のPythonファイル数: {len(current_files)}")
    
    # 分類
    keep_files = []
    delete_candidates = []
    
    for file in current_files:
        if file in essential_files:
            keep_files.append(file)
        else:
            # テスト・デバッグファイルかチェック
            is_test_debug = any(
                file.startswith(pattern.replace("*", "")) or 
                file.endswith(pattern.replace("*", "")) or
                pattern.replace("*", "") in file
                for pattern in test_debug_files
            )
            
            if is_test_debug:
                delete_candidates.append(file)
            else:
                keep_files.append(file)
    
    print(f"\n📁 保持するファイル ({len(keep_files)}個):")
    for file in sorted(keep_files):
        desc = essential_files.get(file, "その他の重要ファイル")
        print(f"  ✓ {file} - {desc}")
    
    print(f"\n🗑️ 削除候補ファイル ({len(delete_candidates)}個):")
    for file in sorted(delete_candidates):
        print(f"  ✗ {file}")
    
    return keep_files, delete_candidates

def create_backup_directory():
    """
    バックアップディレクトリ作成
    """
    backup_dir = Path("backup_removed_files")
    backup_dir.mkdir(exist_ok=True)
    print(f"✓ バックアップディレクトリ作成: {backup_dir}")
    return backup_dir

def cleanup_files(delete_candidates, backup_dir):
    """
    ファイルクリーンアップ実行
    """
    print(f"\n=== ファイルクリーンアップ実行 ===")
    
    if not delete_candidates:
        print("削除対象ファイルはありません")
        return
    
    print(f"削除対象: {len(delete_candidates)}個のファイル")
    print("バックアップしてから削除します")
    
    moved_count = 0
    error_count = 0
    
    for file in delete_candidates:
        try:
            source = Path(file)
            if source.exists():
                # バックアップディレクトリに移動
                destination = backup_dir / file
                shutil.move(str(source), str(destination))
                print(f"  ✓ {file} → backup/")
                moved_count += 1
            else:
                print(f"  ⚠ {file} が見つかりません")
        
        except Exception as e:
            print(f"  ✗ {file} 移動エラー: {e}")
            error_count += 1
    
    print(f"\n結果:")
    print(f"  移動完了: {moved_count}個")
    print(f"  エラー: {error_count}個")

def create_final_project_structure():
    """
    最終的なプロジェクト構造を作成
    """
    print(f"\n=== 最終プロジェクト構造作成 ===")
    
    # 最終版main.py作成
    main_py_content = '''# main.py - Twitter自動化システム メインエントリーポイント
"""
Twitter自動化システム
VPN + Chrome + GPT + Twitter投稿の統合システム
"""

import sys
import time
from pathlib import Path

# モジュールパス追加
sys.path.append('.')

# コアモジュールインポート
from modules.config_manager import ConfigManager
from modules.vpn_manager import VPNManager
from modules.csv_manager import CSVManager
from final_chrome_manager import FinalChromeManager

class TwitterAutomationSystem:
    """Twitter自動化システム メインクラス"""
    
    def __init__(self):
        """初期化"""
        print("=== Twitter自動化システム初期化 ===")
        
        self.config = ConfigManager()
        self.vpn_manager = VPNManager(self.config)
        self.chrome_manager = FinalChromeManager()
        self.csv_manager = CSVManager(self.config)
        
        print("✓ 全モジュール初期化完了")
    
    def run_system_check(self):
        """システム動作確認"""
        print("\\n=== システム動作確認 ===")
        
        try:
            # VPN接続テスト
            print("VPN接続テスト...")
            vpn_success = self.vpn_manager.connect_account_vpn("acc1")
            
            if vpn_success:
                info = self.vpn_manager.get_connection_info()
                print(f"✓ VPN接続成功: {info['current_ip']}")
                
                # Chrome起動テスト
                print("Chrome起動テスト...")
                chrome_success = self.chrome_manager.start_chrome("acc1", "https://www.google.com")
                
                if chrome_success:
                    print("✓ Chrome起動成功")
                    
                    time.sleep(5)
                    
                    # 終了処理
                    self.chrome_manager.close_chrome("acc1")
                    print("✓ Chrome終了完了")
                    
                    # VPN切断
                    self.vpn_manager.disconnect()
                    print("✓ VPN切断完了")
                    
                    print("\\n🎉 システム動作確認完了！")
                    return True
                else:
                    print("✗ Chrome起動失敗")
                    return False
            else:
                print("✗ VPN接続失敗")
                return False
                
        except Exception as e:
            print(f"✗ システムチェックエラー: {str(e)}")
            return False
    
    def show_menu(self):
        """メインメニュー表示"""
        print("\\n" + "="*50)
        print("Twitter自動化システム")
        print("="*50)
        print("1. システム動作確認")
        print("2. GPTツイート取得（手動）")
        print("3. 設定確認")
        print("4. ログ確認")
        print("0. 終了")
        print("-"*50)
        
        choice = input("選択してください (0-4): ")
        return choice
    
    def run(self):
        """メインループ"""
        print("Twitter自動化システム開始")
        
        while True:
            choice = self.show_menu()
            
            if choice == "1":
                self.run_system_check()
            elif choice == "2":
                print("GPTツイート取得機能は開発中です")
                print("simple_gpt_fetcher.py を使用してください")
            elif choice == "3":
                self.show_config()
            elif choice == "4":
                self.show_logs()
            elif choice == "0":
                print("システム終了")
                break
            else:
                print("無効な選択です")
    
    def show_config(self):
        """設定確認"""
        print("\\n=== 設定確認 ===")
        accounts = self.config.get_all_accounts()
        print(f"登録アカウント数: {len(accounts)}")
        for account_id in accounts:
            print(f"  - {account_id}")
    
    def show_logs(self):
        """ログ確認"""
        print("\\n=== ログ確認 ===")
        log_dir = Path("logs")
        if log_dir.exists():
            log_files = list(log_dir.glob("*.log"))
            print(f"ログファイル数: {len(log_files)}")
            for log_file in sorted(log_files)[-5:]:  # 最新5件
                print(f"  - {log_file.name}")
        else:
            print("ログディレクトリが見つかりません")

def main():
    """メイン実行"""
    try:
        system = TwitterAutomationSystem()
        system.run()
    except KeyboardInterrupt:
        print("\\nシステム中断")
    except Exception as e:
        print(f"システムエラー: {str(e)}")

if __name__ == "__main__":
    main()
'''
    
    with open("main.py", "w", encoding="utf-8") as f:
        f.write(main_py_content)
    
    print("✓ 最終版main.py作成完了")
    
    # README.md更新
    readme_content = '''# Twitter自動化システム

VPN + Chrome + GPT + Twitter投稿の統合自動化システム

## 🚀 機能

- **VPN自動接続**: NordVPN自動接続・切断
- **Chrome管理**: プロファイル分離でのブラウザ制御
- **GPT連携**: ChatGPTからのツイート自動取得
- **CSV管理**: ツイートデータの保存・管理

## 📁 プロジェクト構造

```
TwitterAutomation/
├── main.py                     # メインエントリーポイント
├── final_chrome_manager.py     # Chrome管理（最終版）
├── modules/                    # コアモジュール
│   ├── config_manager.py       # 設定管理
│   ├── vpn_manager.py         # VPN管理
│   ├── csv_manager.py         # CSV管理
│   └── logger_setup.py        # ログ設定
├── config/                     # 設定ファイル
│   ├── config.json            # システム設定
│   ├── accounts.json          # アカウント設定
│   └── ovpn/                  # VPN設定ファイル
├── data/                      # データ保存
│   └── tweets/                # ツイートCSV
└── logs/                      # ログファイル
```

## 🛠️ セットアップ

1. 依存関係インストール:
```bash
pip install -r requirements.txt
```

2. 設定ファイル準備:
- `config/config.json`: システム設定
- `config/accounts.json`: アカウント設定
- `config/auth.txt`: VPN認証情報
- `config/ovpn/`: VPNファイル配置

3. システム実行:
```bash
python main.py
```

## 📝 使用方法

1. **システム動作確認**: VPN + Chrome統合テスト
2. **GPTツイート取得**: ChatGPTからツイート生成
3. **CSV管理**: 生成ツイートの保存・管理

## 🎯 開発状況

- ✅ VPN管理システム
- ✅ Chrome管理システム  
- ✅ 基盤統合システム
- 🔄 GPTツイート取得（開発中）
- 📝 Twitter投稿自動化（予定）
'''
    
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)
    
    print("✓ README.md更新完了")

def main():
    print("プロジェクトファイル整理・クリーンアップを開始します\\n")
    
    # ファイル分析
    keep_files, delete_candidates = analyze_current_files()
    
    if delete_candidates:
        print(f"\\n削除候補ファイルがあります")
        confirm = input("バックアップしてクリーンアップを実行しますか？ (y/n): ")
        
        if confirm.lower() == 'y':
            # バックアップディレクトリ作成
            backup_dir = create_backup_directory()
            
            # ファイルクリーンアップ
            cleanup_files(delete_candidates, backup_dir)
            
            # 最終プロジェクト構造作成
            create_final_project_structure()
            
            print(f"\\n🎉 プロジェクトクリーンアップ完了！")
            print(f"\\n📁 整理後のプロジェクト:")
            print(f"  - 保持ファイル: {len(keep_files)}個")
            print(f"  - バックアップ: {len(delete_candidates)}個")
            print(f"  - メインエントリー: main.py")
            print(f"\\n次のステップ:")
            print(f"  python main.py でシステム実行")
        else:
            print("クリーンアップをキャンセルしました")
    else:
        print("削除対象ファイルはありません")
        
        # 最終プロジェクト構造作成
        create_final_project_structure()

if __name__ == "__main__":
    main()