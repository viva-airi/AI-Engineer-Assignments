"""
LINE送信機能
"""
import time
import requests
from typing import Optional


class LineClient:
    def __init__(self, channel_access_token: str, user_id: Optional[str] = None):
        """
        LINEクライアントを初期化
        
        Args:
            channel_access_token: LINE Channel Access Token
            user_id: 特定のユーザーに送信する場合のUser ID（Noneの場合はbroadcast）
        """
        self.channel_access_token = channel_access_token
        self.user_id = user_id
        self.headers = {
            'Authorization': f'Bearer {channel_access_token}',
            'Content-Type': 'application/json'
        }
    
    def send_text(self, text: str) -> None:
        """
        テキストメッセージを送信
        
        Args:
            text: 送信するテキスト
            
        Raises:
            Exception: LINE API呼び出しでエラーが発生した場合
        """
        retry_count = 0
        max_retries = 3
        
        while retry_count < max_retries:
            try:
                if self.user_id:
                    # 特定のユーザーにpush送信
                    url = 'https://api.line.me/v2/bot/message/push'
                    data = {
                        'to': self.user_id,
                        'messages': [{
                            'type': 'text',
                            'text': text
                        }]
                    }
                else:
                    # 全ユーザーにbroadcast送信
                    url = 'https://api.line.me/v2/bot/message/broadcast'
                    data = {
                        'messages': [{
                            'type': 'text',
                            'text': text
                        }]
                    }
                
                response = requests.post(
                    url,
                    headers=self.headers,
                    json=data,
                    timeout=15
                )
                
                if response.status_code == 200:
                    print("LINE送信が完了しました。")
                    return
                elif response.status_code in [429, 500, 502, 503, 504]:
                    # レート制限やサーバーエラーの場合はリトライ
                    retry_count += 1
                    if retry_count < max_retries:
                        wait_time = 2 ** retry_count  # 指数的バックオフ
                        print(f"LINE API エラー (リトライ {retry_count}/{max_retries}): {response.status_code}")
                        print(f"{wait_time}秒待機中...")
                        time.sleep(wait_time)
                        continue
                else:
                    # その他のエラー
                    error_msg = response.text if response.text else f"HTTP {response.status_code}"
                    raise Exception(f"LINE送信でエラーが発生しました: {error_msg}")
                    
            except requests.exceptions.RequestException as e:
                retry_count += 1
                if retry_count < max_retries:
                    wait_time = 2 ** retry_count
                    print(f"LINE送信でネットワークエラー (リトライ {retry_count}/{max_retries}): {e}")
                    print(f"{wait_time}秒待機中...")
                    time.sleep(wait_time)
                    continue
                else:
                    raise Exception(f"LINE送信でネットワークエラーが発生しました: {str(e)}")
        
        raise Exception("LINE送信が最大リトライ回数に達しました。")
