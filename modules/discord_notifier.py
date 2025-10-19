# modules/discord_notifier.py - Discord通知モジュール
"""
Discord Webhook通知システム
システム開始/終了、重大エラー、アカウント処理完了を通知
"""

import requests
import json
from typing import Optional
from pathlib import Path

class DiscordNotifier:
    def __init__(self, webhook_url: Optional[str] = None):
        """
        Discord通知クラス
        
        Args:
            webhook_url: Discord Webhook URL（Noneの場合は設定ファイルから読み込み）
        """
        if webhook_url:
            self.webhook_url = webhook_url
        else:
            # 設定ファイルから読み込み
            config_path = Path("config/discord_config.json")
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.webhook_url = config.get("webhook_url")
            else:
                self.webhook_url = None
                print("⚠️ Discord Webhook URLが設定されていません")
        
        self.enabled = bool(self.webhook_url)
    
    def _send(self, content: str, embed: Optional[dict] = None) -> bool:
        """
        Discord通知を送信（内部メソッド）
        
        Args:
            content: メッセージ本文
            embed: リッチ埋め込み（オプション）
        
        Returns:
            送信成功ならTrue
        """
        if not self.enabled:
            return False
        
        try:
            data = {"content": content}
            if embed:
                data["embeds"] = [embed]
            
            response = requests.post(
                self.webhook_url,
                json=data,
                timeout=10
            )
            
            if response.status_code == 204:
                return True
            else:
                print(f"⚠️ Discord通知失敗: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"⚠️ Discord通知エラー: {str(e)}")
            return False
    
    # 🔴 必須通知
    
    def notify_system_start(self) -> bool:
        """システム開始通知"""
        return self._send("🚀 **システム開始**")
    
    def notify_system_end(self, summary: str = "") -> bool:
        """
        システム終了通知
        
        Args:
            summary: 処理サマリー（例：「2アカウント、12件収集」）
        """
        message = "🏁 **全処理完了**"
        if summary:
            message += f"\n{summary}"
        return self._send(message)
    
    def notify_critical_error(self, error_type: str, details: str = "") -> bool:
        """
        重大エラー通知
        
        Args:
            error_type: エラー種別（例：「VPN接続失敗」「Chrome起動失敗」）
            details: エラー詳細（オプション）
        """
        message = f"🔴 **重大エラー: {error_type}**"
        if details:
            message += f"\n```\n{details}\n```"
        return self._send(message)
    
    def notify_unexpected_stop(self, exception_info: str) -> bool:
        """
        予期しない停止通知
        
        Args:
            exception_info: 例外情報
        """
        message = f"⛔ **予期しない停止**\n```\n{exception_info}\n```"
        return self._send(message)
    
    # 🟡 推奨通知
    
    def notify_account_complete(self, account_id: str, item_count: int, action: str = "収集") -> bool:
        """
        各アカウント処理完了通知
        
        Args:
            account_id: アカウントID（例：「acc01」）
            item_count: 処理件数
            action: アクション名（例：「収集」「投稿」）
        """
        message = f"✅ **@{account_id}**: {item_count}件{action}完了"
        return self._send(message)


def test_discord_notifier():
    """Discord通知テスト"""
    print("=== Discord通知テスト ===\n")
    
    # Webhook URL入力
    webhook_url = input("Discord Webhook URLを入力してください: ").strip()
    
    if not webhook_url:
        print("❌ Webhook URLが入力されていません")
        return False
    
    notifier = DiscordNotifier(webhook_url)
    
    print("\n通知テスト実行中...\n")
    
    # 各種通知テスト
    print("1️⃣ システム開始通知")
    notifier.notify_system_start()
    input("   → Discordで確認したらEnterを押してください")
    
    print("\n2️⃣ アカウント処理完了通知")
    notifier.notify_account_complete("acc01", 5, "収集")
    input("   → Discordで確認したらEnterを押してください")
    
    print("\n3️⃣ 重大エラー通知")
    notifier.notify_critical_error("VPN接続失敗", "タイムアウト: 30秒")
    input("   → Discordで確認したらEnterを押してください")
    
    print("\n4️⃣ システム終了通知")
    notifier.notify_system_end("2アカウント、12件収集")
    input("   → Discordで確認したらEnterを押してください")
    
    print("\n✅ テスト完了！")
    return True


if __name__ == "__main__":
    test_discord_notifier()