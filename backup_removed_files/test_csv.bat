@echo off
chcp 65001 > nul
echo ===============================================
echo csv_manager.py テスト実行
echo ===============================================

cd /d "C:\Users\shiki\AutoTweet"

echo.
echo CSVManagerのテストを開始します...
echo.

python modules\csv_manager.py

echo.
echo ===============================================
echo テスト完了！
echo ===============================================
echo.
echo 作成されたファイルを確認:
echo.

if exist "data" (
    echo ✓ data ディレクトリ作成済み
    dir data /b
    echo.
    
    if exist "data\tweets_acc1.csv" (
        echo ✓ tweets_acc1.csv 作成済み
        echo 内容の確認:
        head -5 data\tweets_acc1.csv 2>nul
    )
    
    if exist "data\backup" (
        echo ✓ backup ディレクトリ作成済み
        dir data\backup /b
    )
) else (
    echo ✗ data ディレクトリ未作成
)

echo.
pause