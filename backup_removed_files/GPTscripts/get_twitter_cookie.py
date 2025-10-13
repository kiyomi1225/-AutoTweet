import undetected_chromedriver as uc
import pickle
import time
import os

COOKIE_FILE = "twitter_cookie.pkl"

def main():
    options = uc.ChromeOptions()
    options.add_argument("--start-maximized")

    driver = uc.Chrome(options=options)
    driver.get("https://x.com/home")

    print("✅ Twitter にログインしてください（Google/Microsoft/Mail）")
    input("👉 ログイン完了したら Enter を押してください：")

    # Cookie 保存
    cookies = driver.get_cookies()
    os.makedirs(os.path.dirname(COOKIE_FILE), exist_ok=True) if "/" in COOKIE_FILE else None
    with open(COOKIE_FILE, "wb") as f:
        pickle.dump(cookies, f)

    print(f"✅ Cookie を保存しました → {COOKIE_FILE}")
    driver.quit()

if __name__ == "__main__":
    main()
