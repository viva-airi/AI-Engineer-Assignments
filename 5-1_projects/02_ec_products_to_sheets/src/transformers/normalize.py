"""
商品データの正規化処理
"""

import re
from datetime import datetime
import pytz


def normalize_product_detail(raw: dict) -> dict:
    """
    商品詳細データを正規化する
    
    Args:
        raw: 生の商品詳細データ
        
    Returns:
        dict: 正規化された商品詳細データ
    """
    # 価格を正規化（数字のみ抽出してintに変換）
    price = None
    price_text = raw.get("price_text", "")
    if price_text:
        # カンマや通貨記号を除去して数字のみ抽出
        price_match = re.search(r'(\d+)', price_text.replace(',', ''))
        if price_match:
            try:
                price = int(price_match.group(1))
            except ValueError:
                price = None
    
    # 在庫状況を正規化
    availability_text = raw.get("availability_text", "").lower()
    availability = "unknown"
    
    if "在庫あり" in availability_text or "通常配送" in availability_text:
        availability = "in_stock"
    elif "在庫切れ" in availability_text or "一時的に在庫切れ" in availability_text:
        availability = "out_of_stock"
    elif "入荷予定" in availability_text:
        availability = "unknown"
    
    # 現在時刻をJSTで取得
    now_jst = datetime.now(pytz.timezone('Asia/Tokyo'))
    timestamp = now_jst.strftime("%Y-%m-%d %H:%M:%S")
    
    return {
        "asin": raw.get("asin", ""),
        "title": raw.get("title", ""),
        "price": price,
        "currency": "JPY",
        "availability": availability,
        "rating": None,
        "review_count": None,
        "url": raw.get("url", ""),
        "image_url": raw.get("image_url", ""),
        "timestamp": timestamp,
        "source": raw.get("source", "")
    }


def normalize_search_item(raw: dict, keyword: str, rank: int) -> dict:
    """
    検索結果アイテムデータを正規化する
    
    Args:
        raw: 生の検索結果データ
        keyword: 検索キーワード
        rank: 検索結果順位
        
    Returns:
        dict: 正規化された検索結果データ
    """
    # 価格を正規化（数値化できなければNone）
    price = None
    s = str(raw.get("price_text", "") or raw.get("price", "") or "")
    if s:
        match = re.search(r"(\d[\d,]*)", s)
        if match:
            try:
                price = int(match.group(1).replace(",", ""))
            except ValueError:
                price = None
    
    # url が空かつ asin があれば f"https://www.amazon.co.jp/dp/{asin}" で補完
    url = raw.get("url", "")
    asin = raw.get("asin", "")
    if not url and asin:
        url = f"https://www.amazon.co.jp/dp/{asin}"
    
    # 現在時刻をJSTで取得
    now_jst = datetime.now(pytz.timezone('Asia/Tokyo'))
    timestamp = now_jst.strftime("%Y-%m-%d %H:%M:%S")
    
    return {
        "keyword": keyword,
        "rank": rank,
        "asin": asin,
        "title": raw.get("title", ""),
        "price": price,
        "rating": None,
        "review_count": None,
        "url": url,
        "timestamp": timestamp,
        "source": "amazon_search"
    }
