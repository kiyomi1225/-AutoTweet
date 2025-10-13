@echo off
chcp 65001 > nul
echo ===============================================
echo TAPアダプター簡単確認
echo ===============================================

echo.
echo [1] 全ネットワークアダプター一覧
powershell -Command "Get-NetAdapter | Format-Table Name, InterfaceDescription, Status -AutoSize"

echo.
echo [2] TAPアダプター検索
powershell -Command "$tapAdapters = Get-NetAdapter | Where-Object {$_.InterfaceDescription -like '*TAP*' -or $_.InterfaceDescription -like '*OpenVPN*' -or $_.Name -like '*TAP*'}; if ($tapAdapters) { Write-Host '✓ TAPアダプター発見:'; $tapAdapters | Format-Table Name, InterfaceDescription, Status } else { Write-Host '✗ TAPアダプターが見つかりません' }"

echo.
echo [3] 無効なTAPアダプター確認
powershell -Command "$disabledTap = Get-NetAdapter | Where-Object {($_.InterfaceDescription -like '*TAP*' -or $_.InterfaceDescription -like '*OpenVPN*') -and $_.Status -eq 'Disabled'}; if ($disabledTap) { Write-Host '⚠ 無効なTAPアダプター:'; $disabledTap | Format-Table Name, Status } else { Write-Host '✓ 無効なTAPアダプターはありません' }"

echo.
echo [4] OpenVPNサービス状態確認
sc query OpenVPNService 2>nul | find "STATE"
sc query OpenVPNServiceInteractive 2>nul | find "STATE"

echo.
echo ===============================================
echo 対処法
echo ===============================================
echo.
echo TAPアダプターが見つからない場合:
echo A) OpenVPN再インストール（推奨）
echo B) デバイスマネージャーで手動確認
echo C) 別のVPNソフトがTAPアダプターを使用中の可能性
echo.
echo 無効なTAPアダプターがある場合:
echo powershell -Command "Get-NetAdapter | Where-Object {$_.InterfaceDescription -like '*TAP*' -and $_.Status -eq 'Disabled'} | Enable-NetAdapter -Confirm:$false"
echo.

set /p action="TAPアダプター修復を実行しますか？ (y/n): "
if /i "%action%"=="y" (
    echo.
    echo TAPアダプター有効化中...
    powershell -Command "Get-NetAdapter | Where-Object {($_.InterfaceDescription -like '*TAP*' -or $_.InterfaceDescription -like '*OpenVPN*') -and $_.Status -eq 'Disabled'} | Enable-NetAdapter -Confirm:$false"
    
    echo.
    echo 修復後の状態確認:
    powershell -Command "Get-NetAdapter | Where-Object {$_.InterfaceDescription -like '*TAP*' -or $_.InterfaceDescription -like '*OpenVPN*'} | Format-Table Name, InterfaceDescription, Status"
)

echo.
pause