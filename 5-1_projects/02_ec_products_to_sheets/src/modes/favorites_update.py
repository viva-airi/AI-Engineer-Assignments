"""
お気に入り商品の更新モード
"""

import os
import gspread
from src.readers.sheets_reader import SheetsReader
from src.collectors.product_detail import fetch_product_by_asin
from src.transformers.normalize import normalize_product_detail
from src.sinks.sheets_sink import SheetsSink


def run(spreadsheet_id: str, ws_products: str, ws_asin_list: str) -> dict:
    """
    お気に入り商品の更新処理を実行する
    
    Args:
        spreadsheet_id: Google SheetsのスプレッドシートID
        ws_products: 商品データ用のワークシート名
        ws_asin_list: ASINリスト用のワークシート名
        
    Returns:
        dict: 処理結果 {"success": int, "failed": int}
    """
    try:
        # gspreadクライアントを初期化
        credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not credentials_path:
            raise ValueError("環境変数GOOGLE_APPLICATION_CREDENTIALSが設定されていません")
        
        gc = gspread.service_account(filename=credentials_path)
        
        # ASINリストを読み込み
        reader = SheetsReader(spreadsheet_id, ws_asin_list)
        asin_list = reader.get_asin_list(gc)
        
        if not asin_list:
            print("ASINリストが見つかりませんでした。")
            return {"success": 0, "failed": 0}
        
        # enabledがTRUEのASINのみを対象とする
        enabled_asins = [asin_data for asin_data in asin_list if asin_data.get('enabled') is True]
        
        # 最大10件までに制限
        if len(enabled_asins) > 10:
            print(f"警告: 取得件数が10件を超えています（{len(enabled_asins)}件）。10件に制限します。")
            enabled_asins = enabled_asins[:10]
        
        print(f"処理対象ASIN数: {len(enabled_asins)}件")
        
        # 商品データを収集・正規化
        normalized_products = []
        success_count = 0
        failed_count = 0
        
        for i, asin_data in enumerate(enabled_asins, 1):
            asin = asin_data.get('asin', '')
            if not asin:
                print(f"ASINが空の行をスキップしました（行{i}）")
                failed_count += 1
                continue
            
            try:
                print(f"処理中 ({i}/{len(enabled_asins)}): {asin}")
                
                # 商品詳細を取得
                raw_data = fetch_product_by_asin(asin)
                
                # データを正規化
                normalized_data = normalize_product_detail(raw_data)
                normalized_products.append(normalized_data)
                
                success_count += 1
                
            except Exception as e:
                print(f"エラー: ASIN {asin} の処理に失敗しました - {e}")
                failed_count += 1
                continue
        
        # 正規化されたデータをSheetsに出力
        if normalized_products:
            sink = SheetsSink()
            sink.ensure_headers()
            sink.append_products(normalized_products)
            print(f"Google Sheetsに {len(normalized_products)} 件のデータを追加しました。")
        
        return {"success": success_count, "failed": failed_count}
        
    except Exception as e:
        print(f"処理中にエラーが発生しました: {e}")
        return {"success": 0, "failed": 1}
