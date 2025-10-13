@echo off
chcp 65001 > nul
echo ===============================================
echo システム環境詳細調査
echo ===============================================

echo.
echo [1] システム基本情報
echo OS情報:
systeminfo | findstr /B /C:"OS Name" /C:"OS Version"
echo.
echo プロセッサ情報:
wmic cpu get name
echo.
echo メモリ情報:
wmic computersystem get TotalPhysicalMemory
echo.

echo ===============================================
echo [2] ディスク容量確認
echo.
wmic logicaldisk get size,freespace,caption

echo.
echo ===============================================
echo [3] ネットワーク接続確認
echo.
echo Google接続テスト:
ping -n 3 8.8.8.8

echo.
echo ===============================================
echo [4] 実行中プロセス確認
echo.
echo Chromeプロセス:
tasklist | find /i "chrome"
if %errorlevel%==0 (
    echo ⚠ Chromeプロセスが実行中です
) else (
    echo ✓ Chromeプロセスは実行されていません
)

echo.
echo Googleプロセス:
tasklist | find /i "google"

echo.
echo ===============================================
echo [5] ファイアウォール・セキュリティ確認
echo.
echo Windows Defender状態:
powershell -Command "Get-MpComputerStatus | Select-Object AntivirusEnabled, RealTimeProtectionEnabled"

echo.
echo ファイアウォール状態:
netsh advfirewall show allprofiles state

echo.
echo ===============================================
echo [6] インストール済みブラウザ確認
echo.
echo Internet Explorer:
if exist "C:\Program Files\Internet Explorer\iexplore.exe" (
    echo ✓ IE存在
) else (
    echo ✗ IE不在
)

echo.
echo Microsoft Edge:
if exist "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" (
    echo ✓ Edge存在
) else (
    echo ✗ Edge不在
)

echo.
echo Firefox:
if exist "C:\Program Files\Mozilla Firefox\firefox.exe" (
    echo ✓ Firefox存在
) else if exist "C:\Program Files (x86)\Mozilla Firefox\firefox.exe" (
    echo ✓ Firefox存在
) else (
    echo ✗ Firefox不在
)

echo.
echo ===============================================
echo [7] レジストリ調査
echo.
echo Chrome関連レジストリ:
reg query "HKEY_LOCAL_MACHINE\SOFTWARE\Google" >nul 2>&1
if %errorlevel%==0 (
    echo ⚠ HKLM\SOFTWARE\Google存在
    reg query "HKEY_LOCAL_MACHINE\SOFTWARE\Google"
) else (
    echo ✓ HKLM\SOFTWARE\Google不在
)

echo.
reg query "HKEY_CURRENT_USER\Software\Google" >nul 2>&1
if %errorlevel%==0 (
    echo ⚠ HKCU\Software\Google存在
) else (
    echo ✓ HKCU\Software\Google不在
)

echo.
echo ===============================================
echo [8] 環境変数確認
echo.
echo PATH環境変数（Google関連）:
echo %PATH% | find /i "google"
if %errorlevel%==0 (
    echo ⚠ PATH環境変数にGoogle関連のパスが含まれています
) else (
    echo ✓ PATH環境変数にGoogle関連のパスはありません
)

echo.
echo TEMP ディレクトリ:
echo %TEMP%
dir "%TEMP%" | find /i "chrome"

echo.
echo ===============================================
echo [9] 権限テスト
echo.
echo 管理者権限確認:
net session >nul 2>&1
if %errorlevel%==0 (
    echo ✓ 管理者権限で実行中
) else (
    echo ⚠ 一般ユーザー権限で実行中
    echo   Chrome問題解決には管理者権限が必要な場合があります
)

echo.
echo ファイル作成権限テスト:
echo test > "%TEMP%\chrome_test.txt"
if exist "%TEMP%\chrome_test.txt" (
    echo ✓ ファイル作成権限OK
    del "%TEMP%\chrome_test.txt"
) else (
    echo ✗ ファイル作成権限NG
)

echo.
echo ===============================================
echo [10] イベントログ確認（直近のエラー）
echo.
echo 直近のアプリケーションエラー:
powershell -Command "Get-EventLog -LogName Application -EntryType Error -Newest 5 | Where-Object {$_.Source -like '*Chrome*' -or $_.Source -like '*Google*'} | Format-Table TimeGenerated, Source, Message -Wrap"

echo.
echo ===============================================
echo システム環境調査完了
echo ===============================================
echo.
echo この結果を保存しますか？
set /p save="診断結果をファイルに保存する場合は 'y' を入力: "
if /i "%save%"=="y" (
    echo システム診断結果をsystem_diagnosis.txtに保存中...
    call "%~f0" > system_diagnosis.txt 2>&1
    echo ✓ 保存完了: system_diagnosis.txt
)

echo.
pause