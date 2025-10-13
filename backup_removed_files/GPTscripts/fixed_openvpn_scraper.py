import time
import csv
import os
import subprocess
import pyautogui
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# === 設定 ===
GPT_URL = "https://chatgpt.com/g/g-685aa726977081918c2166e6709e915b-ji-ke-tuitozuo-cheng-ai-lian-ai-xian-sheng"
MAX_TWEETS = 50
WAIT_SECONDS = 60

# アカウント毎のVPN設定
VPN_CONFIGS = {
    "acc1": {
        "config": "C:/Program Files/OpenVPN/config/us4735.nordvpn.com.udp.ovpn",
        "auth": "C:/Program Files/OpenVPN/config/auth.txt",
        "csv": "DB/tweets_acc1.csv"
    },
    "acc2": {
        "config": "C:/Program Files/OpenVPN/config/uk2156.nordvpn.com.udp.ovpn", 
        "auth": "C:/Program Files/OpenVPN/config/auth2.txt",
        "csv": "DB/tweets_acc2.csv"
    },
    "acc3": {
        "config": "C:/Program Files/OpenVPN/config/jp890.nordvpn.com.udp.ovpn",
        "auth": "C:/Program Files/OpenVPN/config/auth3.txt", 
        "csv": "DB/tweets_acc3.csv"
    }
}

def check_openvpn_availability():
    """OpenVPNの利用可能性をチェック"""
    openvpn_paths = [
        "C:/Program Files/OpenVPN/bin/openvpn.exe",
        "C:/Program Files (x86)/OpenVPN/bin/openvpn.exe"
    ]
    
    for path in openvpn_paths:
        if os.path.exists(path):
            return path
    return None

def get_account_choice():
    """アカウント選択"""
    print("📋 使用するアカウントを選択してください:")
    for acc_name in VPN_CONFIGS.keys():
        config_path = VPN_CONFIGS[acc_name]["config"]
        config_exists = "✅" if os.path.exists(config_path) else "❌"
        print(f"  {acc_name}: {config_exists} {os.path.basename(config_path)}")
    
    while True:
        choice = input("アカウント名を入力 (例: acc1): ").strip()
        if choice in VPN_CONFIGS:
            return choice
        print("❌ 無効なアカウント名です。再入力してください。")

def connect_openvpn_with_config(config_file, auth_file=None):
    """指定された設定ファイルでOpenVPN接続"""
    try:
        print(f"🔌 OpenVPN接続中: {os.path.basename(config_file)}")
        
        # OpenVPNのパスを取得
        openvpn_exe = check_openvpn_availability()
        if not openvpn_exe:
            print("❌ OpenVPNが見つかりません")
            print("OpenVPNをインストールしてください: https://openvpn.net/community-downloads/")
            return False, None
        
        # 設定ファイルの確認
        if not os.path.exists(config_file):
            print(f"❌ 設定ファイルが見つかりません: {config_file}")
            return False, None
        
        # 認証ファイルの確認（指定されている場合）
        if auth_file and not os.path.exists(auth_file):
            print(f"❌ 認証ファイルが見つかりません: {auth_file}")
            return False, None
        
        # 既存のOpenVPNプロセスを終了
        try:
            subprocess.run("taskkill /F /IM openvpn.exe", shell=True, stderr=subprocess.DEVNULL)
            time.sleep(2)
            print("🔄 既存のOpenVPN接続を終了しました")
        except:
            pass
        
        # コマンド構築
        if auth_file:
            cmd = f'"{openvpn_exe}" --config "{config_file}" --auth-user-pass "{auth_file}"'
        else:
            cmd = f'"{openvpn_exe}" --config "{config_file}"'
        
        print(f"実行コマンド: {cmd}")
        
        # 非同期で実行
        process = subprocess.Popen(cmd, shell=True, 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE,
                                 creationflags=subprocess.CREATE_NEW_CONSOLE)
        
        # 接続確認（最大60秒待機）
        print("⏳ VPN接続を確認中...")
        for i in range(60):
            time.sleep(1)
            
            # プロセスが生きているかチェック
            if process.poll() is not None:
                print("❌ OpenVPNプロセスが終了しました")
                try:
                    stdout, stderr = process.communicate(timeout=1)
                    if stdout:
                        print(f"出力: {stdout.decode('utf-8', errors='ignore')}")
                    if stderr:
                        print(f"エラー: {stderr.decode('utf-8', errors='ignore')}")
                except:
                    pass
                return False, None
            
            # tasklist でプロセス確認
            result = subprocess.run("tasklist /FI \"IMAGENAME eq openvpn.exe\"", 
                                  shell=True, capture_output=True, text=True)
            if "openvpn.exe" in result.stdout:
                # 接続確認のため少し待つ
                if i > 10:  # 10秒後から接続成功とみなす
                    print("✅ OpenVPN接続成功")
                    return True, process
            
            if i % 10 == 0 and i > 0:
                print(f"⏳ 接続確認中... ({i}/60秒)")
        
        print("❌ OpenVPN接続タイムアウト")
        try:
            process.terminate()
        except:
            pass
        return False, None
        
    except Exception as e:
        print(f"❌ OpenVPN接続エラー: {e}")
        return False, None

def disconnect_openvpn():
    """OpenVPN切断"""
    try:
        print("🔌 OpenVPN切断中...")
        subprocess.run("taskkill /F /IM openvpn.exe", shell=True, stderr=subprocess.DEVNULL)
        time.sleep(3)
        print("✅ OpenVPN切断完了")
    except Exception as e:
        print(f"⚠️ OpenVPN切断エラー: {e}")

def save_tweets(tweets, csv_file):
    """ツイートをCSVに保存"""
    os.makedirs(os.path.dirname(csv_file), exist_ok=True)
    existing = []
    if os.path.exists(csv_file):
        with open(csv_file, newline='', encoding='utf-8') as f:
            existing = list(csv.reader(f))[1:]  # ヘッダーをスキップ
    
    with open(csv_file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not existing:
            writer.writerow(["id", "text", "used"])
        start_id = len(existing) + 1
        for i, tweet in enumerate(tweets):
            writer.writerow([start_id + i, tweet.strip(), "False"])

def extract_tweets_from_output(text):
    """GPT出力からツイート案を抽出"""
    exclusions = [
        "「追加でツイート作成を依頼する場合は n を入力してください。」",
        "追加でツイート作成を依頼する場合は n を入力してください",
        "何か他にお手伝いできることはありますか",
        "どのような内容にしますか",
        "以下のツイート案はいかがでしょうか"
    ]
    
    lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
    tweets = []
    
    for line in lines:
        # 140文字以内で、除外パターンに該当しないもの
        if (0 < len(line) <= 140 and 
            not any(exc in line for exc in exclusions) and
            not line.startswith(('###', '**', '1.', '2.', '3.', '4.', '5.', '・', '－'))):
            tweets.append(line)
    
    return tweets[:10]  # 最大10件まで

def get_current_tweet_count(csv_file):
    """現在のツイート数を取得"""
    if not os.path.exists(csv_file):
        return 0
    with open(csv_file, newline='', encoding='utf-8') as f:
        return sum(1 for _ in list(csv.reader(f))[1:])  # ヘッダーをスキップ

def wait_for_reply(driver, timeout=60):
    """GPTの応答を待機"""
    print("⏳ 応答を待機中...")
    
    selectors = [
        ".markdown.prose",
        "[data-message-author-role='assistant']",
        ".prose",
        "[class*='markdown']",
        ".whitespace-pre-wrap"
    ]
    
    start_time = time.time()
    last_content = ""
    
    while time.time() - start_time < timeout:
        for selector in selectors:
            try:
                outputs = driver.find_elements(By.CSS_SELECTOR, selector)
                if outputs:
                    current_content = outputs[-1].text
                    if current_content and current_content != last_content:
                        if len(current_content) > 20:  # 短すぎる応答は除外
                            print("✅ 応答を取得しました")
                            return current_content
                        last_content = current_content
            except Exception as e:
                continue
        
        time.sleep(2)
    
    print("⚠️ 応答のタイムアウト")
    return ""

def send_prompt(driver, text, timeout=20):
    """メッセージを送信"""
    try:
        # 複数のセレクタを試す
        selectors = [
            "textarea[placeholder*='Message']",
            "textarea[data-id='root']",
            "textarea",
            "#prompt-textarea",
            "textarea[placeholder*='メッセージ']"
        ]
        
        textarea = None
        for selector in selectors:
            try:
                textarea = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                break
            except:
                continue
        
        if textarea:
            # Seleniumで送信
            textarea.click()
            time.sleep(0.5)
            textarea.clear()
            textarea.send_keys(text)
            time.sleep(0.5)
            textarea.send_keys(Keys.ENTER)
            print(f"📤 メッセージ送信: {text}")
            return True
        else:
            # フォールバック: pyautogui使用
            print("⚠️ Seleniumでの送信に失敗、pyautogui使用...")
            screen_width = driver.execute_script("return window.innerWidth")
            screen_height = driver.execute_script("return window.innerHeight")
            
            # 画面下部の入力欄付近をクリック
            pyautogui.click(screen_width // 2, int(screen_height * 0.9))
            time.sleep(0.5)
            pyautogui.typewrite(text)
            time.sleep(0.5)
            pyautogui.press('enter')
            print(f"📤 pyautoguiでメッセージ送信: {text}")
            return True
            
    except Exception as e:
        print(f"❌ メッセージ送信に失敗: {e}")
        driver.save_screenshot(f"send_error_{int(time.time())}.png")
        return False

def main():
    """メイン処理"""
    print("🚀 OpenVPN対応ChatGPTスクレイパーを開始...")
    
    # OpenVPNの利用可能性をチェック
    openvpn_path = check_openvpn_availability()
    if not openvpn_path:
        print("❌ OpenVPNが見つかりません")
        print("OpenVPNをインストールするか、VPNなしで実行してください")
    else:
        print(f"✅ OpenVPN発見: {openvpn_path}")
    
    # アカウント選択
    account = get_account_choice()
    account_config = VPN_CONFIGS[account]
    
    print(f"🎯 選択されたアカウント: {account}")
    print(f"📄 設定ファイル: {account_config['config']}")
    print(f"💾 保存先: {account_config['csv']}")
    
    # VPN接続オプション
    print("\n🔍 VPN接続オプション:")
    if openvpn_path:
        print("1. OpenVPNで自動接続")
    print("2. VPNなしで実行")
    print("3. 手動でVPN接続済み")
    
    choice = input("選択してください (1-3): ").strip()
    
    vpn_connected = False
    vpn_process = None
    
    if choice == "1" and openvpn_path:
        success, process = connect_openvpn_with_config(
            account_config['config'], 
            account_config['auth']
        )
        if success:
            vpn_connected = True
            vpn_process = process
        else:
            print("❌ VPN接続に失敗しました")
            retry = input("VPNなしで続行しますか？ (y/n): ")
            if retry.lower() != 'y':
                return
    elif choice == "3":
        print("⚠️ VPNが手動で接続済みであることを確認してください")
        input("確認後、Enterキーを押してください...")
        vpn_connected = True
    elif choice == "1" and not openvpn_path:
        print("❌ OpenVPNが利用できません。他のオプションを選択してください")
        return

    print(f"✅ Chromeに突入: {account}")
    # Chrome設定
    options = uc.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    # プロファイル設定
    user_data_dir = os.path.expandvars(r"C:\Users\%USERNAME%\AppData\Local\Google\Chrome\User Data")
    if os.path.exists(user_data_dir):
        options.add_argument(f"--user-data-dir={user_data_dir}")
        options.add_argument(f"--profile-directory={account}")
        print(f"✅ Chromeプロファイル使用: {account}")
    else:
        print("⚠️ Chromeプロファイルが見つかりません。新しいセッションで開始します")
    
    try:
        driver = uc.Chrome(options=options)
        time.sleep(5)
        
        print("🎯 GPTsにアクセス中...")
        driver.get(GPT_URL)
        time.sleep(10)
        
        retry_count = 0
        max_retries = 3
        csv_file = account_config['csv']
        
        while get_current_tweet_count(csv_file) < MAX_TWEETS:
            current_count = get_current_tweet_count(csv_file)
            print(f"📊 現在のツイート数: {current_count}/{MAX_TWEETS}")
            
            if not send_prompt(driver, "n"):
                retry_count += 1
                if retry_count > max_retries:
                    print("❌ 送信に失敗しました。終了します。")
                    break
                print(f"⚠️ 送信失敗、リトライします... ({retry_count}/{max_retries})")
                time.sleep(5)
                continue
            
            output = wait_for_reply(driver, WAIT_SECONDS)
            if not output:
                retry_count += 1
                if retry_count > max_retries:
                    print("❌ 応答が得られませんでした。終了します。")
                    break
                print(f"⚠️ 応答なし、リトライします... ({retry_count}/{max_retries})")
                continue
            
            tweets = extract_tweets_from_output(output)
            if tweets:
                save_tweets(tweets, csv_file)
                new_count = get_current_tweet_count(csv_file)
                print(f"✅ {len(tweets)}件保存 → 合計: {new_count}件")
                retry_count = 0  # 成功したらリトライカウントをリセット
            else:
                print("⚠️ 有効なツイートが見つかりませんでした")
                print(f"GPT応答内容: {output[:200]}...")  # デバッグ用
            
            time.sleep(10)  # 次のリクエストまで待機
        
        print(f"🎉 {account}で{MAX_TWEETS}件のツイート案を保存しました！")
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        try:
            driver.save_screenshot(f"error_screenshot_{account}_{int(time.time())}.png")
            print("📸 エラースクリーンショットを保存しました")
        except:
            pass
    
    finally:
        try:
            driver.quit()
        except:
            pass
        
        if vpn_connected and choice == "1":
            disconnect_openvpn()
        print("🔚 プログラムを終了します")

if __name__ == "__main__":
    main()