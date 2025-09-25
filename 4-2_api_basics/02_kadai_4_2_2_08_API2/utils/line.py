"""
LINE通知ユーティリティ
"""
import time
import requests
from typing import Tuple


def push_text(user_id: str, text: str, token: str, retry: int = 1) -> Tuple[bool, str]:
    """
    LINE Messaging API /push にテキスト送信
    
    Args:
        user_id: 送信先ユーザーID
        text: 送信テキスト
        token: チャンネルアクセストークン
        retry: リトライ回数（デフォルト1回）
        
    Returns:
        成功: (True, ""), 失敗: (False, "status=... body=...")
    """
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "to": user_id,
        "messages": [
            {
                "type": "text",
                "text": text
            }
        ]
    }
    
    max_attempts = retry + 1
    
    for attempt in range(max_attempts):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                return True, ""
            else:
                error_msg = f"status={response.status_code} body={response.text}"
                if attempt < max_attempts - 1:
                    time.sleep(1)  # 1秒待機してリトライ
                else:
                    return False, error_msg
                    
        except requests.exceptions.RequestException as e:
            error_msg = f"Request failed: {str(e)}"
            if attempt < max_attempts - 1:
                time.sleep(1)  # 1秒待機してリトライ
            else:
                return False, error_msg
    
    return False, "Unknown error"
