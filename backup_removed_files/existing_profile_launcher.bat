@echo off
chcp 65001 > nul
echo ===============================================
echo Chrome 既存プロファイル起動
echo ===============================================

set "USER_DATA_DIR=C:\Users\shiki\AppData\Local\Google\Chrome\User Data"
set "CHROME_EXE=C:\Program Files\Google\Chrome\Application\chrome.exe"

echo 既存Chromeプロファイルディレクトリ: %USER_DATA_DIR%
echo.

echo 利用可能なプロファイル確認中...
if exist "%USER_DATA_DIR%\acc1" (
    echo ✓ acc1 プロファイル存在
) else (
    echo ⚠ acc1 プロファイル不在
)

if exist "%USER_DATA_DIR%\acc2" (
    echo ✓ acc2 プロファイル存在
) else (
    echo ⚠ acc2 プロファイル不在
)

if exist "%USER_DATA_DIR%\Default" (
    echo ✓ Default プロファイル存在
) else (
    echo ⚠ Default プロファイル不在
)

echo.
echo 起動するプロファイルを選択してください:
echo 1. acc1
echo 2. acc2
echo 3. Default
echo 4. カスタム
echo.
set /p choice="選択 (1-4): "

if "%choice%"=="1" (
    set "PROFILE=acc1"
) else if "%choice%"=="2" (
    set "PROFILE=acc2"
) else if "%choice%"=="3" (
    set "PROFILE=Default"
) else if "%choice%"=="4" (
    set /p PROFILE="プロファイル名を入力: "
) else (
    echo 無効な選択です
    pause
    exit /b
)

echo.
echo 開始URLを選択してください:
echo 1. Google (https://www.google.com)
echo 2. ChatGPT (https://chatgpt.com)
echo 3. IP確認 (https://whatismyipaddress.com)
echo 4. カスタムURL
echo 5. URLなし
echo.
set /p url_choice="選択 (1-5): "

if "%url_choice%"=="1" (
    set "URL=https://www.google.com"
) else if "%url_choice%"=="2" (
    set "URL=https://chatgpt.com"
) else if "%url_choice%"=="3" (
    set "URL=https://whatismyipaddress.com"
) else if "%url_choice%"=="4" (
    set /p URL="URLを入力: "
) else (
    set "URL="
)

echo.
echo ===============================================
echo Chrome起動実行
echo ===============================================
echo プロファイル: %PROFILE%
echo プロファイルパス: %USER_DATA_DIR%\%PROFILE%
echo URL: %URL%
echo.

REM 実際のコマンド表示
echo 実行コマンド:
if "%URL%"=="" (
    echo "%CHROME_EXE%" --user-data-dir="%USER_DATA_DIR%" --profile-directory="%PROFILE%"
) else (
    echo "%CHROME_EXE%" --user-data-dir="%USER_DATA_DIR%" --profile-directory="%PROFILE%" "%URL%"
)

echo.
echo Chrome起動中...

REM Chrome起動実行
if "%URL%"=="" (
    "%CHROME_EXE%" --user-data-dir="%USER_DATA_DIR%" --profile-directory="%PROFILE%"
) else (
    "%CHROME_EXE%" --user-data-dir="%USER_DATA_DIR%" --profile-directory="%PROFILE%" "%URL%"
)

if %errorlevel%==0 (
    echo ✓ Chrome起動完了
) else (
    echo ✗ Chrome起動エラー（コード: %errorlevel%）
)

echo.
pause