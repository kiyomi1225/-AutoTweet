
import csv
import random
import time
import os
import pyautogui
import pyperclip
import pickle
import subprocess
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

WAIT_RANGE = (180, 600)
CLOSE_BUTTON_IMAGE = "close_button.png"
TWEET_BOX_IMAGE = "tweet_box.png"
ACCOUNT_DB_FILE = "account_settings.csv"

def get_account_settings():
    df = pd.read_csv(ACCOUNT_DB_FILE)
    return df.to_dict(orient="records")

def get_next_tweet(csv_file):
    with open(csv_file, newline="", encoding="utf-8") as f:
        reader = list(csv.reader(f))
        header = reader[0]
        for row in reader[1:]:
            if row[2].strip().lower() == "false":
                return row[0], row[1]
    return None, None

def mark_tweet_as_used(csv_file, tweet_id):
    rows = []
    with open(csv_file, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            if row[0] == tweet_id:
                row[2] = "True"
            rows.append(row)
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "tweet", "used"])
        writer.writerows(rows)

def connect_vpn(ovpn_path):
    print(f"🌐 VPN接続中... ({ovpn_path})")
    subprocess.run(["taskkill", "/f", "/im", "openvpn.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2)
    subprocess.Popen(["openvpn", "--config", ovpn_path, "--auth-user-pass", "auth.txt"])
    time.sleep(10)

def disconnect_vpn():
    subprocess.run(["taskkill", "/f", "/im", "openvpn.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2)

def load_cookies(driver, cookie_file):
    if not os.path.exists(cookie_file):
        print(f"❌ Cookieファイルが見つかりません: {cookie_file}")
        return
    driver.get("https://twitter.com/home")
    time.sleep(3)
    with open(cookie_file, "rb") as f:
        cookies = pickle.load(f)
        for cookie in cookies:
            try:
                driver.add_cookie(cookie)
            except Exception as e:
                print(f"⚠️ Cookie追加失敗: {cookie.get('name')} → {e}")
    driver.refresh()
    time.sleep(5)

def close_login_modal_gui():
    print("🔍 モーダル検出中...")
    close_btn = pyautogui.locateCenterOnScreen(CLOSE_BUTTON_IMAGE, confidence=0.8)
    if close_btn:
        pyautogui.click(close_btn)
        print("✅ モーダルを閉じました")
        time.sleep(2)

def post_tweet_gui(tweet):
    print(f"📥 ツイート中: {tweet[:40]}...")
    box = pyautogui.locateCenterOnScreen(TWEET_BOX_IMAGE, confidence=0.8)
    if not box:
        print("❌ ツイート欄が見つかりません")
        return False
    pyautogui.click(box)
    time.sleep(1)
    pyperclip.copy(tweet)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(1)
    pyautogui.hotkey("ctrl", "enter")
    print("✅ ツイート送信完了")
    return True

def run_for_account(account):
    print(f"🚀 アカウント{account['id']}で処理開始")

    # VPN切替
    disconnect_vpn()
    connect_vpn(account["vpn_file"])

    # Chrome起動（プロファイル指定）
    chrome_options = Options()
    chrome_options.add_argument(f"--user-data-dir={account['chrome_profile']}")
    chrome_options.add_argument("--start-maximized")
    driver = webdriver.Chrome(options=chrome_options)

    try:
        driver.get("https://twitter.com/home")
        time.sleep(5)
        load_cookies(driver, account["cookie_file"])
        close_login_modal_gui()

        tweet_id, tweet_text = get_next_tweet(account["csv_file"])
        if not tweet_text:
            print("⚠️ 有効なツイートがありません。")
            return

        if post_tweet_gui(tweet_text):
            mark_tweet_as_used(account["csv_file"], tweet_id)
    finally:
        driver.quit()

def main():
    accounts = get_account_settings()
    while True:
        for account in accounts:
            run_for_account(account)
            wait = random.randint(*WAIT_RANGE)
            print(f"⏳ 次のアカウントまで {wait} 秒待機...")
            time.sleep(wait)

if __name__ == "__main__":
    main()
