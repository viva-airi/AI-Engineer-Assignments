#!/usr/bin/env python3
"""
EC商品データをGoogle Sheetsに出力するメインスクリプト
"""

import argparse
import os
from datetime import datetime
import pytz
from dotenv import load_dotenv

from src.sinks.sheets_sink import SheetsSink
from src.sources.sheets_source import SheetsSource
from src.readers.sheets_reader import SheetsReader


def smoketest():
    """接続確認テスト"""
    try:
        # .envを読み込み
        load_dotenv()
        
        # SheetsSinkを初期化
        sink = SheetsSink()
        
        # ヘッダーを確保
        sink.ensure_headers()
        
        # ダミーデータを作成
        now_jst = datetime.now(pytz.timezone('Asia/Tokyo'))
        dummy_data = [{
            "asin": "DUMMYASIN001",
            "title": "SMOKE TEST",
            "price": 1234,
            "currency": "JPY",
            "availability": "unknown",
            "rating": None,
            "review_count": None,
            "url": "https://example.com",
            "image_url": "",
            "timestamp": now_jst.strftime("%Y-%m-%d %H:%M:%S JST"),
            "source": "smoketest"
        }]
        
        # ダミーデータを書き込み
        sink.append_products(dummy_data)
        
        print("OK: 1 row appended.")
        
    except Exception as e:
        print(f"Error: {e}")
        return


def list_asins():
    """ASINリストを取得して表示する"""
    try:
        # .envを読み込み
        load_dotenv()
        
        # 環境変数を取得
        spreadsheet_id = os.getenv('SPREADSHEET_ID')
        worksheet_asin_list = os.getenv('WORKSHEET_ASIN_LIST', 'ASIN_LIST')
        credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        
        if not spreadsheet_id or not credentials_path:
            print("環境変数SPREADSHEET_IDまたはGOOGLE_APPLICATION_CREDENTIALSが設定されていません")
            return
        
        # gspreadクライアントを初期化
        import gspread
        gc = gspread.service_account(filename=credentials_path)
        
        # SheetsReaderを初期化してASINリストを取得
        reader = SheetsReader(spreadsheet_id, worksheet_asin_list)
        asin_list = reader.get_asin_list(gc)
        
        if not asin_list:
            print("No data found")
            return
        
        print(f"ASIN_LIST（{len(asin_list)}件）:")
        print("-" * 48)
        
        # ヘッダー行を表示
        print(f"{'No':<3} {'ASIN':<12} {'MEMO':<30} {'ENABLED':<8}")
        print("-" * 48)
        
        # 各行を見やすく表示
        for i, asin_data in enumerate(asin_list, 1):
            asin = asin_data.get('asin', '')
            memo = asin_data.get('memo', '')[:28]  # 最大28文字
            enabled = asin_data.get('enabled', '')
            
            # enabledの値を文字列に変換
            if enabled is True:
                enabled_str = 'TRUE'
            elif enabled is False:
                enabled_str = 'FALSE'
            else:
                enabled_str = str(enabled) if enabled else ''
            
            print(f"{i:<3} {asin:<12} {memo:<30} {enabled_str:<8}")
        
    except Exception as e:
        print(f"エラー: {e}")


def list_keywords():
    """キーワードリストを取得して表示する"""
    try:
        # .envを読み込み
        load_dotenv()
        
        # 環境変数を取得
        spreadsheet_id = os.getenv('SPREADSHEET_ID')
        worksheet_keywords = os.getenv('WORKSHEET_KEYWORDS', 'KEYWORDS')
        credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        
        if not spreadsheet_id or not credentials_path:
            print("環境変数SPREADSHEET_IDまたはGOOGLE_APPLICATION_CREDENTIALSが設定されていません")
            return
        
        # gspreadクライアントを初期化
        import gspread
        gc = gspread.service_account(filename=credentials_path)
        
        # SheetsReaderを初期化してキーワードリストを取得
        reader = SheetsReader(spreadsheet_id, worksheet_keywords)
        keywords_list = reader.get_keywords(gc)
        
        if not keywords_list:
            print("No data found")
            return
        
        print(f"KEYWORDS（{len(keywords_list)}件）:")
        print("-" * 50)
        
        # ヘッダー行を表示
        print(f"{'No':<3} {'KEYWORD':<30} {'TOP_N':<8}")
        print("-" * 50)
        
        # 各行を見やすく表示
        for i, keyword_data in enumerate(keywords_list, 1):
            keyword = keyword_data.get('keyword', '')[:28]  # 最大28文字
            top_n = keyword_data.get('top_n', 10)
            
            print(f"{i:<3} {keyword:<30} {top_n:<8}")
        
    except Exception as e:
        print(f"エラー: {e}")


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(description="EC商品データをGoogle Sheetsに出力")
    parser.add_argument(
        "--smoketest",
        action="store_true",
        help="接続確認テストを実行"
    )
    parser.add_argument(
        "--list-asins",
        action="store_true",
        help="ASINリストを表示"
    )
    parser.add_argument(
        "--list-keywords",
        action="store_true",
        help="キーワードリストを表示"
    )
    parser.add_argument(
        "mode",
        nargs="?",
        choices=["favorites_update", "compare_topN"],
        help="実行モードを選択"
    )
    
    args = parser.parse_args()
    
    if args.smoketest:
        smoketest()
        return
    
    if args.list_asins:
        list_asins()
        return
    
    if args.list_keywords:
        list_keywords()
        return
    
    if args.mode:
        if args.mode == "favorites_update":
            # .envを読み込み
            load_dotenv()
            
            # 環境変数を取得
            spreadsheet_id = os.getenv('SPREADSHEET_ID')
            worksheet_products = os.getenv('WORKSHEET_PRODUCTS', 'PRODUCTS_HISTORY')
            worksheet_asin_list = os.getenv('WORKSHEET_ASIN_LIST', 'ASIN_LIST')
            
            if not spreadsheet_id:
                print("環境変数SPREADSHEET_IDが設定されていません")
                return
            
            # favorites_updateモードを実行
            from src.modes.favorites_update import run
            result = run(spreadsheet_id, worksheet_products, worksheet_asin_list)
            
            print(f"Done: success={result['success']}, failed={result['failed']}")
        elif args.mode == "compare_topN":
            # .envを読み込み
            load_dotenv()
            
            # 環境変数を取得
            spreadsheet_id = os.getenv('SPREADSHEET_ID')
            worksheet_keywords = os.getenv('WORKSHEET_KEYWORDS', 'KEYWORDS')
            worksheet_ranking = os.getenv('WORKSHEET_RANKING', 'RANKING_SNAPSHOTS')
            
            if not spreadsheet_id:
                print("環境変数SPREADSHEET_IDが設定されていません")
                return
            
            # compare_topNモードを実行
            from src.modes.compare_topn import run
            success_rows, failed_keywords = run(spreadsheet_id, worksheet_keywords, worksheet_ranking, max_keywords=3)
            
            print(f"Done: rows={success_rows}, failed_keywords={failed_keywords}")
        else:
            print("未実装です")
        return
    
    # 引数が何も指定されていない場合
    parser.print_help()


if __name__ == "__main__":
    main()
