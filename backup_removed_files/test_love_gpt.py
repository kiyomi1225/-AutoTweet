# test_love_gpt.py - 恋愛先生GPT専用テスト
import sys
sys.path.append('.')

def test_love_gpt_automation():
    """恋愛先生GPT自動化テスト"""
    print("=" * 60)
    print("💕 恋愛先生GPT自動化テスト開始")
    print("=" * 60)
    
    try:
        from modules.config_manager import ConfigManager
        from modules.vpn_manager import VPNManager
        from modules.chrome_manager import ChromeManager
        from modules.gpt_image_automation import GPTImageAutomation
        from pathlib import Path
        
        # 設定確認
        print("📋 事前確認:")
        
        # 画像ファイル確認
        if Path("images/textarea.png").exists():
            print("✅ images/textarea.png 存在")
        else:
            print("❌ images/textarea.png が見つかりません")
            print("\n📷 画像ファイル準備手順:")
            print("1. 恋愛先生GPTページにアクセス")
            print("2. テキスト入力エリア（textarea）をスクリーンショット")
            print("3. images/textarea.png として保存")
            return
        
        # 設定初期化
        config = ConfigManager()
        vpn_manager = VPNManager(config)
        chrome_manager = ChromeManager(config)
        automation = GPTImageAutomation(config, vpn_manager, chrome_manager)
        
        print("✅ モジュール初期化完了")
        
        # テスト設定
        test_account = "acc1"
        love_gpt_url = "https://chatgpt.com/g/g-685aa726977081918c2166e6709e915b-ji-ke-tuitozuo-cheng-ai-lian-ai-xian-sheng"
        target_count = 30  # テスト用に少なめ
        
        print(f"\n🧪 テスト設定:")
        print(f"   🆔 アカウント: {test_account}")
        print(f"   💕 恋愛先生GPT URL: {love_gpt_url}")
        print(f"   🎯 目標取得数: {target_count}件")
        print(f"   📂 保存先: data/{test_account}.csv")
        
        confirm = input(f"\n🚀 恋愛先生GPT自動化テストを実行しますか？ (y/n): ")
        if confirm.lower() != 'y':
            print("テスト中止")
            return
        
        print(f"\n📷 画像認識自動化開始...")
        print(f"⚠️ 重要: 実行中はマウス・キーボードを操作しないでください")
        
        # カウントダウン
        for i in range(3, 0, -1):
            print(f"⏰ {i}秒後に開始...")
            import time
            time.sleep(1)
        
        # 自動化実行
        success = automation.run_automation(test_account, love_gpt_url, target_count)
        
        if success:
            print(f"\n🎉 恋愛先生GPT自動化テスト成功！")
            
            # 結果確認
            csv_file = Path(f"data/{test_account}.csv")
            if csv_file.exists():
                import csv
                with open(csv_file, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    next(reader)  # ヘッダースキップ
                    tweets = list(reader)
                
                total_count = len(tweets)
                print(f"📊 総取得数: {total_count}件")
                
                # 最新数件を表示
                print(f"\n💕 最新の恋愛ツイート:")
                print("-" * 60)
                for i, tweet_row in enumerate(tweets[-5:], 1):
                    if len(tweet_row) >= 2:
                        content = tweet_row[1]  # content列
                        length = len(content)
                        print(f"{i}. ({length}文字) {content}")
                print("-" * 60)
                
                # 文字数分布確認
                lengths = [len(row[1]) for row in tweets if len(row) >= 2]
                if lengths:
                    avg_length = sum(lengths) / len(lengths)
                    max_length = max(lengths)
                    min_length = min(lengths)
                    valid_count = sum(1 for l in lengths if l <= 140)
                    
                    print(f"\n📈 文字数分析:")
                    print(f"   平均文字数: {avg_length:.1f}文字")
                    print(f"   最大文字数: {max_length}文字")
                    print(f"   最小文字数: {min_length}文字")
                    print(f"   140文字以下: {valid_count}/{len(lengths)}件")
            else:
                print(f"📁 CSVファイルが見つかりません")
        else:
            print(f"\n❌ 恋愛先生GPT自動化テスト失敗")
            print(f"📋 原因確認:")
            print(f"   - images/textarea.png が正確か")
            print(f"   - GPTsページが正常に表示されているか")
            print(f"   - ログイン状態が維持されているか")
        
        print(f"\n🏁 恋愛先生GPT自動化テスト完了")
        
    except Exception as e:
        print(f"❌ テストエラー: {str(e)}")
        import traceback
        traceback.print_exc()

def show_sample_output():
    """恋愛先生GPTの想定出力例を表示"""
    print("\n💕 恋愛先生GPT 想定出力例:")
    print("-" * 50)
    sample_output = """
1. 今日のデートプラン、彼と一緒に考えてるだけでドキドキしちゃう💕 みんなはどんなデートが好き？

2. 彼からの「おはよう」のメッセージで一日が始まる幸せ✨ 愛って素晴らしいね！

3. 恋愛映画見てると、自分たちもこんな風に愛し合えてるかなって思っちゃう😊

4. 彼の笑顔を見てるだけで、全部の悩みが吹き飛んじゃう💫 これが恋の力かな？

5. 今度の記念日、何をプレゼントしようか悩み中...💭 みんなは何あげてる？

「追加でツイート作成を依頼する場合は n を入力してください。」
"""
    print(sample_output)
    print("-" * 50)
    print("📝 この例から以下が抽出されます:")
    print("   - 番号付きリスト (1. 2. 3. 4. 5.)")
    print("   - 140文字以下のツイート")
    print("   - 案内メッセージは除外")

if __name__ == "__main__":
    print("💕 恋愛先生GPT自動化テストシステム")
    print("=" * 60)
    
    print("メニュー:")
    print("1. 📷 恋愛先生GPT自動化テスト実行")
    print("2. 📝 想定出力例表示")
    print("0. 終了")
    
    choice = input("\n選択してください (0-2): ")
    
    if choice == "1":
        test_love_gpt_automation()
    elif choice == "2":
        show_sample_output()
    else:
        print("終了")