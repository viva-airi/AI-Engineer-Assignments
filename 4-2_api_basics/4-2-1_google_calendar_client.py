"""
Google Calendar API クライアント
最小実装版
"""

import os
from datetime import datetime, timedelta
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

# Google Calendar API のスコープ
SCOPES = ['https://www.googleapis.com/auth/calendar']

class GoogleCalendarClient:
    def __init__(self):
        """Google Calendar クライアントを初期化"""
        self.service = None
        self.calendar_id = os.getenv('CALENDAR_ID', 'vivaairi.06@gmail.com')
        
        self._authenticate()
    
    def _authenticate(self):
        """Google API認証を実行"""
        cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if not cred_path:
            raise ValueError("GOOGLE_APPLICATION_CREDENTIALS が設定されていません。.envファイルを確認してください。")
        
        if not os.path.exists(cred_path):
            raise FileNotFoundError(f"認証情報ファイルが見つかりません: {cred_path}")
        
        creds = Credentials.from_service_account_file(cred_path, scopes=SCOPES)
        self.service = build('calendar', 'v3', credentials=creds)
    
    def get_events(self, max_results: int = 10, time_min: datetime = None) -> list:
        """
        イベント一覧を取得
        
        Args:
            max_results (int): 取得する最大イベント数
            time_min (datetime): 取得開始時刻
            
        Returns:
            list: イベント一覧
        """
        try:
            if time_min is None:
                time_min = datetime.utcnow()
            
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=time_min.isoformat() + 'Z',
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            return events
            
        except Exception as e:
            print(f"イベント取得エラー: {e}")
            return []
    
    def create_event(self, summary: str, start_time: datetime, 
                    end_time: datetime, description: str = None) -> dict:
        """
        新しいイベントを作成
        
        Args:
            summary (str): イベントのタイトル
            start_time (datetime): 開始時刻
            end_time (datetime): 終了時刻
            description (str): イベントの説明
            
        Returns:
            dict: 作成されたイベント情報
        """
        try:
            event = {
                'summary': summary,
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': 'Asia/Tokyo',
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'Asia/Tokyo',
                },
            }
            
            if description:
                event['description'] = description
            
            created_event = self.service.events().insert(
                calendarId=self.calendar_id,
                body=event
            ).execute()
            
            print(f"イベントが作成されました: {created_event.get('htmlLink')}")
            return created_event
            
        except Exception as e:
            print(f"イベント作成エラー: {e}")
            return {}
    

def main():
    """テスト用のメイン関数"""
    try:
        # クライアントを初期化
        calendar = GoogleCalendarClient()
        
        # 今後のイベントを取得
        print("今後のイベント (最大5件):")
        events = calendar.get_events(max_results=5)
        
        if not events:
            print("イベントが見つかりませんでした。")
        else:
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                print(f"- {event.get('summary', 'No Title')} ({start})")
        print("-" * 50)
        
        # テストイベントを作成（1時間後から2時間後）
        print("テストイベント作成:")
        now = datetime.now()
        start_time = now + timedelta(hours=1)
        end_time = now + timedelta(hours=2)
        
        test_event = calendar.create_event(
            summary="テストイベント",
            start_time=start_time,
            end_time=end_time,
            description="これはテスト用のイベントです。"
        )
        
        if test_event:
            print("テストイベントが正常に作成されました。")
            print(f"イベントID: {test_event.get('id')}")
        
    except Exception as e:
        print(f"エラー: {e}")
        print("環境変数と認証情報が正しく設定されているか確認してください。")

if __name__ == "__main__":
    main()
