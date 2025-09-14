"""
Google Meet クライアント
Google Calendar API を使用してGoogle Meet会議を作成
"""

import os
import sys
import json
import uuid
import argparse
from datetime import datetime
from typing import List, Optional, Dict, Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class GoogleMeetClient:
    """Google Meet クライアント"""
    
    # Google Calendar API のスコープ
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    
    def __init__(self, credentials_path: str, token_path: str, verbose: bool = False):
        """
        初期化
        
        Args:
            credentials_path (str): 認証情報ファイルのパス
            token_path (str): トークンファイルのパス
            verbose (bool): 詳細ログの有効/無効
        """
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.verbose = verbose
        self.service = None
        
        self._log("Google Meet クライアントを初期化中...")
        self._authenticate()
    
    def _log(self, message: str):
        """ログ出力（verbose モード時のみ）"""
        if self.verbose:
            print(f"[LOG] {message}")
    
    def _authenticate(self):
        """Google API認証を実行"""
        try:
            self._log("認証を開始...")
            
            # 認証情報ファイルの存在確認
            if not os.path.exists(self.credentials_path):
                raise FileNotFoundError(f"認証情報ファイルが見つかりません: {self.credentials_path}")
            
            creds = None
            
            # 既存のトークンファイルを確認
            if os.path.exists(self.token_path):
                self._log("既存のトークンを読み込み中...")
                creds = Credentials.from_authorized_user_file(self.token_path, self.SCOPES)
            
            # トークンが無効または存在しない場合、新しいトークンを取得
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    self._log("トークンを更新中...")
                    creds.refresh(Request())
                else:
                    self._log("新しいトークンを取得中...")
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, self.SCOPES)
                    creds = flow.run_local_server(port=0)
                
                # トークンを保存
                self._log(f"トークンを保存中: {self.token_path}")
                os.makedirs(os.path.dirname(self.token_path), exist_ok=True)
                with open(self.token_path, 'w') as token:
                    token.write(creds.to_json())
            
            # Google Calendar API サービスを構築
            self._log("Google Calendar API サービスを構築中...")
            self.service = build('calendar', 'v3', credentials=creds)
            self._log("認証が完了しました")
            
        except Exception as e:
            raise Exception(f"認証エラー: {e}")
    
    def create_meet_event(self, title: str, start_time: str, end_time: str, 
                         timezone: str = "Asia/Tokyo", description: str = None, 
                         attendees: List[str] = None) -> Dict[str, Any]:
        """
        Google Meet イベントを作成
        
        Args:
            title (str): イベントのタイトル
            start_time (str): 開始時刻 (ISO形式)
            end_time (str): 終了時刻 (ISO形式)
            timezone (str): タイムゾーン
            description (str): イベントの説明
            attendees (List[str]): 参加者のメールアドレスリスト
            
        Returns:
            Dict[str, Any]: 作成されたイベント情報
        """
        try:
            self._log(f"Google Meet イベントを作成中: {title}")
            
            # 参加者リストを準備
            attendee_list = []
            if attendees:
                for email in attendees:
                    attendee_list.append({'email': email.strip()})
                self._log(f"参加者: {', '.join(attendees)}")
            
            # 会議データの設定
            conference_data = {
                'createRequest': {
                    'requestId': str(uuid.uuid4())
                }
            }
            
            # イベントデータを構築
            event = {
                'summary': title,
                'start': {
                    'dateTime': start_time,
                    'timeZone': timezone,
                },
                'end': {
                    'dateTime': end_time,
                    'timeZone': timezone,
                },
                'conferenceData': conference_data,
                'conferenceDataVersion': 1,
            }
            
            if description:
                event['description'] = description
                self._log(f"説明: {description}")
            
            if attendee_list:
                event['attendees'] = attendee_list
            
            self._log("Google Calendar API にイベントを送信中...")
            
            # イベントを作成
            created_event = self.service.events().insert(
                calendarId='primary',
                body=event,
                conferenceDataVersion=1
            ).execute()
            
            self._log("イベントが正常に作成されました")
            
            # 結果を整形
            result = {
                'eventId': created_event.get('id'),
                'htmlLink': created_event.get('htmlLink'),
                'meetUrl': created_event.get('conferenceData', {}).get('entryPoints', [{}])[0].get('uri', ''),
                'start': created_event.get('start', {}).get('dateTime'),
                'end': created_event.get('end', {}).get('dateTime'),
                'timeZone': created_event.get('start', {}).get('timeZone')
            }
            
            self._log(f"結果: {json.dumps(result, ensure_ascii=False, indent=2)}")
            return result
            
        except HttpError as e:
            error_msg = f"Google Calendar API エラー: {e}"
            self._log(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"イベント作成エラー: {e}"
            self._log(error_msg)
            raise Exception(error_msg)


def parse_datetime(datetime_str: str) -> str:
    """
    日時文字列をISO形式に変換
    
    Args:
        datetime_str (str): 日時文字列 (例: "2024-01-01 10:00")
        
    Returns:
        str: ISO形式の日時文字列
    """
    try:
        # 複数の形式に対応
        formats = [
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d %H:%M:%S",
            "%Y/%m/%d %H:%M",
            "%Y/%m/%d %H:%M:%S",
            "%Y-%m-%dT%H:%M",
            "%Y-%m-%dT%H:%M:%S"
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(datetime_str, fmt)
                return dt.isoformat()
            except ValueError:
                continue
        
        raise ValueError(f"サポートされていない日時形式: {datetime_str}")
        
    except Exception as e:
        raise ValueError(f"日時解析エラー: {e}")


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description='Google Meet イベントを作成')
    parser.add_argument('--title', required=True, help='イベントのタイトル')
    parser.add_argument('--start', required=True, help='開始時刻 (例: "2024-01-01 10:00")')
    parser.add_argument('--end', required=True, help='終了時刻 (例: "2024-01-01 11:00")')
    parser.add_argument('--timezone', default='Asia/Tokyo', help='タイムゾーン (デフォルト: Asia/Tokyo)')
    parser.add_argument('--description', help='イベントの説明')
    parser.add_argument('--attendees', help='参加者のメールアドレス (カンマ区切り)')
    parser.add_argument('--verbose', action='store_true', help='詳細ログを表示')
    
    args = parser.parse_args()
    
    try:
        # パス設定
        script_dir = os.path.dirname(os.path.abspath(__file__))
        credentials_path = os.path.join(script_dir, 'credentials', 'google_credentials.json')
        token_path = os.path.join(script_dir, 'tokens', 'token.json')
        
        # クライアントを初期化
        client = GoogleMeetClient(credentials_path, token_path, args.verbose)
        
        # 日時をISO形式に変換
        start_time = parse_datetime(args.start)
        end_time = parse_datetime(args.end)
        
        # 参加者リストを準備
        attendees = None
        if args.attendees:
            attendees = [email.strip() for email in args.attendees.split(',')]
        
        # Google Meet イベントを作成
        result = client.create_meet_event(
            title=args.title,
            start_time=start_time,
            end_time=end_time,
            timezone=args.timezone,
            description=args.description,
            attendees=attendees
        )
        
        # 結果をJSON形式で出力
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
    except Exception as e:
        print(f"エラー: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
