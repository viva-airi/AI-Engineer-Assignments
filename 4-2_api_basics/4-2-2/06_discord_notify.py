#!/usr/bin/env python3
"""
Discord Webhook通知スクリプト

DiscordのWebhookを使用してメッセージを送信します。
環境変数からWebhook URLを読み込み、CLIからメッセージを送信できます。
"""

import argparse
import requests
import sys
from pathlib import Path
from typing import Optional

# プロジェクトルートからの相対パスでutilsをインポート
sys.path.append(str(Path(__file__).resolve().parent))
from utils.env_loader import load_env


def send_discord(message: str, username: Optional[str] = None) -> None:
    """
    Discord Webhookを使用してメッセージを送信する
    
    Args:
        message: 送信するメッセージ
        username: 送信者のユーザー名（任意）
    
    Raises:
        FileNotFoundError: .envファイルが見つからない場合
        requests.RequestException: ネットワークエラーまたはHTTPエラーの場合
    """
    # 環境変数を読み込み
    env_path = Path(__file__).resolve().parent / "env" / "discord.env"
    env = load_env(str(env_path))
    
    webhook_url = env.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        raise ValueError("DISCORD_WEBHOOK_URLが設定されていません")
    
    # メッセージ長制限チェック（Discordの制限は2000文字）
    if len(message) > 2000:
        print(f"警告: メッセージが2000文字を超えています（{len(message)}文字）。先頭2000文字に切り詰めます。")
        message = message[:2000]
    
    # 送信データを構築
    data = {"content": message}
    if username:
        data["username"] = username
    
    try:
        # Discord WebhookにPOSTリクエストを送信
        response = requests.post(
            webhook_url,
            json=data,
            timeout=20
        )
        
        # 成功ステータスチェック
        if response.status_code not in [200, 204]:
            raise requests.HTTPError(
                f"HTTPエラー: {response.status_code}\n"
                f"レスポンス本文: {response.text}\n"
                f"URL: {webhook_url}"
            )
        
        print("OK")
        
    except requests.exceptions.Timeout:
        raise requests.RequestException("リクエストがタイムアウトしました（20秒）")
    except requests.exceptions.ConnectionError:
        raise requests.RequestException("ネットワーク接続エラーが発生しました")
    except requests.exceptions.RequestException as e:
        raise requests.RequestException(f"リクエストエラー: {e}")


def main():
    """CLIエントリーポイント"""
    parser = argparse.ArgumentParser(
        description="Discord Webhookを使用してメッセージを送信します",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python 06_discord_notify.py "テスト通知"
  python 06_discord_notify.py "テスト通知" --username "Bot"
        """
    )
    
    parser.add_argument(
        "message",
        help="送信するメッセージ（必須）"
    )
    
    parser.add_argument(
        "--username",
        help="送信者のユーザー名（任意）"
    )
    
    args = parser.parse_args()
    
    try:
        send_discord(args.message, args.username)
    except (FileNotFoundError, ValueError, requests.RequestException) as e:
        print(f"エラー: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
