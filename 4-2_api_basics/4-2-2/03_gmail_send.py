#!/usr/bin/env python3
"""
Gmail API: メール送信スクリプト（UTF-8対応）

使用例:
    python 4-2-2/03_gmail_send.py --to "recipient@example.com" --subject "テスト" --body "メール本文"
"""

import argparse
import base64
import json
import sys
from pathlib import Path

import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr, formatdate, make_msgid

from utils.env_loader import load_env

# Gmail API設定
SCOPES = ['https://www.googleapis.com/auth/gmail.send']
GMAIL_API_URL = 'https://gmail.googleapis.com/gmail/v1/users/me/messages/send'


class GmailSender:
    """Gmail APIを使用したメール送信クラス"""

    def __init__(self, credentials_path: str, token_path: str, from_email: str):
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.from_email = from_email
        self.creds = None

    def authenticate(self) -> None:
        """OAuth認証を実行し、トークンを取得・保存する"""
        if Path(self.token_path).exists():
            self.creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)

        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                try:
                    self.creds.refresh(Request())
                except Exception:
                    self.creds = None

            if not self.creds:
                if not Path(self.credentials_path).exists():
                    raise FileNotFoundError(f"認証ファイルが見つかりません: {self.credentials_path}")

                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, SCOPES)
                self.creds = flow.run_local_server(port=0)

            Path(self.token_path).parent.mkdir(parents=True, exist_ok=True)
            with open(self.token_path, 'w', encoding='utf-8') as token:
                token.write(self.creds.to_json())

    def create_message(self, to_addr: str, subject: str, body: str) -> dict:
        """UTF-8のMIMEメールを組み立ててbase64urlでraw化"""
        # 本文（charset=utf-8）
        msg = MIMEText(body, _subtype="plain", _charset="utf-8")

        # ヘッダ（RFC 2047エンコード）
        # 表示名はここでは from_email と同じにしています。表示名を別にしたい場合は Header("表示名", "utf-8") を使ってください。
        msg["From"] = formataddr((str(Header(self.from_email, "utf-8")), self.from_email))
        msg["To"] = to_addr
        msg["Subject"] = str(Header(subject, "utf-8"))
        msg["Date"] = formatdate(localtime=True)
        msg["Message-ID"] = make_msgid()

        # Gmail API は base64url（+ → -, / → _, 末尾の=はそのままでOK）
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("ascii")
        return {"raw": raw}

    def send_mail(self, to_addr: str, subject: str, body: str) -> str:
        """メールを送信する"""
        self.authenticate()
        message = self.create_message(to_addr, subject, body)

        headers = {
            'Authorization': f'Bearer {self.creds.token}',
            'Content-Type': 'application/json',
        }

        try:
            response = requests.post(GMAIL_API_URL, headers=headers, json=message, timeout=30)
            if response.ok:
                return "OK"

            # 詳細エラーを整形
            error_detail = response.text
            try:
                error_detail = json.dumps(response.json(), indent=2, ensure_ascii=False)
            except Exception:
                pass

            raise RuntimeError(f"HTTP {response.status_code}\nURL: {response.url}\nRESPONSE: {error_detail}")

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"リクエストエラー: {e}") from e


def load_gmail_config() -> tuple[str, str, str]:
    """Gmail設定を読み込む"""
    script_dir = Path(__file__).resolve().parent

    env_path = script_dir / "env" / "gmail.env"
    env = load_env(str(env_path))

    from_email = env.get("GMAIL_FROM")
    if not from_email:
        raise RuntimeError("GMAIL_FROM が設定されていません")

    credentials_path = script_dir / "credentials" / "gmail_client_secret.json"
    token_path = script_dir / "tokens" / "gmail_token.json"

    return str(credentials_path), str(token_path), from_email


def parse_arguments() -> argparse.Namespace:
    """コマンドライン引数を解析する"""
    parser = argparse.ArgumentParser(description="Gmail APIを使用したメール送信")
    parser.add_argument("--to", required=True, help="宛先メールアドレス（必須）")
    parser.add_argument("--subject", required=True, help="件名（必須）")
    parser.add_argument("--body", required=True, help="本文（必須）")
    return parser.parse_args()


def main() -> None:
    try:
        args = parse_arguments()
        credentials_path, token_path, from_email = load_gmail_config()
        gmail_sender = GmailSender(credentials_path, token_path, from_email)
        result = gmail_sender.send_mail(args.to, args.subject, args.body)
        print(result)
    except Exception as e:
        print(f"エラー: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
