#!/usr/bin/env python3
"""
Google Docs API クライアント
新規ドキュメント作成＋テキスト挿入
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# スコープ
SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive.file",
]

# 認証情報の場所
CREDENTIALS_FILE = "credentials/google_credentials.json"
TOKEN_FILE = "tokens/token.json"


def get_credentials():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w", encoding="utf-8") as token:
            token.write(creds.to_json())
    return creds


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--title", required=True, help="新しいドキュメントのタイトル")
    parser.add_argument("--text", required=True, help="挿入するテキスト")
    parser.add_argument("--folder-id", help="保存先フォルダID")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO if args.verbose else logging.ERROR)

    creds = get_credentials()
    docs_service = build("docs", "v1", credentials=creds)
    drive_service = build("drive", "v3", credentials=creds)

    # ドキュメント作成
    doc = docs_service.documents().create(body={"title": args.title}).execute()
    document_id = doc.get("documentId")

    # テキスト挿入
    requests = [
        {
            "insertText": {
                "location": {"index": 1},
                "text": args.text,
            }
        }
    ]
    docs_service.documents().batchUpdate(
        documentId=document_id, body={"requests": requests}
    ).execute()

    # フォルダ移動（必要なら）
    if args.folder_id:
        drive_service.files().update(
            fileId=document_id,
            addParents=args.folder_id,
            fields="id, parents",
        ).execute()

    document_url = f"https://docs.google.com/document/d/{document_id}/edit"

    result = {
        "documentId": document_id,
        "title": args.title,
        "documentUrl": document_url,
        "folderId": args.folder_id,
        "insertedChars": len(args.text),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
