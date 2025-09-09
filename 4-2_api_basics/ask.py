#!/usr/bin/env python3
"""
OpenAI ChatGPT CLI ツール

このスクリプトは、コマンドラインからOpenAIのChatGPT APIに質問を送信するためのCLIツールです。

使用例:
    # 単発の質問
    python ask.py "Pythonについて教えて"
    
    # システムプロンプト付き
    python ask.py "コードを書いて" --system "あなたはプログラミングの専門家です"
    
    # パラメータを指定
    python ask.py "創造的な物語を書いて" --temp 0.9 --max-tokens 2000
    
    # インタラクティブモード
    python ask.py
    質問: こんにちは
    回答: こんにちは！何かお手伝いできることはありますか？
    質問: exit
"""

import argparse
import sys
import signal
from typing import Optional

from chatgpt_client import ChatGPTClient


def signal_handler(signum, frame):
    """Ctrl+C ハンドラー"""
    print("\n\n終了します...")
    sys.exit(0)


def check_api_key() -> None:
    """API キーの存在をチェック"""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        print("エラー: OPENAI_API_KEY が設定されていません。")
        print("")
        print("解決方法:")
        print("1. .env ファイルを作成してください")
        print("2. 以下の内容を追加してください:")
        print("   OPENAI_API_KEY=your_api_key_here")
        print("")
        print("API キーは https://platform.openai.com/ で取得できます。")
        sys.exit(1)


def single_shot_mode(question: str, system_prompt: Optional[str], 
                    model: str, temperature: float, max_tokens: int) -> None:
    """単発質問モード"""
    try:
        client = ChatGPTClient(model=model, temperature=temperature, max_tokens=max_tokens)
        response = client.send_message(question, system_prompt)
        print(response)
    except Exception as e:
        print(f"エラー: {str(e)}", file=sys.stderr)
        sys.exit(1)


def interactive_mode(system_prompt: Optional[str], model: str, 
                    temperature: float, max_tokens: int) -> None:
    """インタラクティブモード"""
    try:
        client = ChatGPTClient(model=model, temperature=temperature, max_tokens=max_tokens)
        
        print("ChatGPT CLI - インタラクティブモード")
        print("終了するには 'exit', 'quit', または Ctrl+C を入力してください")
        print("-" * 50)
        
        while True:
            try:
                question = input("質問: ").strip()
                
                if not question:
                    continue
                    
                if question.lower() in ['exit', 'quit']:
                    print("終了します...")
                    break
                
                response = client.send_message(question, system_prompt)
                print(f"回答: {response}")
                print()
                
            except EOFError:
                print("\n終了します...")
                break
            except KeyboardInterrupt:
                print("\n終了します...")
                break
                
    except Exception as e:
        print(f"エラー: {str(e)}", file=sys.stderr)
        sys.exit(1)


def main():
    """メイン関数"""
    # Ctrl+C ハンドラーを設定
    signal.signal(signal.SIGINT, signal_handler)
    
    # API キーをチェック
    check_api_key()
    
    # 引数解析
    parser = argparse.ArgumentParser(
        description="OpenAI ChatGPT CLI ツール",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  %(prog)s "Pythonについて教えて"
  %(prog)s "コードを書いて" --system "あなたはプログラミングの専門家です"
  %(prog)s "創造的な物語を書いて" --temp 0.9 --max-tokens 2000
  %(prog)s  # インタラクティブモード
        """
    )
    
    parser.add_argument(
        'question',
        nargs='?',
        help='質問内容（省略するとインタラクティブモード）'
    )
    
    parser.add_argument(
        '--system',
        type=str,
        help='システムプロンプト'
    )
    
    parser.add_argument(
        '--temp',
        type=float,
        default=0.7,
        help='温度パラメータ (デフォルト: 0.7)'
    )
    
    parser.add_argument(
        '--max-tokens',
        type=int,
        default=1000,
        help='最大トークン数 (デフォルト: 1000)'
    )
    
    parser.add_argument(
        '--model',
        type=str,
        default='gpt-4o-mini',
        help='使用するモデル (デフォルト: gpt-4o-mini)'
    )
    
    args = parser.parse_args()
    
    # パラメータの検証
    if args.temp < 0 or args.temp > 2:
        print("エラー: --temp は 0.0 から 2.0 の間で指定してください", file=sys.stderr)
        sys.exit(1)
    
    if args.max_tokens < 1:
        print("エラー: --max-tokens は 1 以上の値を指定してください", file=sys.stderr)
        sys.exit(1)
    
    # モードの選択
    if args.question:
        # 単発質問モード
        single_shot_mode(
            args.question, 
            args.system, 
            args.model, 
            args.temp, 
            args.max_tokens
        )
    else:
        # インタラクティブモード
        interactive_mode(
            args.system, 
            args.model, 
            args.temp, 
            args.max_tokens
        )


if __name__ == "__main__":
    main()
