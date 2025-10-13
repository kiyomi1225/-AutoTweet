# main.py - Twitter自動化システム メインエントリーポイント
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
        print("\n=== システム動作確認 ===")
        
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
                    
                    print("\n🎉 システム動作確認完了！")
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
        print("\n" + "="*50)
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
        print("\n=== 設定確認 ===")
        accounts = self.config.get_all_accounts()
        print(f"登録アカウント数: {len(accounts)}")
        for account_id in accounts:
            print(f"  - {account_id}")
    
    def show_logs(self):
        """ログ確認"""
        print("\n=== ログ確認 ===")
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
        print("\nシステム中断")
    except Exception as e:
        print(f"システムエラー: {str(e)}")

if __name__ == "__main__":
    main()
