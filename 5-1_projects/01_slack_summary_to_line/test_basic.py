#!/usr/bin/env python3
"""
基本的な動作テスト用スクリプト
"""
import os
import sys
from dotenv import load_dotenv

# 環境変数読み込み
load_dotenv()

def test_environment_variables():
    """環境変数の設定確認"""
    print("=== 環境変数設定確認 ===")
    
    required_vars = {
        'SLACK_BOT_TOKEN': 'Slack Bot Token',
        'SLACK_CHANNEL_ID': 'Slack Channel ID',
        'OPENAI_API_KEY': 'OpenAI API Key',
        'LINE_CHANNEL_ACCESS_TOKEN': 'LINE Channel Access Token'
    }
    
    optional_vars = {
        'LINE_USER_ID': 'LINE User ID (任意)',
        'SUMMARY_TIME_RANGE_HOURS': '要約対象時間（デフォルト: 12）'
    }
    
    print("必須環境変数:")
    for var, desc in required_vars.items():
        value = os.getenv(var)
        if value:
            # トークンは最初の数文字のみ表示
            masked_value = value[:8] + "..." if len(value) > 8 else "設定済み"
            print(f"  [OK] {var}: {masked_value}")
        else:
            print(f"  [NG] {var}: 未設定")
    
    print("\n任意環境変数:")
    for var, desc in optional_vars.items():
        value = os.getenv(var)
        if value:
            print(f"  [OK] {var}: {value}")
        else:
            print(f"  [-] {var}: 未設定（デフォルト値を使用）")
    
    print()

def test_imports():
    """必要なモジュールのインポート確認"""
    print("=== モジュールインポート確認 ===")
    
    try:
        from src.slack_client import SlackClient
        print("  [OK] slack_client.py")
    except ImportError as e:
        print(f"  [NG] slack_client.py: {e}")
    
    try:
        from src.summarizer import Summarizer
        print("  [OK] summarizer.py")
    except ImportError as e:
        print(f"  [NG] summarizer.py: {e}")
    
    try:
        from src.line_client import LineClient
        print("  [OK] line_client.py")
    except ImportError as e:
        print(f"  [NG] line_client.py: {e}")
    
    print()

def test_line_client():
    """LINEクライアントのテスト（実際の送信は行わない）"""
    print("=== LINEクライアント初期化テスト ===")
    
    try:
        from src.line_client import LineClient
        
        # テスト用のトークンで初期化
        test_token = "test_token"
        test_user_id = "test_user_id"
        
        # USER_IDありの場合
        client_with_user = LineClient(test_token, test_user_id)
        print("  [OK] USER_ID指定での初期化: 成功")
        
        # USER_IDなしの場合
        client_broadcast = LineClient(test_token, None)
        print("  [OK] USER_ID未指定での初期化: 成功")
        
    except Exception as e:
        print(f"  [NG] LINEクライアント初期化エラー: {e}")
    
    print()

def main():
    """メインテスト実行"""
    print("Slack要約LINE送信CLI - 基本動作テスト\n")
    
    test_environment_variables()
    test_imports()
    test_line_client()
    
    print("=== テスト完了 ===")
    print("すべてのテストが成功した場合、以下のコマンドで実際の動作確認ができます：")
    print("  python main.py --hours 1")
    print("\n注意: 実際のAPI呼び出しが発生するため、適切な環境変数が設定されていることを確認してください。")

if __name__ == "__main__":
    main()
