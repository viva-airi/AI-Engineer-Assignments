"""
Top N商品比較モード
"""

import time
import gspread
from typing import List, Dict, Tuple
from src.collectors.search_results import fetch_top_n
from src.collectors.product_detail import fetch_title_by_asin
from src.transformers.normalize import normalize_search_item
from src.sinks.sheets_sink import SheetsSink


def deduplicate_by_asin(items: List[Dict]) -> List[Dict]:
    """
    ASIN単位で重複排除（最安値採用）
    
    Args:
        items: 重複排除対象のアイテムリスト
        
    Returns:
        List[Dict]: 重複排除後のアイテムリスト
    """
    asin_groups = {}
    
    for item in items:
        asin = item.get('asin', '')
        
        # ASINが空のものはそのまま別扱い
        if not asin:
            asin_groups[f"empty_{len(asin_groups)}"] = [item]
            continue
        
        if asin not in asin_groups:
            asin_groups[asin] = []
        asin_groups[asin].append(item)
    
    deduplicated = []
    for asin, group in asin_groups.items():
        if len(group) == 1:
            deduplicated.append(group[0])
        else:
            # 同一ASINが複数ある場合は最安値を採用
            # price が数値で最小のものを採用（price が None のものより数値を優先）
            best_item = None
            min_price = float('inf')
            
            for item in group:
                price = item.get('price')
                if price is not None and isinstance(price, (int, float)):
                    if price < min_price:
                        min_price = price
                        best_item = item
                elif best_item is None:
                    # price が None の場合のフォールバック
                    best_item = item
            
            if best_item is None:
                best_item = group[0]  # フォールバック
            
            # rank は最小を残す
            best_rank = min(item.get('rank', 999) for item in group)
            best_item['rank'] = best_rank
            
            # title / url は非空を優先でマージ
            best_title = ""
            best_url = ""
            for item in group:
                if item.get('title', '').strip() and not best_title:
                    best_title = item.get('title', '')
                if item.get('url', '').strip() and not best_url:
                    best_url = item.get('url', '')
            
            if best_title:
                best_item['title'] = best_title
            if best_url:
                best_item['url'] = best_url
            
            # rating と review_count は常に None のため処理不要
            
            deduplicated.append(best_item)
    
    # rank順でソート
    deduplicated.sort(key=lambda x: x.get('rank', 999))
    
    return deduplicated


def complement_missing_titles(items: List[Dict], keyword: str, max_count: int = 3) -> List[Dict]:
    """
    タイトルが空のアイテムについて、fetch_title_by_asinで補完する
    
    Args:
        items: アイテムリスト
        keyword: 検索キーワード（ログ用）
        max_count: 最大補完件数
        
    Returns:
        List[Dict]: 補完後のアイテムリスト
    """
    complemented_count = 0
    
    for item in items:
        if complemented_count >= max_count:
            break
            
        title = item.get('title', '').strip()
        asin = item.get('asin', '')
        
        if not title and asin:
            try:
                fetched_title = fetch_title_by_asin(asin)
                if fetched_title:
                    item['title'] = fetched_title
                    complemented_count += 1
                    print(f"[INFO] タイトル補完成功: asin={asin}, title={fetched_title[:50]}...")
            except Exception as e:
                print(f"[WARN] タイトル補完失敗: asin={asin}, error={e}")
    
    return items


def run(spreadsheet_id: str, ws_keywords: str, ws_ranking: str, max_keywords: int = 3) -> Tuple[int, int]:
    """
    Top N商品の比較処理を実行する
    
    Args:
        spreadsheet_id: スプレッドシートID
        ws_keywords: キーワードシート名
        ws_ranking: ランキングシート名
        max_keywords: 最大処理キーワード数
        
    Returns:
        Tuple[int, int]: (total_success_rows, total_failed_keywords)
    """
    total_success_rows = 0
    total_failed_keywords = 0
    
    try:
        # SheetsSinkを初期化
        sink = SheetsSink()
        
        # gspreadクライアントを初期化
        import os
        credentials_path = 'credentials/service_account.json'
        gc = gspread.service_account(filename=credentials_path)
        spreadsheet = gc.open_by_key(spreadsheet_id)
        
        # キーワードシートからデータを取得
        keywords_sheet = spreadsheet.worksheet(ws_keywords)
        keywords_data = keywords_sheet.get_all_records()
        
        # 有効なキーワードをフィルタリング
        valid_keywords = []
        for row in keywords_data:
            keyword = row.get('keyword', '').strip()
            if keyword:
                valid_keywords.append(row)
        
        print(f"処理対象keyword数: {len(valid_keywords)}件")
        
        if len(valid_keywords) == 0:
            print("処理対象のキーワードが0件のため、処理を終了します。")
            return total_success_rows, total_failed_keywords
        
        # 最大max_keywords個のキーワードを処理
        processed_count = 0
        for row in valid_keywords:
            if processed_count >= max_keywords:
                break
                
            keyword = row.get('keyword', '').strip()
            top_n = row.get('top_n', 10)  # デフォルト10件
                
            try:
                print(f"検索中: {keyword} (top {top_n})")
                
                # 検索結果を取得
                search_results, fetch_stats = fetch_top_n(keyword, top_n)
                detail_fallback_used = fetch_stats.get('detail_fallback_used', 0)
                filled_by_detail_count = sum(1 for item in search_results if item.get('detail_filled'))
                
                if not search_results:
                    print(f"  抽出件数: 0 / 追加件数: 0")
                    total_failed_keywords += 1
                    continue
                
                # 各結果を正規化
                normalized_results = []
                for rank, result in enumerate(search_results, 1):
                    normalized = normalize_search_item(result, keyword, rank)
                    normalized_results.append(normalized)
                
                # ASIN単位で重複排除（最安値採用）
                before_count = len(normalized_results)
                deduplicated_results = deduplicate_by_asin(normalized_results)
                after_count = len(deduplicated_results)
                
                # タイトル最終補完（任意・軽量、各keywordにつき最大3件まで）
                deduplicated_results = complement_missing_titles(deduplicated_results, keyword, max_count=3)
                
                # 統計情報を集計
                missing_title_count = sum(1 for item in deduplicated_results if not item.get('title', '').strip())
                missing_url_count = sum(1 for item in deduplicated_results if not item.get('url', '').strip())
                missing_price_count = sum(1 for item in deduplicated_results if item.get('price') is None)
                
                # rank を 1..N に詰め直して、上位 N 件に丸める
                final_results = []
                for new_rank, item in enumerate(deduplicated_results[:top_n], 1):
                    item['rank'] = new_rank
                    final_results.append(item)
                
                # ランキングデータを追加
                sink.append_ranking(final_results)
                
                added_count = len(final_results)
                total_success_rows += added_count
                
                # ログ出力
                print(f"[{keyword}] before={len(normalized_results)} -> after_dedupe={len(deduplicated_results)}")
                print(f"  filled_by_detail: {filled_by_detail_count}, missing_price: {missing_price_count}")
                print(f"  detail_fetch_used: {detail_fallback_used}, empty_title: {missing_title_count}, empty_url: {missing_url_count}")
                print(f"  追加件数: {added_count}")
                
                processed_count += 1
                
                # 検索間隔を空ける（1-3秒）
                time.sleep(2)
                
            except Exception as e:
                print(f"  エラー ({keyword}): {e}")
                total_failed_keywords += 1
                continue
        
        return total_success_rows, total_failed_keywords
        
    except Exception as e:
        print(f"全体エラー: {e}")
        return total_success_rows, total_failed_keywords
