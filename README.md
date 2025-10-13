# Twitter自動化システム

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
