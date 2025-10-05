#!/usr/bin/env python3
"""
Slack要約LINE送信CLI
Slackの直近N時間のメッセージを取得→OpenAIで要約→LINEに送信
"""
import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

from src.slack_client import SlackClient
from src.summarizer import Summarizer
from src.line_client import LineClient


def load_environment():
    """環境変数を読み込み"""
    load_dotenv()
    
    required_vars = [
        'SLACK_BOT_TOKEN',
        'SLACK_CHANNEL_ID', 
        'OPENAI_API_KEY',
        'LINE_CHANNEL_ACCESS_TOKEN'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"エラー: 以下の環境変数が設定されていません: {', '.join(missing_vars)}")
        print("環境変数ファイル(.env)を確認してください。")
        sys.exit(1)
    
    return {
        'slack_bot_token': os.getenv('SLACK_BOT_TOKEN'),
        'slack_channel_id': os.getenv('SLACK_CHANNEL_ID'),
        'openai_api_key': os.getenv('OPENAI_API_KEY'),
        'line_channel_access_token': os.getenv('LINE_CHANNEL_ACCESS_TOKEN'),
        'line_user_id': os.getenv('LINE_USER_ID'),  # 任意
        'summary_time_range_hours': int(os.getenv('SUMMARY_TIME_RANGE_HOURS', '12'))
    }


def save_log(start_time: datetime, end_time: datetime, items_count: int, success: bool, error_msg: str = ""):
    """ログをJSONLファイルに保存"""
    log_dir = Path("runlogs")
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / f"{start_time.strftime('%Y%m%d_%H%M')}.jsonl"
    
    log_entry = {
        "start": start_time.isoformat(),
        "end": end_time.isoformat(),
        "items": items_count,
        "ok": success,
        "err": error_msg
    }
    
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(description='Slack要約LINE送信CLI')
    parser.add_argument('--hours', type=int, help='要約対象時間（時間）')
    args = parser.parse_args()
    
    # 環境変数読み込み
    env = load_environment()
    
    # 時間設定（引数 > 環境変数 > デフォルト）
    hours = args.hours if args.hours is not None else env['summary_time_range_hours']
    
    start_time = datetime.now()
    error_msg = ""
    
    try:
        print(f"Slack要約LINE送信を開始します（直近{hours}時間）...")
        
        # Slackクライアント初期化
        print("Slackメッセージを取得中...")
        slack_client = SlackClient(env['slack_bot_token'])
        messages = slack_client.fetch_messages(env['slack_channel_id'], hours)
        
        print(f"取得したメッセージ数: {len(messages)}件")
        
        # メッセージが0件の場合
        if not messages:
            summary_text = f"直近{hours}時間、新着なし"
        else:
            # OpenAI要約
            print("OpenAIで要約中...")
            summarizer = Summarizer(env['openai_api_key'])
            summary = summarizer.summarize(messages)
            summary_text = f"【Slackまとめ（直近{hours}h）】\n\n{summary}"
        
        # LINE送信
        print("LINEに送信中...")
        line_client = LineClient(
            env['line_channel_access_token'],
            env['line_user_id']
        )
        line_client.send_text(summary_text)
        
        print("処理が完了しました。")
        
        # 成功ログ保存
        end_time = datetime.now()
        save_log(start_time, end_time, len(messages), True)
        
    except Exception as e:
        error_msg = str(e)
        print(f"エラーが発生しました: {error_msg}")
        
        # エラーログ保存
        end_time = datetime.now()
        save_log(start_time, end_time, 0, False, error_msg)
        
        sys.exit(1)


if __name__ == "__main__":
    main()
