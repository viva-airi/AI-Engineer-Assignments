"""
Google Sheetsへのデータ出力処理
"""

import os
import gspread
from google.oauth2.service_account import Credentials
from typing import List, Dict, Any


class SheetsSink:
    """Google Sheetsへのデータ出力クラス"""
    
    def __init__(self):
        """
        初期化 - .envから設定を読み込んでスプレッドシートに接続
        """
        # 環境変数から設定を読み込み
        self.spreadsheet_id = os.getenv('SPREADSHEET_ID')
        self.worksheet_name = os.getenv('WORKSHEET_PRODUCTS', 'PRODUCTS_HISTORY')
        
        if not self.spreadsheet_id:
            raise ValueError("SPREADSHEET_ID環境変数が設定されていません")
        
        # サービスアカウント認証
        credentials_path = 'credentials/service_account.json'
        if not os.path.exists(credentials_path):
            raise FileNotFoundError(f"認証ファイルが見つかりません: {credentials_path}")
        
        scope = ['https://www.googleapis.com/auth/spreadsheets']
        credentials = Credentials.from_service_account_file(credentials_path, scopes=scope)
        
        # gspreadクライアント初期化
        self.gc = gspread.authorize(credentials)
        self.spreadsheet = self.gc.open_by_key(self.spreadsheet_id)
        self.worksheet = self.spreadsheet.worksheet(self.worksheet_name)
    
    def ensure_headers(self) -> None:
        """
        1行目にヘッダーが無ければ書き込む
        """
        headers = [
            "asin", "title", "price", "currency", "availability", 
            "url", "image_url", "timestamp", "source"
        ]
        
        # 現在の1行目を取得
        try:
            current_headers = self.worksheet.row_values(1)
            if not current_headers or current_headers != headers:
                # ヘッダーが無いか異なる場合は書き込み
                self.worksheet.update('A1', [headers])
        except Exception:
            # エラー時は強制的にヘッダーを書き込み
            self.worksheet.update('A1', [headers])
    
    def append_products(self, rows: List[Dict[str, Any]]) -> None:
        """
        上記列順に整列して複数行をappend
        
        Args:
            rows: 商品データのリスト
        """
        if not rows:
            return
        
        # ヘッダー順にデータを整列
        headers = [
            "asin", "title", "price", "currency", "availability", 
            "url", "image_url", "timestamp", "source"
        ]
        
        formatted_rows = []
        for row in rows:
            formatted_row = []
            for header in headers:
                value = row.get(header, '')
                formatted_row.append(value)
            formatted_rows.append(formatted_row)
        
        # スプレッドシートに追加
        if formatted_rows:
            self.worksheet.append_rows(formatted_rows)
    
    def append_ranking(self, rows: List[Dict[str, Any]]) -> None:
        """
        ランキングデータを追加する
        
        Args:
            rows: ランキングデータのリスト
        """
        if not rows:
            return
        
        # ランキングデータ用のヘッダーを確保
        ranking_headers = [
            "keyword", "rank", "asin", "title", "price", 
            "url", "timestamp", "source"
        ]
        
        # RANKING_SNAPSHOTSシートに接続
        ranking_worksheet_name = 'RANKING_SNAPSHOTS'
        try:
            ranking_worksheet = self.spreadsheet.worksheet(ranking_worksheet_name)
        except:
            # シートが存在しない場合は作成
            ranking_worksheet = self.spreadsheet.add_worksheet(title=ranking_worksheet_name, rows=1000, cols=8)
        
        # ヘッダーを確保
        try:
            current_headers = ranking_worksheet.row_values(1)
            if not current_headers or current_headers != ranking_headers:
                ranking_worksheet.update('A1', [ranking_headers])
        except Exception:
            ranking_worksheet.update('A1', [ranking_headers])
        
        # ヘッダー順にデータを整列
        formatted_rows = []
        for row in rows:
            formatted_row = []
            for header in ranking_headers:
                value = row.get(header, '')
                formatted_row.append(value)
            formatted_rows.append(formatted_row)
        
        # スプレッドシートに追加
        if formatted_rows:
            ranking_worksheet.append_rows(formatted_rows)
