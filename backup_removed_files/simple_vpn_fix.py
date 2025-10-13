# simple_vpn_fix.py - 簡易VPN修正
import subprocess
import time
import sys
from pathlib import Path
sys.path.append('.')

def test_simple_openvpn():
    """
    最もシンプルなOpenVPN接続テスト
    """
    print("=== 簡易OpenVPN接続テスト ===")
    
    # 最もシンプルなコマンド
    cmd = [
        r"C:\Program Files\OpenVPN\bin\openvpn.exe",
        "--config", "config/ovpn/us4735.nordvpn.com.udp.ovpn",
        "--auth-user-pass", "config/auth.txt",
        "--dev", "tun",
        "--verb", "1"
    ]
    
    print("実行コマンド:")
    print(" ".join(cmd))
    
    print(f"\nOpenVPN開始（10秒テスト）...")
    
    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # 10秒待機
        time.sleep(10)
        
        if process.poll() is None:
            print("✓ OpenVPN実行中")
            
            # 終了
            process.terminate()
            stdout, stderr = process.communicate(timeout=5)
            
            print("✓ OpenVPN終了")
            print(f"最後の出力: {stdout[-200:] if stdout else 'なし'}")
            
            return True
        else:
            stdout, stderr = process.communicate()
            print("✗ OpenVPN失敗")
            print(f"エラー: {stderr}")
            return False
            
    except Exception as e:
        print(f"✗ 実行エラー: {str(e)}")
        return False

def main():
    print("簡易VPN修正テストを開始します\n")
    
    # ファイル確認
    print("[確認] 必要ファイル存在確認:")
    
    files_to_check = [
        r"C:\Program Files\OpenVPN\bin\openvpn.exe",
        "config/ovpn/us4735.nordvpn.com.udp.ovpn", 
        "config/auth.txt"
    ]
    
    all_exists = True
    for file_path in files_to_check:
        if Path(file_path).exists():
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path}")
            all_exists = False
    
    if not all_exists:
        print("\n必要ファイルが不足しています")
        return
    
    # OpenVPNテスト
    result = test_simple_openvpn()
    
    if result:
        print("\n🎉 簡易テスト成功！")
        print("VPN基本機能は動作しています")
        print("\n次のテスト:")
        print("python test_vpn_connection.py")
    else:
        print("\n⚠ 簡易テストも失敗")
        print("OpenVPN設定に根本的な問題があります")

if __name__ == "__main__":
    main()