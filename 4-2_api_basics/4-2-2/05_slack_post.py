#!/usr/bin/env python3
"""
Slackにメッセージを投稿するスクリプト

使用方法:
    python 05_slack_post.py "メッセージ内容"
    python 05_slack_post.py "メッセージ内容" --thread-ts 1234567890.123456
"""

import argparse
import sys
from pathlib import Path
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from utils.env_loader import load_env


def main():
    # コマンドライン引数の解析
    parser = argparse.ArgumentParser(description='Slackにメッセージを投稿')
    parser.add_argument('message', help='投稿するメッセージ（必須）')
    parser.add_argument('--thread-ts', help='スレッド返信のタイムスタンプ（任意）')
    
    args = parser.parse_args()
    
    # 環境変数の読み込み
    script_dir = Path(__file__).resolve().parent
    env_path = script_dir / "env" / "slack.env"
    
    try:
        env = load_env(str(env_path))
    except FileNotFoundError as e:
        print(f"エラー: {e}")
        sys.exit(1)
    
    # 必要な環境変数の確認
    bot_token = env.get('SLACK_BOT_TOKEN')
    channel_id = env.get('SLACK_CHANNEL_ID')
    
    if not bot_token:
        print("エラー: SLACK_BOT_TOKEN が設定されていません")
        sys.exit(1)
    
    if not channel_id:
        print("エラー: SLACK_CHANNEL_ID が設定されていません")
        sys.exit(1)
    
    # メッセージの長さチェック（2000文字制限）
    message = args.message
    if len(message) > 2000:
        message = message[:2000]
        print("注意: メッセージが2000文字を超えたため、先頭2000文字に切り詰めました")
    
    # Slackクライアントの初期化
    client = WebClient(token=bot_token)
    
    # メッセージ投稿のパラメータ
    post_params = {
        'channel': channel_id,
        'text': message
    }
    
    # スレッド返信の場合はthread_tsを追加
    if args.thread_ts:
        post_params['thread_ts'] = args.thread_ts
    
    try:
        # メッセージを投稿
        response = client.chat_postMessage(**post_params)
        
        # レスポンスの確認
        if response['ok']:
            print("OK")
        else:
            print(f"エラー: Slack API エラー - {response.get('error', 'Unknown error')}")
            sys.exit(1)
            
    except SlackApiError as e:
        print(f"エラー: Slack API エラー - {e.response['error']}")
        sys.exit(1)
    except Exception as e:
        print(f"エラー: 予期しないエラーが発生しました - {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
