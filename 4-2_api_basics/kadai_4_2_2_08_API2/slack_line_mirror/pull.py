"""Slack-LINE Mirror: Slackの新着メッセージをLINEへ通知"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

from .utils.env_loader import load_env, get_env_path, print_env_setup_help
from .utils.slack_client import fetch_new_messages, get_channel_info
from .utils.line_client import push_line_text, format_slack_message_for_line


def load_latest_ts(state_dir: Path) -> float:
    """
    最新のタイムスタンプを読み込み
    
    Args:
        state_dir: 状態ファイルディレクトリ
        
    Returns:
        最新タイムスタンプ。ファイルが存在しない場合は0.0
    """
    ts_file = state_dir / "slack_latest_ts.json"
    
    if not ts_file.exists():
        return 0.0
    
    try:
        with open(ts_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return float(data.get("latest_ts", 0.0))
    except (json.JSONDecodeError, ValueError, KeyError):
        return 0.0


def save_latest_ts(state_dir: Path, ts: float) -> None:
    """
    最新のタイムスタンプを保存
    
    Args:
        state_dir: 状態ファイルディレクトリ
        ts: 保存するタイムスタンプ
    """
    ts_file = state_dir / "slack_latest_ts.json"
    
    # ディレクトリが存在しない場合は作成
    state_dir.mkdir(parents=True, exist_ok=True)
    
    data = {"latest_ts": ts}
    
    with open(ts_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_channel_name(token: str, channel_id: str) -> str:
    """
    チャンネル名を取得（表示用）
    
    Args:
        token: Slack Bot Token
        channel_id: チャンネルID
        
    Returns:
        チャンネル名。取得に失敗した場合はチャンネルIDを返す
    """
    channel_info = get_channel_info(token, channel_id)
    if channel_info:
        return channel_info.get("name", channel_id)
    return channel_id


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(
        description="Slackの特定チャンネルの新着メッセージをLINEへ通知",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python -m kadai_4_2_2_08_API2.slack_line_mirror.pull
  python -m kadai_4_2_2_08_API2.slack_line_mirror.pull --channel CXXXXXXXX --limit 100
        """
    )
    
    parser.add_argument(
        "--channel", "-c",
        type=str,
        help="SlackチャンネルID (Cで始まる)。未指定時は.envのSLACK_CHANNEL_IDを使用"
    )
    
    parser.add_argument(
        "--limit", "-l",
        type=int,
        default=50,
        help="取得するメッセージ数の上限 (デフォルト: 50)"
    )
    
    args = parser.parse_args()
    
    try:
        # 環境変数を読み込み
        env_path = get_env_path()
        env_vars = load_env(env_path)
        
    except FileNotFoundError:
        print_env_setup_help()
        sys.exit(1)
    except ValueError as e:
        print(f"環境設定エラー: {e}", file=sys.stderr)
        sys.exit(1)
    
    # チャンネルIDを決定
    channel_id = args.channel or env_vars["SLACK_CHANNEL_ID"]
    
    # 状態ディレクトリのパスを取得
    state_dir = Path(__file__).resolve().parent / "state"
    
    # 最新タイムスタンプを読み込み
    oldest_ts = load_latest_ts(state_dir)
    
    try:
        # Slackからメッセージを取得
        print(f"Slackチャンネル {channel_id} から新着メッセージを取得中...")
        messages = fetch_new_messages(
            token=env_vars["SLACK_BOT_TOKEN"],
            channel_id=channel_id,
            oldest_ts=oldest_ts,
            limit=args.limit
        )
        
        total_fetched = len(messages)
        new_count = len([msg for msg in messages if float(msg["ts"]) > oldest_ts])
        
        print(f"[OK] Slack fetched: {total_fetched} messages (new={new_count})")
        
        if not messages:
            print("新着メッセージはありません")
            return
        
        # チャンネル名を取得
        channel_name = get_channel_name(env_vars["SLACK_BOT_TOKEN"], channel_id)
        
        # LINEにメッセージを送信
        success_count = 0
        failed_messages = []
        
        for msg in messages:
            # メッセージをLINE用に整形
            formatted_text = format_slack_message_for_line(
                channel_name=channel_name,
                user_id=msg["user"],
                text=msg["text"],
                permalink=msg["permalink"]
            )
            
            # LINEに送信
            result = push_line_text(
                token=env_vars["LINE_CHANNEL_ACCESS_TOKEN"],
                to=env_vars["LINE_TO_USER_ID"],
                text=formatted_text
            )
            
            if result["ok"]:
                success_count += 1
            else:
                failed_messages.append({
                    "ts": msg["ts"],
                    "user": msg["user"],
                    "error": result["error"]
                })
        
        print(f"[OK] LINE pushed: {success_count} / {len(messages)}")
        
        # 失敗したメッセージがあれば警告表示
        if failed_messages:
            print(f"[WARN] {len(failed_messages)} 件のLINE送信に失敗しました:")
            for failed in failed_messages:
                print(f"  [{failed['ts']}] {failed['user']}: {failed['error']}")
        
        # 最新タイムスタンプを更新
        if messages:
            latest_ts = max(float(msg["ts"]) for msg in messages)
            save_latest_ts(state_dir, latest_ts)
            print(f"[OK] latest_ts updated: {latest_ts}")
        
    except KeyboardInterrupt:
        print("\n処理が中断されました", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"予期しないエラー: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
