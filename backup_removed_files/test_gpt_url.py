# test_gpt_url.py - GPTsアクセステスト
import sys
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

sys.path.append('.')

def test_gpts_access():
    """GPTsアクセステスト"""
    print("=" * 60)
    print("🔗 GPTsアクセステスト開始")
    print("=" * 60)
    
    # テスト用URL
    test_urls = [
        "https://chatgpt.com/g/g-685aa726977081918c2166e6709e915b-ji-ke-tuitozuo-cheng-ai-lian-ai-xian-sheng",
        "https://chatgpt.com/",
        "https://chat.openai.com/"
    ]
    
    driver = None
    
    try:
        # Chrome設定
        chrome_options = Options()
        chrome_options.binary_location = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        
        # 独立プロファイル
        selenium_profile_dir = Path("test_selenium_profile")
        selenium_profile_dir.mkdir(exist_ok=True)
        
        chrome_options.add_argument(f"--user-data-dir={selenium_profile_dir.absolute()}")
        chrome_options.add_argument("--profile-directory=Default")
        
        # エラー抑制オプション
        chrome_options.add_argument("--remote-debugging-port=0")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-logging")
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_argument("--silent")
        chrome_options.add_argument("--disable-gpu-logging")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--start-maximized")
        
        # ChromeDriverサービス
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            service = Service(ChromeDriverManager().install())
        except ImportError:
            service = Service()
        
        service.log_level = 'FATAL'
        
        # ドライバー作成
        print("🌐 Chrome起動中...")
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.implicitly_wait(10)
        print("✅ Chrome起動成功")
        
        # URL別テスト
        for i, url in enumerate(test_urls, 1):
            print(f"\n[テスト {i}] {url}")
            
            try:
                print("🔗 アクセス中...")
                driver.get(url)
                
                # ページ読み込み待機
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # ページタイトル取得
                title = driver.title
                print(f"📄 ページタイトル: {title}")
                
                # URL確認
                current_url = driver.current_url
                print(f"🔗 現在のURL: {current_url}")
                
                # ログイン状態確認
                time.sleep(3)
                
                # ChatGPT要素の存在確認
                chatgpt_elements = [
                    "textarea[data-id='root']",
                    "textarea[placeholder*='メッセージ']",
                    "textarea[placeholder*='Message']",
                    ".ProseMirror",
                    "#prompt-textarea"
                ]
                
                found_textarea = False
                for selector in chatgpt_elements:
                    try:
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        if elements:
                            print(f"✅ チャット入力エリア発見: {selector}")
                            found_textarea = True
                            break
                    except:
                        continue
                
                if not found_textarea:
                    print("⚠️ チャット入力エリアが見つかりません")
                    
                    # ログイン要求の確認
                    login_indicators = [
                        "button[data-testid='login-button']",
                        "a[href*='login']",
                        "Log in",
                        "ログイン"
                    ]
                    
                    login_needed = False
                    for indicator in login_indicators:
                        try:
                            if indicator.startswith(('Log in', 'ログイン')):
                                if indicator in driver.page_source:
                                    login_needed = True
                                    break
                            else:
                                elements = driver.find_elements(By.CSS_SELECTOR, indicator)
                                if elements:
                                    login_needed = True
                                    break
                        except:
                            continue
                    
                    if login_needed:
                        print("🔐 ログインが必要です")
                    else:
                        print("❓ 不明な状態です")
                else:
                    print("✅ GPTsアクセス成功")
                
                # スクリーンショット保存
                screenshot_path = f"test_screenshot_{i}.png"
                driver.save_screenshot(screenshot_path)
                print(f"📷 スクリーンショット保存: {screenshot_path}")
                
                if i == 1:  # 最初のURL（恋愛先生GPT）で詳細確認
                    print(f"\n📋 恋愛先生GPT詳細確認:")
                    
                    # ページソースの一部確認
                    page_source = driver.page_source
                    
                    gpt_indicators = [
                        "恋愛先生",
                        "ツイート作成",
                        "ji-ke-tuitozuo-cheng-ai-lian-ai-xian-sheng"
                    ]
                    
                    for indicator in gpt_indicators:
                        if indicator in page_source:
                            print(f"✅ GPT要素確認: {indicator}")
                        else:
                            print(f"❌ GPT要素なし: {indicator}")
                    
                    # 10秒間確認時間
                    print(f"\n⏰ 10秒間手動確認時間...")
                    print(f"ブラウザでGPTsページが正しく表示されているか確認してください")
                    time.sleep(10)
                
            except Exception as e:
                print(f"❌ アクセスエラー: {str(e)}")
                continue
        
        print(f"\n🏁 GPTsアクセステスト完了")
        
    except Exception as e:
        print(f"❌ テスト全体エラー: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        if driver:
            print(f"\n🧹 Chrome終了中...")
            driver.quit()
            print(f"✅ Chrome終了完了")

def test_url_format():
    """URL形式テスト"""
    print("\n🔗 URL形式確認:")
    
    original_url = "https://chatgpt.com/g/g-685aa726977081918c2166e6709e915b-ji-ke-tuitozuo-cheng-ai-lian-ai-xian-sheng"
    
    # 代替URL形式
    alternative_urls = [
        "https://chat.openai.com/g/g-685aa726977081918c2166e6709e915b-ji-ke-tuitozuo-cheng-ai-lian-ai-xian-sheng",
        "https://chatgpt.com/g/g-685aa726977081918c2166e6709e915b",
        "https://chatgpt.com/",
    ]
    
    print(f"元のURL: {original_url}")
    print(f"\n代替URL候補:")
    for i, url in enumerate(alternative_urls, 1):
        print(f"{i}. {url}")

if __name__ == "__main__":
    print("🧪 GPTs接続テストシステム")
    print("=" * 60)
    
    print("メニュー:")
    print("1. 🔗 GPTsアクセステスト実行")
    print("2. 🔗 URL形式確認")
    print("0. 終了")
    
    choice = input("\n選択してください (0-2): ")
    
    if choice == "1":
        test_gpts_access()
    elif choice == "2":
        test_url_format()
    else:
        print("終了")