"""
Google Sheetsからのデータ読み込み処理
"""

import gspread
from typing import List, Dict, Any


class SheetsReader:
    """Google Sheetsからのデータ読み込みクラス"""
    
    def __init__(self, spreadsheet_id: str, worksheet_name: str):
        """
        初期化
        
        Args:
            spreadsheet_id: スプレッドシートID
            worksheet_name: ワークシート名
        """
        self.spreadsheet_id = spreadsheet_id
        self.worksheet_name = worksheet_name
        # gspreadクライアントの初期化は呼び出し側で行う前提
    
    def get_asin_list(self, gc: gspread.Client) -> List[Dict[str, Any]]:
        """
        ASINリストを読み込む（1行目=ヘッダー、2行目以降=データ）
        
        Args:
            gc: gspreadクライアント
            
        Returns:
            List[Dict[str, Any]]: ASINリストの辞書リスト
        """
        try:
            # スプレッドシートとワークシートを開く
            spreadsheet = gc.open_by_key(self.spreadsheet_id)
            worksheet = spreadsheet.worksheet(self.worksheet_name)
            
            # 全行を取得
            values = worksheet.get_all_values()
            if not values or len(values) < 2:
                return []
            
            # 1行目をヘッダーとして取得（小文字化）
            headers = [h.strip().lower() for h in values[0]]
            
            # 2行目以降をデータとして取得
            data = [dict(zip(headers, row)) for row in values[1:] if any(cell.strip() for cell in row)]
            
            result = []
            for row_dict in data:
                # enabledの値を正規化
                enabled_value = row_dict.get('enabled', '').strip().lower()
                if enabled_value in {'true', '1', 'yes', 'y', 'on'}:
                    row_dict['enabled'] = True
                elif enabled_value in {'false', '0', 'no', 'n', 'off'}:
                    row_dict['enabled'] = False
                # それ以外は元の文字列を保持（空の場合は空文字）
                
                result.append(row_dict)
            
            return result
            
        except Exception as e:
            print(f"ASINリスト取得エラー: {e}")
            return []
    
    def read_asin_list(self) -> list:
        """
        ASINリストを読み込む（後方互換性のため）
        
        Returns:
            list: ASINリスト
        """
        # このメソッドは後方互換性のため残す
        # 実際の使用時はget_asin_list(gc)を使用する
        return []
    
    def get_keywords(self, gc: gspread.Client) -> List[Dict[str, Any]]:
        """
        キーワードリストを読み込む（1行目=ヘッダー、2行目以降=データ）
        
        Args:
            gc: gspreadクライアント
            
        Returns:
            List[Dict[str, Any]]: キーワードリストの辞書リスト
        """
        try:
            # スプレッドシートとワークシートを開く
            spreadsheet = gc.open_by_key(self.spreadsheet_id)
            worksheet = spreadsheet.worksheet(self.worksheet_name)
            
            # 全行を取得
            values = worksheet.get_all_values()
            if not values or len(values) < 2:
                return []
            
            # 1行目をヘッダーとして取得（小文字化）
            headers = [h.strip().lower() for h in values[0]]
            
            # 2行目以降をデータとして取得
            data = [dict(zip(headers, row)) for row in values[1:] if any(cell.strip() for cell in row)]
            
            result = []
            for row_dict in data:
                # top_nの値を正規化
                top_n_str = row_dict.get('top_n', '10').strip()
                try:
                    top_n = int(top_n_str) if top_n_str else 10
                except (ValueError, TypeError):
                    top_n = 10  # 不正な値や空の場合は10にフォールバック
                
                row_dict['top_n'] = top_n
                result.append(row_dict)
            
            return result
            
        except Exception as e:
            print(f"キーワードリスト取得エラー: {e}")
            return []
    
    def read_keywords(self) -> list:
        """
        検索キーワードリストを読み込む（後方互換性のため）
        
        Returns:
            list: キーワードリスト
        """
        # このメソッドは後方互換性のため残す
        # 実際の使用時はget_keywords(gc)を使用する
        return []
