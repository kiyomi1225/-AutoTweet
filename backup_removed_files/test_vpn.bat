@echo off
chcp 65001 > nul
echo ===============================================
echo vpn_manager.py テスト実行
echo ===============================================

cd /d "C:\Users\shiki\AutoTweet"

echo.
echo VPNManagerのテストを開始します...
echo ※実際のVPN接続は行いません
echo.

python modules\vpn_manager.py

echo.
echo ===============================================
echo 設定ファイル確認
echo ===============================================
echo.

if exist "config\auth.txt" (
    echo ✓ config\auth.txt - 存在
    echo 内容確認:
    type config\auth.txt
) else (
    echo ⚠ config\auth.txt - 未作成
    echo   VPN接続には認証情報が必要です
)

echo.

if exist "config\ovpn" (
    echo ✓ config\ovpn ディレクトリ - 存在
    echo VPNファイル一覧:
    dir config\ovpn\*.ovpn 2>nul | find ".ovpn"
    if errorlevel 1 echo   ⚠ VPNファイル(.ovpn)がありません
) else (
    echo ⚠ config\ovpn ディレクトリ - 未作成
    echo   VPNファイルの配置が必要です
)

echo.
echo ===============================================
echo OpenVPN確認
echo ===============================================

echo OpenVPNインストール状態:
where openvpn >nul 2>&1
if %errorlevel%==0 (
    echo ✓ OpenVPN - PATH環境変数で利用可能
    openvpn --version | head -1
) else (
    echo ⚠ OpenVPN - PATH環境変数で見つかりません
    
    if exist "C:\Program Files\OpenVPN\bin\openvpn.exe" (
        echo ✓ OpenVPN - インストール済み
        echo   パス: C:\Program Files\OpenVPN\bin\openvpn.exe
    ) else if exist "C:\Program Files (x86)\OpenVPN\bin\openvpn.exe" (
        echo ✓ OpenVPN - インストール済み
        echo   パス: C:\Program Files (x86)\OpenVPN\bin\openvpn.exe
    ) else (
        echo ✗ OpenVPN - 未インストール
        echo   https://openvpn.net/download-open-vpn/ からダウンロードしてください
    )
)

echo.
pause