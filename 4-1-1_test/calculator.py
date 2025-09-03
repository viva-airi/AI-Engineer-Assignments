def calculator():
    """
    簡単な計算機プログラム
    ユーザーから2つの数値と四則演算子を入力させ、結果を表示します
    """
    print("=== 簡単な計算機 ===")
    print("四則演算（+、-、*、/）ができます")
    
    try:
        # 1つ目の数値を入力
        num1 = float(input("1つ目の数値を入力してください: "))
        
        # 2つ目の数値を入力
        num2 = float(input("2つ目の数値を入力してください: "))
        
        # 演算子を入力
        operator = input("演算子を入力してください（+、-、*、/）: ")
        
        # 計算の実行
        if operator == "+":
            result = num1 + num2
            print(f"{num1} + {num2} = {result}")
        elif operator == "-":
            result = num1 - num2
            print(f"{num1} - {num2} = {result}")
        elif operator == "*":
            result = num1 * num2
            print(f"{num1} * {num2} = {result}")
        elif operator == "/":
            if num2 == 0:
                print("エラー: 0で割ることはできません")
            else:
                result = num1 / num2
                print(f"{num1} / {num2} = {result}")
        else:
            print("エラー: 無効な演算子です。+、-、*、/のいずれかを入力してください")
            
    except ValueError:
        print("エラー: 数値を正しく入力してください")
    except Exception as e:
        print(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    calculator()
