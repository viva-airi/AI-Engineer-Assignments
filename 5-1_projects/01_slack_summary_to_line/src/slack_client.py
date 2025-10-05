"""
Slackクライアント - メッセージ取得機能
"""
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


class SlackClient:
    def __init__(self, bot_token: str):
        """
        Slackクライアントを初期化
        
        Args:
            bot_token: Slack Bot Token
        """
        self.client = WebClient(token=bot_token)
    
    def fetch_messages(self, channel_id: str, hours: int) -> List[Dict[str, Any]]:
        """
        指定されたチャンネルから直近N時間のメッセージを取得
        
        Args:
            channel_id: SlackチャンネルID
            hours: 取得する時間範囲（時間）
            
        Returns:
            メッセージのリスト（ts, user, textを含む）
            
        Raises:
            SlackApiError: Slack API呼び出しでエラーが発生した場合
        """
        # 取得開始時刻を計算
        start_time = datetime.now() - timedelta(hours=hours)
        start_timestamp = start_time.timestamp()
        
        messages = []
        cursor = None
        retry_count = 0
        max_retries = 3
        
        while retry_count < max_retries:
            try:
                # メッセージ履歴を取得
                response = self.client.conversations_history(
                    channel=channel_id,
                    oldest=str(start_timestamp),
                    cursor=cursor,
                    limit=1000
                )
                
                # メッセージを整形
                for message in response['messages']:
                    # ボットメッセージやシステムメッセージは除外
                    if message.get('subtype') in ['bot_message', 'system']:
                        continue
                    
                    # 必要な情報のみ抽出
                    formatted_message = {
                        'ts': message.get('ts'),
                        'user': message.get('user', 'unknown'),
                        'text': message.get('text', ''),
                        'thread_ts': message.get('thread_ts')  # スレッドメッセージの場合は親メッセージのts
                    }
                    messages.append(formatted_message)
                
                # 次のページがあるかチェック
                if not response.get('has_more', False):
                    break
                    
                cursor = response.get('response_metadata', {}).get('next_cursor')
                if not cursor:
                    break
                    
                # レート制限を避けるため少し待機
                time.sleep(0.1)
                
            except SlackApiError as e:
                if e.response['status_code'] in [429, 500, 502, 503, 504]:
                    # レート制限やサーバーエラーの場合はリトライ
                    retry_count += 1
                    if retry_count < max_retries:
                        wait_time = 2 ** retry_count  # 指数的バックオフ
                        print(f"Slack API エラー (リトライ {retry_count}/{max_retries}): {e}")
                        print(f"{wait_time}秒待機中...")
                        time.sleep(wait_time)
                        continue
                raise e
        
        # タイムスタンプでソート（古い順）
        messages.sort(key=lambda x: float(x['ts']))
        
        return messages
