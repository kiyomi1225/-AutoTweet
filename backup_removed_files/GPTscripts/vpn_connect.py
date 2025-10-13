import subprocess
import time
import requests

# VPN実行用のバッチファイルパス
BATCH_FILE = "connect_vpn.bat"

# 接続後に期待するVPNサーバーの国（IPで識別）
EXPECTED_COUNTRY = "United States"  # 必要なら "Japan" 等に変更

def get_ip_info():
    try:
        response = requests.get("http://ip-api.com/json", timeout=10)
        return response.json()
    except Exception as e:
        print(f"❌ IP取得失敗: {e}")
        return {}

def is_vpn_connected():
    info = get_ip_info()
    country = info.get("country", "不明")
    ip = info.get("query", "不明")
    print(f"🌍 現在のIP: {ip} / 国: {country}")
    return country == EXPECTED_COUNTRY

def connect_vpn():
    print("🔌 VPN接続バッチを実行します...")
    process = subprocess.Popen(BATCH_FILE, shell=True)
    print("⏳ VPN接続を待機中...")
    time.sleep(10)

    for _ in range(6):  # 最大60秒待つ
        if is_vpn_connected():
            print("✅ VPN接続成功！")
            return True
        print("🔁 VPN接続確認中...")
        time.sleep(10)

    print("❌ VPN接続に失敗しました。")
    return False

if __name__ == "__main__":
    if connect_vpn():
        print("🎯 ここから後続処理を続行できます")
    else:
        print("⚠ 終了します")
