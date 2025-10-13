@echo off
chcp 65001 > nul
echo ===============================================
echo シンプルChrome完全削除
echo ===============================================
echo.
echo 警告: Chrome完全削除を実行します
echo.
set /p confirm="続行しますか？ (y/n): "
if /i not "%confirm%"=="y" exit /b

echo.
echo Step 1: Chromeプロセス終了
taskkill /f /im chrome.exe >nul 2>&1
taskkill /f /im GoogleCrashHandler.exe >nul 2>&1
taskkill /f /im GoogleCrashHandler64.exe >nul 2>&1
echo ✓ プロセス終了完了

echo.
echo Step 2: Chrome実行ファイル削除
rmdir /s /q "C:\Program Files\Google" >nul 2>&1
rmdir /s /q "C:\Program Files (x86)\Google" >nul 2>&1
echo ✓ 実行ファイル削除完了

echo.
echo Step 3: ユーザーデータ削除
rmdir /s /q "%LOCALAPPDATA%\Google" >nul 2>&1
rmdir /s /q "%APPDATA%\Google" >nul 2>&1
echo ✓ ユーザーデータ削除完了

echo.
echo Step 4: 一時ファイル削除
for /d %%i in ("%TEMP%\chrome*") do rmdir /s /q "%%i" >nul 2>&1
for %%i in ("%TEMP%\chrome*") do del /f /q "%%i" >nul 2>&1
echo ✓ 一時ファイル削除完了

echo.
echo Step 5: レジストリ削除
reg delete "HKEY_LOCAL_MACHINE\SOFTWARE\Google" /f >nul 2>&1
reg delete "HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\Google" /f >nul 2>&1
reg delete "HKEY_CURRENT_USER\Software\Google" /f >nul 2>&1
echo ✓ レジストリ削除完了

echo.
echo ===============================================
echo Chrome完全削除完了
echo ===============================================
echo.
echo 次の手順:
echo 1. PCを再起動
echo 2. Chrome新規インストール
echo.
set /p restart="今すぐ再起動しますか？ (y/n): "
if /i "%restart%"=="y" shutdown /r /t 5
pause