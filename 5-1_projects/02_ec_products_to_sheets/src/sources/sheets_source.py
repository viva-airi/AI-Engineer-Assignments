"""
Google SheetsからASINリストを取得するソースクラス
"""

import os
from typing import List, Dict, Any
import gspread
from google.auth import default
from dotenv import load_dotenv


class SheetsSource:
    """Google Sheetsからデータを取得するソースクラス"""
    
    def __init__(self):
        """SheetsSourceを初期化する"""
        # .envファイルを読み込み
        load_dotenv()
        
        # 環境変数を取得
        self.spreadsheet_id = os.getenv('SPREADSHEET_ID')
        self.worksheet_asin_list = os.getenv('WORKSHEET_ASIN_LIST', 'ASIN_LIST')
        self.credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        
        if not self.spreadsheet_id:
            raise ValueError("SPREADSHEET_ID環境変数が設定されていません")
        
        if not self.credentials_path:
            raise ValueError("GOOGLE_APPLICATION_CREDENTIALS環境変数が設定されていません")
        
        # サービスアカウント認証でgspreadクライアントを初期化
        self._init_gspread_client()
        
        # スプレッドシートとワークシートを取得
        self._init_worksheets()
    
    def _init_gspread_client(self) -> None:
        """gspreadクライアントを初期化する"""
        try:
            # サービスアカウント認証
            gc = gspread.service_account(filename=self.credentials_path)
            self.gc = gc
        except Exception as e:
            raise RuntimeError(f"Google Sheets認証に失敗しました: {e}")
    
    def _init_worksheets(self) -> None:
        """スプレッドシートとワークシートを初期化する"""
        try:
            # スプレッドシートを開く
            self.spreadsheet = self.gc.open_by_key(self.spreadsheet_id)
            
            # ASIN_LISTワークシートを取得
            self.asin_worksheet = self.spreadsheet.worksheet(self.worksheet_asin_list)
            
        except Exception as e:
            raise RuntimeError(f"ワークシートの取得に失敗しました: {e}")
    
    def get_asin_list(self) -> List[Dict[str, Any]]:
        """
        ASIN_LISTワークシートからASINリストを取得する
        
        Returns:
            List[Dict[str, Any]]: ASINリストの辞書リスト
                各辞書にはヘッダー行の値がキーとして含まれる
        
        Raises:
            RuntimeError: データの取得に失敗した場合
        """
        try:
            # ワークシートの全データを取得
            values = self.asin_worksheet.get_all_values()
            
            if len(values) > 1:
                headers = values[0]
                data = [dict(zip(headers, row)) for row in values[1:]]
            else:
                data = []
            
            return data
            
        except Exception as e:
            raise RuntimeError(f"ASINリストの取得に失敗しました: {e}")
