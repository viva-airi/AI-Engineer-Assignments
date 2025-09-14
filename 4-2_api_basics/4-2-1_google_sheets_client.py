"""
Google Sheets API クライアント
最小実装版
"""

import os
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

# Google Sheets API のスコープ
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

class GoogleSheetsClient:
    def __init__(self):
        """Google Sheets クライアントを初期化"""
        self.gc = None
        self.spreadsheet = None
        self.worksheet = None
        
        self.spreadsheet_id = os.getenv('SPREADSHEET_ID')
        self.worksheet_name = os.getenv('WORKSHEET_NAME', 'Sheet1')
        
        if not self.spreadsheet_id:
            raise ValueError("SPREADSHEET_ID が設定されていません。.envファイルを確認してください。")
        
        self._authenticate()
    
    def _authenticate(self):
        """Google API認証を実行"""
        cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if not cred_path:
            raise ValueError("GOOGLE_APPLICATION_CREDENTIALS が設定されていません。.envファイルを確認してください。")
        
        if not os.path.exists(cred_path):
            raise FileNotFoundError(f"認証情報ファイルが見つかりません: {cred_path}")
        
        creds = Credentials.from_service_account_file(cred_path, scopes=SCOPES)
        self.gc = gspread.authorize(creds)
        
        # スプレッドシートとワークシートを開く
        self.spreadsheet = self.gc.open_by_key(self.spreadsheet_id)
        self.worksheet = self.spreadsheet.worksheet(self.worksheet_name)
    
    def read_range(self, range_name: str = None) -> list:
        """
        指定された範囲のデータを読み取り
        
        Args:
            range_name (str): 読み取る範囲（例: 'A1:C10'）。Noneの場合は全データを読み取り
            
        Returns:
            list: 読み取ったデータ
        """
        try:
            if range_name:
                return self.worksheet.get(range_name)
            else:
                return self.worksheet.get_all_values()
            
        except Exception as e:
            print(f"データ読み取りエラー: {e}")
            return []
    
    def write_range(self, range_name: str, values: list) -> bool:
        """
        指定された範囲にデータを書き込み
        
        Args:
            range_name (str): 書き込む範囲（例: 'A1:C10'）
            values (list): 書き込むデータ
            
        Returns:
            bool: 成功した場合True
        """
        try:
            self.worksheet.update(range_name, values)
            print(f"データが更新されました: {range_name}")
            return True
            
        except Exception as e:
            print(f"データ書き込みエラー: {e}")
            return False
    
    def append_row(self, values: list) -> bool:
        """
        ワークシートに新しい行を追加
        
        Args:
            values (list): 追加するデータ
            
        Returns:
            bool: 成功した場合True
        """
        try:
            self.worksheet.append_row(values)
            print(f"新しい行が追加されました: {values}")
            return True
            
        except Exception as e:
            print(f"行追加エラー: {e}")
            return False
    
    def get_sheet_info(self) -> dict:
        """
        スプレッドシートの基本情報を取得
        
        Returns:
            dict: スプレッドシート情報
        """
        try:
            return {
                'title': self.spreadsheet.title,
                'worksheet_name': self.worksheet.title,
                'worksheet_id': self.worksheet.id,
                'row_count': self.worksheet.row_count,
                'col_count': self.worksheet.col_count
            }
            
        except Exception as e:
            print(f"シート情報取得エラー: {e}")
            return {}

def main():
    """テスト用のメイン関数"""
    try:
        # クライアントを初期化
        sheets = GoogleSheetsClient()
        
        # スプレッドシート情報を取得
        print("スプレッドシート情報:")
        info = sheets.get_sheet_info()
        print(f"タイトル: {info.get('title', 'N/A')}")
        print(f"ワークシート名: {info.get('worksheet_name', 'N/A')}")
        print(f"行数: {info.get('row_count', 'N/A')}")
        print(f"列数: {info.get('col_count', 'N/A')}")
        print("-" * 50)
        
        # データを読み取り（A1:C5の範囲）
        print("データ読み取りテスト (A1:C5):")
        data = sheets.read_range('A1:C5')
        for i, row in enumerate(data, 1):
            print(f"行{i}: {row}")
        print("-" * 50)
        
        # ヘッダー行を書き込み（A1:C1の範囲）
        print("ヘッダー書き込みテスト:")
        header_data = [['名前', '年齢', '住所']]
        success = sheets.write_range('A1:C1', header_data)
        if success:
            print("ヘッダー書き込み成功")
        else:
            print("ヘッダー書き込み失敗")
        print("-" * 50)
        
        # データ行を追加
        print("データ行追加テスト:")
        data1 = ["田中太郎", "25", "東京都"]
        data2 = ["佐藤花子", "30", "大阪府"]
        data3 = ["鈴木一郎", "28", "愛知県"]
        
        for data in [data1, data2, data3]:
            success = sheets.append_row(data)
            if success:
                print(f"データ追加成功: {data}")
            else:
                print(f"データ追加失敗: {data}")
        print("-" * 50)
        
    except Exception as e:
        print(f"エラー: {e}")
        print("環境変数と認証情報が正しく設定されているか確認してください。")

if __name__ == "__main__":
    main()
