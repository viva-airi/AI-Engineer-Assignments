"""
ChatGPT API 4-2
最小実装版
"""

import os
from openai import OpenAI
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

class ChatGPTClient:
    def __init__(self, model: str = "gpt-4o-mini", temperature: float = 0.7, max_tokens: int = 1000):
        """ChatGPT クライアントを初期化
        
        Args:
            model (str): 使用するモデル名 (デフォルト: gpt-4o-mini)
            temperature (float): 温度パラメータ (デフォルト: 0.7)
            max_tokens (int): 最大トークン数 (デフォルト: 1000)
        """
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY が設定されていません。.envファイルを確認してください。")
        
        # 環境変数からプロキシ設定をクリア
        proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy']
        for var in proxy_vars:
            if var in os.environ:
                del os.environ[var]
        
        try:
            self.client = OpenAI(api_key=api_key)
        except Exception as e:
            raise ValueError(f"OpenAIクライアントの初期化に失敗しました: {str(e)}")
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
    
    def send_message(self, message: str, system_prompt: str = None) -> str:
        """
        ChatGPTにメッセージを送信して応答を取得
        
        Args:
            message (str): ユーザーのメッセージ
            system_prompt (str, optional): システムプロンプト
            
        Returns:
            str: ChatGPTの応答
        """
        try:
            messages = []
            
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            messages.append({"role": "user", "content": message})
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"エラーが発生しました: {str(e)}"
    
    def get_completion(self, prompt: str) -> str:
        """
        シンプルな完了タスク用のメソッド
        
        Args:
            prompt (str): プロンプト
            
        Returns:
            str: 完了されたテキスト
        """
        return self.send_message(prompt)
def main():
    """対話モード"""
    try:
        # クライアントを初期化
        chatgpt = ChatGPTClient()

        print("対話モード開始！質問をどうぞ。（終了するには 'exit' または 'quit' を入力）")

        while True:
            # 質問を入力
            user_message = input("質問: ").strip()

            # 終了コマンドなら抜ける
            if user_message.lower() in ("exit", "quit"):
                print("対話モードを終了します。")
                break

            if not user_message:
                continue  # 空入力ならスキップ

            print("-" * 50)

            # ChatGPTへ送信
            response = chatgpt.send_message(user_message)

            print("ChatGPTの応答:")
            print(response)
            print("-" * 50)

    except KeyboardInterrupt:
        print("\n(終了しました)")
    except Exception as e:
        print(f"エラー: {e}")
        print("環境変数OPENAI_API_KEYが正しく設定されているか確認してください。")


if __name__ == "__main__":
    main()

