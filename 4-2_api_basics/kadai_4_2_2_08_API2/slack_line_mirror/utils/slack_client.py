"""Slack API クライアント"""

import requests
import sys
from typing import List, Dict, Optional


def _normalize_oldest(oldest_ts) -> Optional[str]:
    # 数値なら小数6桁で文字列化、文字列なら数値化できるか検証
    if isinstance(oldest_ts, (int, float)):
        if float(oldest_ts) <= 0:
            return None  # 0以下は oldest を送らない（Slackが 0 を嫌うケースの回避）
        return f"{float(oldest_ts):.6f}"
    if isinstance(oldest_ts, str):
        try:
            v = float(oldest_ts)
            if v <= 0:
                return None
            # Slackの message["ts"] をそのまま保存していれば、ここは素通しでOK
            return oldest_ts
        except ValueError:
            return None
    return None

def fetch_new_messages(token: str, channel_id: str, oldest_ts, limit: int = 50) -> List[Dict]:
    """
    ...
    oldest_ts: この時刻より新しいメッセージのみ取得（Slackの ts 文字列 or float）
            0 や None の場合はパラメータ送信しない（初回取得）
    """
    url = "https://slack.com/api/conversations.history"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    params = {"channel": channel_id, "limit": limit}
    norm = _normalize_oldest(oldest_ts)
    if norm is not None:
        params["oldest"] = norm  # ここでのみ oldest を付ける

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if not data.get("ok"):
            error = data.get("error", "unknown_error")
            print(f"Slack API エラー: {error}", file=sys.stderr)
            print(f"レスポンス: {data}", file=sys.stderr)
            sys.exit(3)

        messages = data.get("messages", [])
        formatted = []
        for msg in messages:
            if msg.get("subtype") or msg.get("bot_id"):
                continue
            formatted.append({
                "ts": msg["ts"],  # ← 文字列のまま保存（浮動小数にしない）
                "user": msg.get("user", "unknown"),
                "text": msg.get("text", ""),
                "permalink": _get_message_permalink(token, channel_id, msg["ts"]),
            })

        # 取得後のフィルタ（oldestを送っていない場合に備え、念のため二重にガード）
        try:
            threshold = float(norm) if norm is not None else 0.0
        except ValueError:
            threshold = 0.0
        new_messages = [m for m in formatted if float(m["ts"]) > threshold]
        new_messages.sort(key=lambda x: float(x["ts"]))
        return new_messages

    except requests.exceptions.RequestException as e:
        print(f"Slack API リクエストエラー: {e}", file=sys.stderr)
        sys.exit(3)



def _get_message_permalink(token: str, channel_id: str, ts: str) -> str:
    """
    メッセージのパーマリンクを取得する。

    Args:
        token: Slack Bot Token（例: "xoxb-..."）
        channel_id: SlackチャンネルID（例: "C09ESNU9XU7"）
        ts: メッセージのタイムスタンプ（例: "1726752000.0"）

    Returns:
        パーマリンクURL。取得に失敗した場合は空文字列
    """
    url = "https://slack.com/api/chat.getPermalink"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    params = {
        "channel": channel_id,
        "message_ts": ts
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()

        if data.get("ok"):
            return data.get("permalink", "")
        else:
            return ""

    except (requests.exceptions.RequestException, KeyError, ValueError):
        return ""


def get_channel_info(token: str, channel_id: str) -> Optional[Dict]:
    """
    チャンネル情報を取得する。

    Args:
        token: Slack Bot Token（例: "xoxb-..."）
        channel_id: SlackチャンネルID（例: "C09ESNU9XU7"）

    Returns:
        チャンネル情報の辞書。取得に失敗した場合は None
    """
    url = "https://slack.com/api/conversations.info"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    params = {
        "channel": channel_id
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()

        if data.get("ok"):
            return data.get("channel")
        else:
            return None

    except (requests.exceptions.RequestException, KeyError, ValueError):
        return None


if __name__ == "__main__":
    # テスト用
    import os
    from dotenv import load_dotenv

    # 環境変数を読み込み（テスト用）
    load_dotenv()
    token = os.getenv("SLACK_BOT_TOKEN")
    channel_id = os.getenv("SLACK_CHANNEL_ID")

    if not token or not channel_id:
        print("環境変数 SLACK_BOT_TOKEN または SLACK_CHANNEL_ID が設定されていません")
        sys.exit(1)

    # 最新のメッセージを取得（過去1時間分）
    import time
    oldest_ts = time.time() - 3600  # 1時間前

    print(f"チャンネル {channel_id} から過去1時間のメッセージを取得中...")
    messages = fetch_new_messages(token, channel_id, oldest_ts, limit=10)

    print(f"取得したメッセージ数: {len(messages)}")
    for msg in messages:
        print(f"  [{msg['ts']}] {msg['user']}: {msg['text'][:50]}...")
