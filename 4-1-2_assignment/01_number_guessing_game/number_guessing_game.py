import random

def number_guessing_game():
    """
    数当てゲームのメイン関数
    コンピューターが1～100の間の数字をランダムに選び、
    ユーザーがその数字を当てるゲーム
    """
    print("=== 数当てゲーム ===")
    print("1から100の間の数字を当ててください！")
    print("-" * 30)
    
    # コンピューターが1～100の間の数字をランダムに選択
    target_number = random.randint(1, 100)
    attempts = 0
    
    while True:
        try:
            # ユーザーの入力を受け取る
            user_input = input("数字を入力してください（1-100）: ")
            
            # 入力値の検証
            if not user_input.isdigit():
                print("正しい数字を入力してください。")
                continue
                
            user_guess = int(user_input)
            
            # 範囲チェック
            if user_guess < 1 or user_guess > 100:
                print("1から100の間の数字を入力してください。")
                continue
            
            attempts += 1
            
            # 数字の比較とヒント表示
            if user_guess < target_number:
                print("もっと大きい数字です！")
            elif user_guess > target_number:
                print("もっと小さい数字です！")
            else:
                print(f"\n🎉 正解です！🎉")
                print(f"答えは {target_number} でした。")
                print(f"試行回数: {attempts}回")
                break
                
        except ValueError:
            print("正しい数字を入力してください。")
        except KeyboardInterrupt:
            print("\n\nゲームを終了します。")
            break
    
    print("\nゲーム終了！お疲れさまでした。")

if __name__ == "__main__":
    number_guessing_game()
