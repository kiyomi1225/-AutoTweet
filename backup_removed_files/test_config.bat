@echo off
chcp 65001 > nul
echo ===============================================
echo config_manager.py テスト実行
echo ===============================================

cd /d "C:\Users\shiki\AutoTweet"

echo.
echo ConfigManagerのテストを開始します...
echo.

python modules\config_manager.py

echo.
echo ===============================================
echo テスト完了！
echo ===============================================
echo.
echo 作成されたファイルを確認:
echo.

if exist "config\config.json" (
    echo ✓ config\config.json - 作成済み
    echo 内容の一部:
    type config\config.json | findstr /i "vpn\|chrome" | head -5
) else (
    echo ✗ config\config.json - 未作成
)

echo.

if exist "config\account_database.xlsx" (
    echo ✓ config\account_database.xlsx - 作成済み
) else (
    echo ✗ config\account_database.xlsx - 未作成
)

echo.
echo logs\ディレクトリのログを確認:
if exist "logs\*.log" (
    echo ✓ ログファイル存在
    dir logs\*.log
) else (
    echo ✗ ログファイル未作成
)

echo.
pause