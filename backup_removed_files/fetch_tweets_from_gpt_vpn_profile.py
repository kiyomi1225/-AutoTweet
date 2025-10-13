import time
import csv
import os
import pickle
import subprocess
import pyautogui
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# === 設定 ===
GPT_URL = "https://chatgpt.com/g/g-685aa726977081918c2166e6709e915b-ji-ke-tuitozuo-cheng-ai-lian-ai-xian-sheng"
CSV_FILE = r"DB/tweets_acc1.csv"
MAX_TWEETS = 50
WAIT_SECONDS = 60
VPN_CONFIG = r"C:/Program Files/OpenVPN/config/us4735.nordvpn.com.udp.ovpn"
AUTH_FILE = r"C:/Program Files/OpenVPN/config/auth.txt"
OPENVPN_PATH = r"C:\Program Files\OpenVPN\bin\openvpn.exe"

def connect_vpn():
    print("🔌 VPN接続中...")
    subprocess.call(f'start /B "" "{OPENVPN_PATH}" --config "{VPN_CONFIG}" --auth-user-pass "{AUTH_FILE}"', shell=True)
    time.sleep(20)

def disconnect_vpn():
    print("🔌 VPN切断中...")
    subprocess.call("taskkill /F /IM openvpn.exe", shell=True)
    time.sleep(5)

def save_tweets(tweets):
    os.makedirs(os.path.dirname(CSV_FILE), exist_ok=True)
    existing = []
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, newline='', encoding='utf-8') as f:
            existing = list(csv.reader(f))[1:]
    with open(CSV_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not existing:
            writer.writerow(["id", "text", "used"])
        start_id = len(existing) + 1
        for i, tweet in enumerate(tweets):
            writer.writerow([start_id + i, tweet.strip(), "False"])

def extract_tweets_from_output(text):
    exclusion_text = "「追加でツイート作成を依頼する場合は n を入力してください。」"
    lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
    return [line for line in lines if 0 < len(line) <= 140 and line != exclusion_text]

def get_current_tweet_count():
    if not os.path.exists(CSV_FILE):
        return 0
    with open(CSV_FILE, newline='', encoding='utf-8') as f:
        return sum(1 for _ in list(csv.reader(f))[1:])

def wait_for_reply(driver, timeout=30):
    for _ in range(timeout):
        outputs = driver.find_elements(By.CSS_SELECTOR, ".markdown.prose")
        if outputs:
            return outputs[-1].text
        time.sleep(1)
    return ""

def send_prompt(driver, text, timeout=20):
    try:
        WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.TAG_NAME, "textarea")))
        image_path = os.path.join("Images", "textarea.png") 
        location = pyautogui.locateCenterOnScreen(image_path, confidence=0.99)
        if location:
            pyautogui.click(location)
            time.sleep(0.3)
            pyautogui.typewrite(text)
            pyautogui.press('enter')
        else:
            raise Exception("入力欄の画像が見つかりません")
    except Exception as e:
        print(f"❌ メッセージ送信に失敗: {e}")
        driver.save_screenshot("error_screen.png")

def main():
    connect_vpn()
    
    options = uc.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--user-data-dir=C:\\Users\\%USERNAME%\\AppData\\Local\\Google\\Chrome\\User Data")
    options.add_argument("--profile-directory=acc1")
    driver = uc.Chrome(options=options)
    time.sleep(5)

    driver.get(GPT_URL)
    time.sleep(10)
    print("1")
    while get_current_tweet_count() < MAX_TWEETS:
        print("📥 n を送信中...")
        send_prompt(driver, "n")
        time.sleep(WAIT_SECONDS)
        output = wait_for_reply(driver)
        if not output:
            print("⚠️ 応答が見つかりません。リトライします。")
            continue
        tweets = extract_tweets_from_output(output)
        if not tweets:
            print("⚠️ 有効なツイートがありません。")
            continue
        save_tweets(tweets)
        print(f"✅ {len(tweets)}件保存 → 現在合計: {get_current_tweet_count()}件")
        time.sleep(10)

    print("🎉 " + MAX_TWEETS + "件以上のツイート案を保存しました！")
    driver.quit()
    disconnect_vpn()

if __name__ == "__main__":
    main()
