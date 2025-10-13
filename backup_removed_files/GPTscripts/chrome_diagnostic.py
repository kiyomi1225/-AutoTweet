import os
import subprocess
import time
import tempfile
import shutil
import sys

def clean_chrome_processes():
    """Chromeプロセスの完全クリーンアップ"""
    print("🧹 Chromeプロセスをクリーンアップ中...")
    
    processes_to_kill = [
        "chrome.exe",
        "chromedriver.exe", 
        "chromedriver",
        "chrome"
    ]
    
    for process in processes_to_kill:
        try:
            subprocess.run(f"taskkill /F /IM {process}", shell=True, stderr=subprocess.DEVNULL)
            time.sleep(1)
        except:
            pass
    
    print("✅ プロセスクリーンアップ完了")

def clean_temp_directories():
    """一時ディレクトリのクリーンアップ"""
    print("🧹 一時ディレクトリをクリーンアップ中...")
    
    temp_dirs = [
        os.path.join(tempfile.gettempdir(), "scoped_dir*"),
        os.path.join(tempfile.gettempdir(), ".com.google.Chrome.*"),
        os.path.expandvars(r"C:\Users\%USERNAME%\AppData\Local\Temp\scoped_dir*")
    ]
    
    for temp_pattern in temp_dirs:
        try:
            import glob
            for temp_dir in glob.glob(temp_pattern):
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception as e:
            print(f"⚠️ 一時ディレクトリ削除失敗: {e}")
    
    print("✅ 一時ディレクトリクリーンアップ完了")

def check_dependencies():
    """依存関係の確認"""
    print("🔍 依存関係を確認中...")
    
    try:
        import undetected_chromedriver as uc
        print("✅ undetected-chromedriver インポート成功")
        print(f"   バージョン: {uc.__version__}")
    except ImportError as e:
        print(f"❌ undetected-chromedriver インポート失敗: {e}")
        print("pip install undetected-chromedriver で再インストールしてください")
        return False
    
    try:
        from selenium import webdriver
        print("✅ selenium インポート成功")
    except ImportError as e:
        print(f"❌ selenium インポート失敗: {e}")
        print("pip install selenium で再インストールしてください")
        return False
    
    return True

def test_chrome_simple():
    """最も基本的なChrome起動テスト"""
    print("🧪 基本Chrome起動テスト...")
    
    clean_chrome_processes()
    time.sleep(2)
    
    try:
        import undetected_chromedriver as uc
        
        # 最小限の設定
        options = uc.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-web-security")
        options.add_argument("--disable-features=VizDisplayCompositor")
        options.add_argument("--headless")  # まずはヘッドレスで
        
        print("🚀 Chrome起動中...")
        driver = uc.Chrome(options=options)
        
        print("🌐 Googleにアクセス中...")
        driver.get("https://www.google.com")
        
        title = driver.title
        print(f"✅ 成功: {title}")
        
        driver.quit()
        return True
        
    except Exception as e:
        print(f"❌ 基本テスト失敗: {e}")
        print(f"エラーの詳細: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

def test_with_custom_chrome_path():
    """カスタムChromeパスでのテスト"""
    print("🧪 カスタムChromeパステスト...")
    
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
    ]
    
    for chrome_path in chrome_paths:
        if os.path.exists(chrome_path):
            print(f"🔄 テスト中: {chrome_path}")
            
            try:
                import undetected_chromedriver as uc
                
                options = uc.ChromeOptions()
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                options.add_argument("--headless")
                options.binary_location = chrome_path
                
                driver = uc.Chrome(options=options)
                driver.get("https://www.google.com")
                print(f"✅ 成功: {chrome_path}")
                driver.quit()
                return chrome_path
                
            except Exception as e:
                print(f"❌ 失敗: {e}")
    
    return None

def test_with_specific_chromedriver():
    """特定のChromedriverでのテスト"""
    print("🧪 Chromedriver指定テスト...")
    
    try:
        import undetected_chromedriver as uc
        
        # Chromedriverのパスを明示的に指定
        options = uc.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--headless")
        
        # 一時ディレクトリにChromedriverをダウンロード
        temp_dir = tempfile.mkdtemp()
        print(f"一時ディレクトリ: {temp_dir}")
        
        driver = uc.Chrome(
            options=options,
            driver_executable_path=None,  # 自動検出
            browser_executable_path=None  # 自動検出
        )
        
        driver.get("https://www.google.com")
        print("✅ Chromedriver指定テスト成功")
        driver.quit()
        
        # 一時ディレクトリをクリーンアップ
        shutil.rmtree(temp_dir, ignore_errors=True)
        return True
        
    except Exception as e:
        print(f"❌ Chromedriver指定テスト失敗: {e}")
        return False

def reinstall_packages():
    """パッケージの再インストール"""
    print("📦 パッケージ再インストール...")
    
    packages = [
        "undetected-chromedriver",
        "selenium"
    ]
    
    for package in packages:
        try:
            print(f"🔄 {package} をアンインストール中...")
            subprocess.run([sys.executable, "-m", "pip", "uninstall", package, "-y"], 
                         check=True, capture_output=True)
            
            print(f"🔄 {package} をインストール中...")
            subprocess.run([sys.executable, "-m", "pip", "install", package], 
                         check=True, capture_output=True)
            
            print(f"✅ {package} 再インストール完了")
            
        except Exception as e:
            print(f"❌ {package} 再インストール失敗: {e}")

def main():
    """メイン診断処理"""
    print("🔍 Chrome詳細診断ツール")
    print("=" * 50)
    
    # 1. 依存関係チェック
    if not check_dependencies():
        print("\n📦 依存関係に問題があります。再インストールしますか？")
        choice = input("再インストールする場合は 'y' を入力: ")
        if choice.lower() == 'y':
            reinstall_packages()
            print("\n🔄 再インストール後、スクリプトを再実行してください")
            return
    
    # 2. クリーンアップ
    clean_chrome_processes()
    clean_temp_directories()
    
    # 3. 基本テスト
    print("\n" + "=" * 50)
    if test_chrome_simple():
        print("🎉 基本テストが成功しました！")
        return
    
    # 4. カスタムパステスト
    print("\n" + "=" * 50)
    working_chrome = test_with_custom_chrome_path()
    if working_chrome:
        print(f"🎉 カスタムパステストが成功しました: {working_chrome}")
        return
    
    # 5. Chromedriver指定テスト
    print("\n" + "=" * 50)
    if test_with_specific_chromedriver():
        print("🎉 Chromedriver指定テストが成功しました！")
        return
    
    # すべて失敗した場合
    print("\n" + "=" * 50)
    print("❌ すべてのテストが失敗しました")
    print("\n🔧 推奨解決策:")
    print("1. Chromeを完全にアンインストールして再インストール")
    print("2. ウイルス対策ソフトを一時的に無効化")
    print("3. 管理者権限でスクリプトを実行")
    print("4. Windowsを再起動")
    print("5. 別のブラウザ自動化ライブラリを検討 (例: playwright)")

if __name__ == "__main__":
    main()