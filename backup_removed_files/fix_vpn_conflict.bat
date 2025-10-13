@echo off
chcp 65001 > nul
echo ===============================================
echo VPN競合問題修正
echo ===============================================

echo 管理者権限確認...
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo 管理者権限が必要です
    pause
    exit /b 1
)

echo.
echo 現在の状況:
echo - NordVPN専用ソフト: インストール済み
echo - OpenVPN単体: インストール済み
echo - 複数TAPアダプター: 競合中
echo.

echo [1] NordVPNサービス一時停止
echo NordVPN関連サービスを停止中...
sc stop NordVPN >nul 2>&1
sc stop NordVpnService >nul 2>&1
sc stop nordvpn-service >nul 2>&1
timeout /t 3 >nul

echo.
echo [2] NordVPN TAPアダプター一時無効化
echo ※OpenVPN用TAPアダプターとの競合を避けるため
powershell -Command "Get-NetAdapter | Where-Object {$_.InterfaceDescription -like '*NordVPN*'} | Disable-NetAdapter -Confirm:$false"

echo.
echo [3] OpenVPN用TAPアダプター確認・有効化
powershell -Command "Get-NetAdapter | Where-Object {$_.Name -eq 'MyOpenVPN' -or ($_.InterfaceDescription -like '*TAP-Windows*' -and $_.InterfaceDescription -notlike '*NordVPN*')} | Enable-NetAdapter -Confirm:$false"

echo.
echo [4] 修正後のTAPアダプター状態確認
powershell -Command "Get-NetAdapter | Where-Object {$_.InterfaceDescription -like '*TAP*'} | Format-Table Name, InterfaceDescription, Status"

echo.
echo [5] OpenVPN接続テスト実行
echo OpenVPN接続テスト中...
cd /d "C:\Users\shiki\AutoTweet"

python -c "
import sys
sys.path.append('.')
from modules.config_manager import ConfigManager
from modules.vpn_manager import VPNManager

print('OpenVPN接続テスト開始...')
config = ConfigManager()
vpn_manager = VPNManager(config)

# 短時間接続テスト
print('VPN接続中（20秒テスト）...')
success = vpn_manager.connect_account_vpn('acc1')

if success:
    print('✓ VPN接続成功')
    info = vpn_manager.get_connection_info()
    print(f'  元IP: {info[\"original_ip\"]}')
    print(f'  VPN IP: {info[\"current_ip\"]}')
    
    # 切断
    vpn_manager.disconnect()
    print('✓ VPN切断完了')
else:
    print('✗ VPN接続失敗')
"

echo.
echo ===============================================
echo 修正完了
echo ===============================================
echo.
echo 解決方法:
echo 1. OpenVPN用TAPアダプター優先設定
echo 2. NordVPN TAPアダプター一時無効化
echo 3. サービス競合回避
echo.
echo 次のステップ:
echo 1. python test_vpn_connection.py でVPN単体テスト
echo 2. python test_vpn_chrome.py で統合テスト
echo.
echo 注意: NordVPN専用ソフトを使いたい場合は
echo 手動でNordVPN TAPアダプターを再有効化してください
echo.
pause