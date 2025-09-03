# 入力した文字の文字数を表示するPythonコード

def main():
    print("文字を入力してください：")
    
    # ユーザーからの入力を取得
    user_input = input()
    
    # 入力された文字を表示
    print(f"入力された文字は「{user_input}」です")
    
    # 文字数も表示
    print(f"文字数は{len(user_input)}文字です")

if __name__ == "__main__":
    main()