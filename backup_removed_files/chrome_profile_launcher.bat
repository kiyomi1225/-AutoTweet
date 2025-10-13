@echo off
chcp 65001 > nul
echo ===============================================
echo Chrome プロファイル起動
echo ===============================================

cd /d "C:\Users\shiki\AutoTweet"

echo プロファイルディレクトリ作成中...
if not exist "chrome_profiles" mkdir chrome_profiles
if not exist "chrome_profiles\acc1" mkdir chrome_profiles\acc1
if not exist "chrome_profiles\acc2" mkdir chrome_profiles\acc2

echo.
echo 起動するプロファイルを選択してください:
echo 1. acc1
echo 2. acc2
echo 3. カスタム
echo.
set /p choice="選択 (1-3): "

if "%choice%"=="1" (
    set "PROFILE=acc1"
) else if "%choice%"=="2" (
    set "PROFILE=acc2"
) else if "%choice%"=="3" (
    set /p PROFILE="プロファイル名を入力: "
    if not exist "chrome_profiles\%PROFILE%" mkdir "chrome_profiles\%PROFILE%"
) else (
    echo 無効な選択です
    pause
    exit /b
)

echo.
echo 開始URLを選択してください:
echo 1. Google (https://www.google.com)
echo 2. ChatGPT (https://chatgpt.com)  
echo 3. カスタムURL
echo 4. URLなし
echo.
set /p url_choice="選択 (1-4): "

if "%url_choice%"=="1" (
    set "URL=https://www.google.com"
) else if "%url_choice%"=="2" (
    set "URL=https://chatgpt.com"
) else if "%url_choice%"=="3" (
    set /p URL="URLを入力: "
) else (
    set "URL="
)

echo.
echo Chrome起動中...
echo プロファイル: %PROFILE%
echo URL: %URL%

REM Chrome起動コマンド
if "%URL%"=="" (
    "C:\Program Files\Google\Chrome\Application\chrome.exe" --user-data-dir="chrome_profiles" --profile-directory="%PROFILE%"
) else (
    "C:\Program Files\Google\Chrome\Application\chrome.exe" --user-data-dir="chrome_profiles" --profile-directory="%PROFILE%" "%URL%"
)

echo.
echo ✓ Chrome起動完了
echo.
echo 使用されたコマンド:
if "%URL%"=="" (
    echo "C:\Program Files\Google\Chrome\Application\chrome.exe" --user-data-dir="chrome_profiles" --profile-directory="%PROFILE%"
) else (
    echo "C:\Program Files\Google\Chrome\Application\chrome.exe" --user-data-dir="chrome_profiles" --profile-directory="%PROFILE%" "%URL%"
)

echo.
pause