@echo off
chcp 65001 > nul
echo ===============================================
echo Chromeプロファイル問題修正
echo ===============================================

cd /d "C:\Users\shiki\AutoTweet"

echo.
echo [1] 全Chromeプロセス終了
taskkill /f /im chrome.exe >nul 2>&1
echo ✓ Chromeプロセス終了完了

echo.
echo [2] 問題のあるプロファイルディレクトリ削除
if exist "chrome_test_profiles" (
    echo chrome_test_profiles 削除中...
    rmdir /s /q "chrome_test_profiles" >nul 2>&1
    echo ✓ 削除完了
)

if exist "chrome_profiles" (
    echo chrome_profiles クリーンアップ中...
    rmdir /s /q "chrome_profiles" >nul 2>&1
    echo ✓ クリーンアップ完了
)

echo.
echo [3] 新しいプロファイルディレクトリ作成
mkdir "chrome_profiles" >nul 2>&1
mkdir "chrome_profiles\acc1" >nul 2>&1
mkdir "chrome_profiles\acc2" >nul 2>&1
echo ✓ プロファイルディレクトリ作成完了

echo.
echo [4] 権限設定
icacls "chrome_profiles" /grant "%USERNAME%:(OI)(CI)F" >nul 2>&1
echo ✓ 権限設定完了

echo.
echo ===============================================
echo 修復完了
echo ===============================================
echo.
echo 次のステップ:
echo 1. python chrome_browser_test.py で再テスト
echo 2. python test_vpn_chrome.py でVPN統合テスト
echo.
pause