import sys
import traceback
import time
import os

# 文字コード設定
if sys.platform == 'win32':
    # 環境変数でUTF-8を強制
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    
    # コンソールのコードページをUTF-8に設定
    try:
        os.system('chcp 65001 >nul 2>&1')
    except:
        pass

def find_script_file():
    """スクリプトファイルを探す"""
    script_names = [
        "fixed_openvpn_scraper.py",
        "fetch_tweets_from_gpt_vpn_profile.py"
    ]
    
    # 現在のディレクトリから探す
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    for script_name in script_names:
        # 同じディレクトリ内を確認
        script_path = os.path.join(current_dir, script_name)
        if os.path.exists(script_path):
            return script_path
        
        # カレントディレクトリを確認
        if os.path.exists(script_name):
            return os.path.abspath(script_name)
    
    return None

def safe_run_scraper():
    """スクレイパーを安全に実行"""
    try:
        print("ChatGPT Auto Tweet Scraper - Safe Mode")
        print("=" * 50)
        
        # 現在のディレクトリを確認
        current_dir = os.getcwd()
        script_dir = os.path.dirname(os.path.abspath(__file__))
        print("Current directory:", current_dir)
        print("Script directory:", script_dir)
        
        # スクリプトファイルを探す
        script_file = find_script_file()
        
        if not script_file:
            print("[ERROR] Main script file not found")
            print("Required files:")
            print("   - fixed_openvpn_scraper.py")
            print("   - fetch_tweets_from_gpt_vpn_profile.py")
            print("")
            print("Python files in current directory:")
            
            # 現在のディレクトリのPythonファイルを一覧表示
            python_files = [f for f in os.listdir('.') if f.endswith('.py')]
            if python_files:
                for f in python_files:
                    print("   -", f)
            else:
                print("   No Python files found")
            
            print("")
            print("Solutions:")
            print("1. Move to correct directory")
            print("2. Place script files in same folder")
            return
        
        print("[OK] Found:", os.path.basename(script_file))
        print("File path:", script_file)
        print("Starting main process...")
        print("")
        
        # スクリプトディレクトリに移動
        os.chdir(script_dir)
        
        # メインスクリプトを実行
        with open(script_file, 'r', encoding='utf-8') as f:
            script_content = f.read()
        
        # グローバル名前空間で実行
        exec(script_content, {'__name__': '__main__'})
        
        print("\n[SUCCESS] Process completed successfully")
        
    except KeyboardInterrupt:
        print("\n[WARNING] Process interrupted by user")
    except FileNotFoundError as e:
        print("\n[ERROR] File not found:", e)
        print("Make sure all required files are in place")
    except ImportError as e:
        print("\n[ERROR] Module import error:", e)
        print("Install required libraries:")
        print("   pip install undetected-chromedriver selenium pyautogui")
    except UnicodeEncodeError as e:
        print("\n[ERROR] Character encoding error:", e)
        print("Try running in a UTF-8 compatible terminal")
    except Exception as e:
        print("\n[ERROR] An error occurred:", e)
        print("Error type:", type(e).__name__)
        print("\nDetailed error information:")
        traceback.print_exc()
        
        print("\nPossible solutions:")
        print("1. Run as administrator")
        print("2. Temporarily disable antivirus")  
        print("3. Reinstall Chrome")
        print("4. Reinstall Python and libraries")
        print("5. Run from correct directory")
    
    finally:
        print("\n" + "=" * 50)
        print("Program finished")
        
        # 強制的に待機してCMDが閉じないようにする
        try:
            input("\nPress Enter to exit...")
        except EOFError:
            print("Auto-closing in 10 seconds...")
            time.sleep(10)
        except KeyboardInterrupt:
            print("\nExiting...")

if __name__ == "__main__":
    safe_run_scraper()