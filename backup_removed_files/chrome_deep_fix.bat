@echo off
chcp 65001 > nul
echo ===============================================
echo Chrome深層修復スクリプト
echo ===============================================
echo.
echo このスクリプトはChrome invalid_optionエラーを解決します
echo 複数の修復手法を順番に試行します
echo.
set /p confirm="続行しますか？ (y/n): "
if /i not "%confirm%"=="y" exit /b

echo.
echo ===============================================
echo Phase 1: システム診断
echo ===============================================

echo.
echo [1.1] Windows バージョン詳細確認
ver
systeminfo | findstr /B /C:"OS Name" /C:"OS Version" /C:"System Type"

echo.
echo [1.2] 管理者権限確認
net session >nul 2>&1
if %errorlevel%==0 (
    echo ✓ 管理者権限で実行中
) else (
    echo ✗ 管理者権限が必要です
    pause
    exit /b 1
)

echo.
echo [1.3] Windows Installer サービス確認
sc query msiserver | find "STATE"
sc query msiserver | find "RUNNING" >nul 2>&1
if %errorlevel%==0 (
    echo ✓ Windows Installer サービス実行中
) else (
    echo ⚠ Windows Installer サービス停止中
    echo サービス開始を試行します...
    sc start msiserver >nul 2>&1
    timeout /t 3 >nul
)

echo.
echo [1.4] TrustedInstaller サービス確認
sc query trustedinstaller | find "STATE"

echo.
echo ===============================================
echo Phase 2: Chrome関連の完全クリーンアップ
echo ===============================================

echo.
echo [2.1] 全Chromeプロセス終了
taskkill /f /im chrome.exe >nul 2>&1
taskkill /f /im GoogleCrashHandler.exe >nul 2>&1
taskkill /f /im GoogleCrashHandler64.exe >nul 2>&1
taskkill /f /im GoogleUpdate.exe >nul 2>&1
echo ✓ Chromeプロセス終了完了

echo.
echo [2.2] Chrome関連サービス停止
sc stop gupdate >nul 2>&1
sc stop gupdatem >nul 2>&1
echo ✓ Chromeサービス停止完了

echo.
echo [2.3] Chrome完全削除
rmdir /s /q "C:\Program Files\Google" >nul 2>&1
rmdir /s /q "C:\Program Files (x86)\Google" >nul 2>&1
rmdir /s /q "%LOCALAPPDATA%\Google" >nul 2>&1
rmdir /s /q "%APPDATA%\Google" >nul 2>&1

echo.
echo [2.4] Chrome一時ファイル削除
for /d %%i in ("%TEMP%\chrome*") do rmdir /s /q "%%i" >nul 2>&1
for %%i in ("%TEMP%\chrome*") do del /f /q "%%i" >nul 2>&1
for %%i in ("%TEMP%\Chrome*") do del /f /q "%%i" >nul 2>&1

echo.
echo [2.5] Chromeレジストリ削除
reg delete "HKEY_LOCAL_MACHINE\SOFTWARE\Google" /f >nul 2>&1
reg delete "HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\Google" /f >nul 2>&1
reg delete "HKEY_CURRENT_USER\Software\Google" /f >nul 2>&1
reg delete "HKEY_CLASSES_ROOT\ChromeHTML" /f >nul 2>&1
reg delete "HKEY_CURRENT_USER\Software\Classes\ChromeHTML" /f >nul 2>&1
echo ✓ Chromeレジストリ削除完了

echo.
echo ===============================================
echo Phase 3: システム修復
echo ===============================================

echo.
echo [3.1] Windows Updateコンポーネント修復
echo SFC（システムファイルチェッカー）実行中...
sfc /scannow
echo ✓ SFC完了

echo.
echo [3.2] DISM修復実行中...
dism /online /cleanup-image /restorehealth
echo ✓ DISM修復完了

echo.
echo [3.3] Windows Installer修復
echo Windows Installer キャッシュクリア中...
rmdir /s /q "%WINDIR%\Installer\$PatchCache$" >nul 2>&1
echo ✓ Windows Installer修復完了

echo.
echo ===============================================
echo Phase 4: 代替Chrome取得・インストール
echo ===============================================

echo.
echo [4.1] 複数ソースからChromeダウンロード試行

REM 方法1: 公式サイト
echo 方法1: Google公式サイトから取得中...
powershell -Command "try { (New-Object System.Net.WebClient).DownloadFile('https://dl.google.com/chrome/install/ChromeStandaloneSetup64.exe', '%TEMP%\Chrome_Official.exe') } catch { Write-Host 'エラー' }"

REM 方法2: 別URL
echo 方法2: 代替URLから取得中...
powershell -Command "try { (New-Object System.Net.WebClient).DownloadFile('https://dl.google.com/chrome/install/standalone/ChromeStandaloneSetup64.exe', '%TEMP%\Chrome_Alt.exe') } catch { Write-Host 'エラー' }"

REM 方法3: curl
echo 方法3: curlで取得中...
curl -L -o "%TEMP%\Chrome_Curl.exe" "https://dl.google.com/chrome/install/ChromeStandaloneSetup64.exe" >nul 2>&1

echo.
echo [4.2] ダウンロード結果確認
set "INSTALLER_COUNT=0"

if exist "%TEMP%\Chrome_Official.exe" (
    echo ✓ 公式URL: %TEMP%\Chrome_Official.exe
    set /a INSTALLER_COUNT+=1
    set "BEST_INSTALLER=%TEMP%\Chrome_Official.exe"
)

if exist "%TEMP%\Chrome_Alt.exe" (
    echo ✓ 代替URL: %TEMP%\Chrome_Alt.exe
    set /a INSTALLER_COUNT+=1
    set "BEST_INSTALLER=%TEMP%\Chrome_Alt.exe"
)

if exist "%TEMP%\Chrome_Curl.exe" (
    echo ✓ curl: %TEMP%\Chrome_Curl.exe
    set /a INSTALLER_COUNT+=1
    set "BEST_INSTALLER=%TEMP%\Chrome_Curl.exe"
)

if %INSTALLER_COUNT%==0 (
    echo ✗ 全てのダウンロードが失敗しました
    goto :manual_download
)

echo 利用可能なインストーラー数: %INSTALLER_COUNT%
echo 使用するインストーラー: %BEST_INSTALLER%

echo.
echo [4.3] Chrome管理者インストール実行
echo.
echo インストール方法選択:
echo 1. msiexec使用（最も安全）
echo 2. 直接実行（標準）
echo 3. PowerShell実行
echo 4. 手動実行
echo.
set /p install_choice="選択 (1-4): "

if "%install_choice%"=="1" goto :msi_install
if "%install_choice%"=="2" goto :direct_install
if "%install_choice%"=="3" goto :powershell_install
if "%install_choice%"=="4" goto :manual_install

:msi_install
echo MSIEXECでインストール中...
msiexec /i "%BEST_INSTALLER%" /quiet /norestart
goto :check_install

:direct_install
echo 直接実行でインストール中...
"%BEST_INSTALLER%" /silent /install
goto :check_install

:powershell_install
echo PowerShellでインストール中...
powershell -Command "Start-Process -FilePath '%BEST_INSTALLER%' -ArgumentList '/silent /install' -Wait -Verb RunAs"
goto :check_install

:manual_install
echo 手動インストール実行...
echo インストーラーを管理者として実行します
echo ※ウィザードが表示されたら手動で進めてください
"%BEST_INSTALLER%"
pause
goto :check_install

:check_install
echo.
echo [4.4] インストール確認
timeout /t 10 >nul

if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    echo ✓ Chrome 64bit インストール成功
    set "CHROME_PATH=C:\Program Files\Google\Chrome\Application\chrome.exe"
    goto :success_install
) else if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" (
    echo ✓ Chrome 32bit インストール成功
    set "CHROME_PATH=C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
    goto :success_install
) else (
    echo ✗ Chromeインストール確認できません
    goto :install_failed
)

:success_install
echo.
echo ===============================================
echo Chrome深層修復成功！
echo ===============================================
echo Chrome実行パス: %CHROME_PATH%

echo.
echo [5] Chrome動作確認
"%CHROME_PATH%" --version
if %errorlevel%==0 (
    echo ✓ Chrome --version 成功
) else (
    echo ⚠ Chrome --version エラー（動作は可能な場合があります）
)

echo.
echo Chrome起動テスト...
start /min "" "%CHROME_PATH%" --no-sandbox --disable-gpu "https://www.google.com"
timeout /t 5 >nul

tasklist | find /i "chrome.exe" >nul 2>&1
if %errorlevel%==0 (
    echo ✓ Chrome起動テスト成功
    taskkill /f /im chrome.exe >nul 2>&1
) else (
    echo ⚠ Chrome起動テスト失敗
)

echo.
echo 推奨次ステップ:
echo 1. python debug_chrome.py
echo 2. python test_vpn_chrome.py
goto :cleanup

:install_failed
echo.
echo ===============================================
echo インストール失敗の場合
echo ===============================================
echo.
echo 追加対処法:
echo 1. PC再起動後に再実行
echo 2. セーフモードでの実行
echo 3. 別のユーザーアカウントで実行
echo 4. Windows 11の互換性設定調整

:manual_download
echo.
echo ===============================================
echo 手動ダウンロード案内
echo ===============================================
echo.
echo 自動ダウンロードが全て失敗しました
echo.
echo 手動手順:
echo 1. Microsoft Edgeを開く
echo 2. https://www.google.com/chrome/ にアクセス
echo 3. Chromeをダウンロード
echo 4. ダウンロードファイルを右クリック→管理者として実行

:cleanup
echo.
echo [6] クリーンアップ
for %%f in ("%TEMP%\Chrome_*.exe") do del "%%f" >nul 2>&1
echo ✓ 一時ファイル削除完了

echo.
pause