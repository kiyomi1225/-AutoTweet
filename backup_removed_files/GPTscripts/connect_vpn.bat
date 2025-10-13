@echo off
REM OpenVPN GUIを管理者として実行（OpenVPNインストールパスは必要に応じて修正）
set OVPN_CONFIG=us4735.nordvpn.com.udp.ovpn

"C:\Program Files\OpenVPN\bin\openvpn.exe" --config "C:\Program Files\OpenVPN\config\%OVPN_CONFIG%" --auth-user-pass "C:\Program Files\OpenVPN\config\auth.txt"
