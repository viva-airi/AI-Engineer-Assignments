#!/usr/bin/env python3
"""
LINE Messaging API: プッシュメッセージ送信（SDK非依存・HTTP直叩き版）
使い方:
    python 4-2-2/07_line_push.py "メッセージ本文"
"""

import argparse
import sys
from pathlib import Path
import requests

from utils.env_loader import load_env


def line_push(text: str) -> None:
    # .env 読み込み（スクリプト基準で固定）
    script_dir = Path(__file__).resolve().parent
    env_path = script_dir / "env" / "line.env"
    env = load_env(str(env_path))

    token = env.get("LINE_CHANNEL_ACCESS_TOKEN")
    user_id = env.get("LINE_USER_ID")

    if not token:
        raise RuntimeError("LINE_CHANNEL_ACCESS_TOKEN が設定されていません")
    if not user_id:
        raise RuntimeError("LINE_USER_ID が設定されていません")

    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=utf-8",
    }
    body = {
        "to": user_id,
        "messages": [{"type": "text", "text": text}],
    }

    r = requests.post(url, headers=headers, json=body, timeout=20)
    if r.ok:
        print("OK")
        return

    # 失敗時は詳細を表示
    raise RuntimeError(
        f"HTTP {r.status_code}\nURL: {r.url}\nRESPONSE: {r.text}"
    )


def main() -> None:
    p = argparse.ArgumentParser(description="LINE プッシュ送信（HTTP版）")
    p.add_argument("message", help="送信するメッセージ（必須）")
    args = p.parse_args()

    try:
        line_push(args.message)
    except Exception as e:
        print(f"エラー: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
