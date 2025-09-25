#!/usr/bin/env python3
"""
Zoom Server-to-Server OAuth: 会議作成スクリプト

使用例:
    python 4-2-2/02_zoom_create_meeting.py --topic "テスト会議" --duration 60
    python 4-2-2/02_zoom_create_meeting.py --topic "緊急会議" --start "2025-09-20T09:00:00Z" --duration 30
"""

import argparse
import base64
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests

from utils.env_loader import load_env

# Zoom API設定
ZOOM_TOKEN_URL = "https://zoom.us/oauth/token"
ZOOM_MEETINGS_URL = "https://api.zoom.us/v2/users/{user_id}/meetings"


class ZoomMeetingCreator:
    """Zoom Server-to-Server OAuthを使用した会議作成クラス"""

    def __init__(self, account_id: str, client_id: str, client_secret: str, user_id: str):
        self.account_id = account_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.user_id = user_id
        self.access_token = None

    def get_access_token(self) -> str:
        """Server-to-Server OAuthでアクセストークンを取得する"""
        # Basic認証用のヘッダーを作成
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()

        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/x-www-form-urlencoded"
        }

        data = {
            "grant_type": "account_credentials",
            "account_id": self.account_id
        }

        try:
            response = requests.post(
                ZOOM_TOKEN_URL,
                headers=headers,
                data=data,
                timeout=20
            )

            if response.ok:
                token_data = response.json()
                self.access_token = token_data["access_token"]
                return self.access_token
            else:
                error_detail = response.text
                try:
                    error_detail = json.dumps(response.json(), indent=2, ensure_ascii=False)
                except Exception:
                    pass
                raise RuntimeError(f"HTTP {response.status_code}\nURL: {response.url}\nRESPONSE: {error_detail}")

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"リクエストエラー: {e}") from e

    def create_meeting(self, topic: str, start_time: str, duration: int) -> dict:
        """会議を作成する"""
        if not self.access_token:
            self.get_access_token()

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        meeting_data = {
            "topic": topic,
            "type": 2,  # スケジュールされた会議
            "start_time": start_time,
            "duration": duration,
            "settings": {
                "join_before_host": True,
                "approval_type": 2  # 承認不要
            }
        }

        url = ZOOM_MEETINGS_URL.format(user_id=self.user_id)

        try:
            response = requests.post(
                url,
                headers=headers,
                json=meeting_data,
                timeout=20
            )

            if response.ok:
                return response.json()
            else:
                error_detail = response.text
                try:
                    error_detail = json.dumps(response.json(), indent=2, ensure_ascii=False)
                except Exception:
                    pass
                raise RuntimeError(f"HTTP {response.status_code}\nURL: {response.url}\nRESPONSE: {error_detail}")

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"リクエストエラー: {e}") from e


def load_zoom_config() -> tuple[str, str, str, str]:
    """Zoom設定を読み込む"""
    script_dir = Path(__file__).resolve().parent
    env_path = script_dir / "env" / "zoom.env"
    env = load_env(str(env_path))

    account_id = env.get("ZOOM_ACCOUNT_ID")
    client_id = env.get("ZOOM_CLIENT_ID")
    client_secret = env.get("ZOOM_CLIENT_SECRET")
    user_id = env.get("ZOOM_USER_ID")

    if not all([account_id, client_id, client_secret, user_id]):
        missing = [key for key, value in [
            ("ZOOM_ACCOUNT_ID", account_id),
            ("ZOOM_CLIENT_ID", client_id),
            ("ZOOM_CLIENT_SECRET", client_secret),
            ("ZOOM_USER_ID", user_id)
        ] if not value]
        raise RuntimeError(f"以下の環境変数が設定されていません: {', '.join(missing)}")

    return account_id, client_id, client_secret, user_id


def parse_arguments() -> argparse.Namespace:
    """コマンドライン引数を解析する"""
    parser = argparse.ArgumentParser(description="Zoom Server-to-Server OAuthを使用した会議作成")
    parser.add_argument("--topic", default="APIテスト会議", help="会議のトピック（デフォルト: APIテスト会議）")
    parser.add_argument("--start", help="開始時刻（ISO8601 UTC形式、例: 2025-09-20T09:00:00Z）。未指定の場合は現在時刻+10分")
    parser.add_argument("--duration", type=int, default=30, help="会議の時間（分、デフォルト: 30）")
    return parser.parse_args()


def validate_arguments(args: argparse.Namespace) -> None:
    """引数のバリデーション"""
    if args.duration < 1:
        raise ValueError("durationは1分以上である必要があります")


def format_start_time(start_time_str: str = None) -> str:
    """開始時刻をISO8601 UTC形式にフォーマットする"""
    if start_time_str:
        # 入力された時刻をそのまま使用（バリデーションは簡易的）
        if not start_time_str.endswith('Z'):
            raise ValueError("start_timeはISO8601 UTC形式（末尾にZ）で指定してください")
        return start_time_str
    else:
        # 現在時刻+10分をISO8601 UTC形式で返す
        now = datetime.now(timezone.utc)
        start_time = now + timedelta(minutes=10)
        return start_time.strftime("%Y-%m-%dT%H:%M:%SZ")


def main() -> None:
    try:
        args = parse_arguments()
        validate_arguments(args)
        
        start_time = format_start_time(args.start)
        account_id, client_id, client_secret, user_id = load_zoom_config()
        
        creator = ZoomMeetingCreator(account_id, client_id, client_secret, user_id)
        meeting = creator.create_meeting(args.topic, start_time, args.duration)
        
        # 成功時の出力（id, password, join_urlを含む）
        result = {
            "id": meeting.get("id"),
            "password": meeting.get("password"),
            "join_url": meeting.get("join_url"),
            "topic": meeting.get("topic"),
            "start_time": meeting.get("start_time"),
            "duration": meeting.get("duration")
        }
        
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"エラー: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
