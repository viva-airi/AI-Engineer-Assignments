"""LINE Messaging API クライアント"""

import requests
from typing import Dict, Optional


def push_line_text(token: str, to: str, text: str) -> Dict:
    """
    LINE Messaging API v2 を使用してテキストメッセージを送信
    
    Args:
        token: LINE Channel Access Token
        to: 送信先ユーザーID
        text: 送信するテキスト
        
    Returns:
        レスポンス情報の辞書:
        {
            "status": int,           # HTTPステータスコード
            "ok": bool,              # 送信成功フラグ
            "error": Optional[str]   # エラーメッセージ（失敗時）
        }
    """
    url = "https://api.line.me/v2/bot/message/push"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "to": to,
        "messages": [
            {
                "type": "text",
                "text": text
            }
        ]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        result = {
            "status": response.status_code,
            "ok": response.status_code == 200,
            "error": None
        }
        
        if not result["ok"]:
            try:
                error_data = response.json()
                result["error"] = error_data.get("message", f"HTTP {response.status_code}")
            except (ValueError, KeyError):
                result["error"] = f"HTTP {response.status_code}: {response.text}"
        
        return result
        
    except requests.exceptions.Timeout:
        return {
            "status": 408,
            "ok": False,
            "error": "Request timeout"
        }
    except requests.exceptions.RequestException as e:
        return {
            "status": 0,
            "ok": False,
            "error": f"Request error: {str(e)}"
        }


def format_slack_message_for_line(channel_name: str, user_id: str, text: str, permalink: str, max_length: int = 1000) -> str:
    """
    SlackメッセージをLINE用に整形
    
    Args:
        channel_name: チャンネル名（表示用）
        user_id: ユーザーID
        text: メッセージ本文
        permalink: Slackパーマリンク
        max_length: 最大文字数（LINEの制限を考慮）
        
    Returns:
        整形されたメッセージテキスト
    """
    # 基本フォーマット: [#channel] user: text
    base_text = f"[#{channel_name}] {user_id}: {text}"
    
    # 文字数制限チェック
    if len(base_text) <= max_length:
        # パーマリンクを追加
        if permalink:
            return f"{base_text}\n{permalink}"
        else:
            return base_text
    else:
        # 長すぎる場合は省略
        available_length = max_length - 50  # 省略表示とパーマリンク用に余裕を持たせる
        truncated_text = text[:available_length] + "..."
        formatted_text = f"[#{channel_name}] {user_id}: {truncated_text}"
        
        if permalink:
            return f"{formatted_text}\n{permalink}"
        else:
            return formatted_text


def get_user_profile(token: str, user_id: str) -> Optional[Dict]:
    """
    LINEユーザープロフィールを取得（送信前にユーザーIDの有効性確認用）
    
    Args:
        token: LINE Channel Access Token
        user_id: ユーザーID
        
    Returns:
        ユーザープロフィール情報。取得に失敗した場合はNone
    """
    url = f"https://api.line.me/v2/bot/profile/{user_id}"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            return None
            
    except requests.exceptions.RequestException:
        return None


if __name__ == "__main__":
    # テスト用
    import os
    from dotenv import load_dotenv
    
    # 環境変数を読み込み（テスト用）
    load_dotenv()
    token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
    user_id = os.getenv("LINE_TO_USER_ID")
    
    if not token or not user_id:
        print("環境変数 LINE_CHANNEL_ACCESS_TOKEN または LINE_TO_USER_ID が設定されていません")
        exit(1)
    
    # テストメッセージを送信
    test_message = "Slack-LINE Mirror のテストメッセージです。"
    result = push_line_text(token, user_id, test_message)
    
    print(f"送信結果: {result}")
    
    if result["ok"]:
        print("LINE送信成功")
    else:
        print(f"LINE送信失敗: {result['error']}")
