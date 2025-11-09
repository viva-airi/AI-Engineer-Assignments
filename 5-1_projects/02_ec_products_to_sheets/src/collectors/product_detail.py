"""
商品詳細ページのスクレイピング
"""

import re
import time
from functools import lru_cache
from datetime import datetime
from bs4 import BeautifulSoup
from src.utils.http import get_html, REQUEST_DELAY_SEC, RETRY_MAX


@lru_cache(maxsize=256)
def fetch_title_price_by_asin(asin: str) -> tuple[str | None, str | None]:
    """
    /dp/{asin} を開き、(title, price_text) を返す。取れなければ (None, None)。
    price_text は "￥3,520" など文字列のまま返す（数値化は normalize 側）。
    """
    url = f"https://www.amazon.co.jp/dp/{asin}"
    try:
        html = get_html(url)
    except Exception:
        return (None, None)

    soup = BeautifulSoup(html, "lxml")

    title_value: str | None = None
    title_element = soup.select_one("#productTitle")
    if title_element:
        title_value = title_element.get_text(" ", strip=True) or None

    price_value: str | None = None
    for selector in [
        "#corePrice_feature_div .a-offscreen",
        "#sns-base-price .a-offscreen",
        "#priceblock_dealprice",
        "#priceblock_ourprice",
        "#priceblock_saleprice",
        "#apex_desktop .a-price .a-offscreen",
    ]:
        price_element = soup.select_one(selector)
        if price_element:
            extracted = price_element.get_text(strip=True)
            if extracted:
                price_value = extracted
                break

    return (title_value, price_value)


def fetch_product_by_asin(asin: str) -> dict:
    """
    ASINから商品詳細を取得する
    
    Args:
        asin: Amazon商品のASIN
        
    Returns:
        dict: 商品詳細データ
    """
    url = f"https://www.amazon.co.jp/dp/{asin}"
    
    try:
        # HTMLを取得
        html = get_html(url)
        soup = BeautifulSoup(html, 'lxml')
        
        # 商品タイトルを抽出
        title_elem = soup.select_one('#productTitle')
        title = title_elem.get_text(strip=True) if title_elem else ""
        
        # 価格を抽出（複数のセレクターを試す）
        price = ""
        price_selectors = [
            '#corePrice_feature_div .a-offscreen',
            '#apex_desktop .a-offscreen'
        ]
        
        for selector in price_selectors:
            price_elem = soup.select_one(selector)
            if price_elem:
                price = price_elem.get_text(strip=True)
                break
        
        # 在庫状況を抽出
        availability = ""
        availability_selectors = [
            '#availability .a-color-success',
            '#availability .a-color-state'
        ]
        
        for selector in availability_selectors:
            availability_elem = soup.select_one(selector)
            if availability_elem:
                availability = availability_elem.get_text(strip=True)
                break
        
        # 画像URLを抽出
        image_url = ""
        image_elem = soup.select_one('#imgTagWrapperId img[src]')
        if image_elem:
            image_url = image_elem.get('src', '')
        
        # 現在時刻をJSTで取得
        now_jst = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return {
            "asin": asin,
            "title": title,
            "price_text": price,
            "availability_text": availability,
            "url": url,
            "image_url": image_url,
            "source": "amazon_jp",
            "fetched_at": now_jst
        }
        
    except Exception as e:
        # エラーが発生した場合は空のデータを返す
        return {
            "asin": asin,
            "title": "",
            "price_text": "",
            "availability_text": "",
            "url": url,
            "image_url": "",
            "source": "amazon_jp",
            "fetched_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }


# 価格フォールバック用キャッシュ（同一ASINは再リクエストしない）
_price_cache = {}


def fetch_price_by_asin(asin: str) -> tuple[int | None, str | None]:
    """
    ASINから価格のみを取得する（フォールバック用）
    
    Args:
        asin: Amazon商品のASIN
        
    Returns:
        tuple[int | None, str | None]: (価格, availability) 
            - 価格: 数値（円）、取得不可ならNone
            - availability: "out_of_stock"またはNone
    """
    # キャッシュ確認
    if asin in _price_cache:
        return _price_cache[asin]
    
    url = f"https://www.amazon.co.jp/dp/{asin}"
    
    # リトライループ
    for attempt in range(RETRY_MAX + 1):
        try:
            # ポライトネス: リクエスト間隔
            if attempt > 0:
                time.sleep(REQUEST_DELAY_SEC * (2 ** (attempt - 1)))  # 指数バックオフ
            else:
                time.sleep(REQUEST_DELAY_SEC)
            
            # HTMLを取得
            html = get_html(url)
            soup = BeautifulSoup(html, 'lxml')
            
            # 在庫文言検出
            availability_text = ""
            availability_elem = soup.select_one('#availability')
            if availability_elem:
                availability_text = availability_elem.get_text(strip=True).lower()
            
            if "在庫切れ" in availability_text or "現在在庫切れです" in availability_text:
                result = (None, "out_of_stock")
                _price_cache[asin] = result
                return result
            
            # 価格抽出（セレクタ順序厳守）
            price_selectors = [
                '#corePrice_feature_div .a-offscreen',
                '#sns-base-price .a-offscreen',
                '#priceblock_dealprice, #priceblock_ourprice, #priceblock_saleprice',
                '#apex_desktop .a-price .a-offscreen'
            ]
            
            price_text = ""
            for selector in price_selectors:
                price_elem = soup.select_one(selector)
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    break
            
            # 価格文字列から数値抽出
            if price_text:
                # 数字以外を除去
                price_digits = re.sub(r"[^\d]", "", price_text)
                if price_digits:
                    try:
                        price_int = int(price_digits)
                        result = (price_int, None)
                        _price_cache[asin] = result
                        return result
                    except ValueError:
                        pass
            
            # 取得できなかった場合
            result = (None, None)
            _price_cache[asin] = result
            return result
            
        except Exception as e:
            # 最終リトライで失敗
            if attempt >= RETRY_MAX:
                result = (None, None)
                _price_cache[asin] = result
                return result
            continue
    
    # ここには到達しないはず
    return (None, None)


def fetch_title_by_asin(asin: str) -> str | None:
    """
    ASINから商品タイトルのみを取得する（軽量版）
    
    Args:
        asin: Amazon商品のASIN
        
    Returns:
        str | None: 商品タイトル（取得できなかった場合はNone）
    """
    url = f"https://www.amazon.co.jp/dp/{asin}"
    
    try:
        # HTMLを取得
        html = get_html(url)
        soup = BeautifulSoup(html, 'lxml')
        
        # 商品タイトルを抽出
        title_elem = soup.select_one('#productTitle')
        if title_elem:
            title = title_elem.get_text(strip=True)
            return title if title else None
        
        return None
        
    except Exception as e:
        # エラーが発生した場合はNoneを返す
        return None