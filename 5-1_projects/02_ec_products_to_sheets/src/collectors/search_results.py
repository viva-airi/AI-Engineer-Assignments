from urllib.parse import quote, urljoin
from bs4 import BeautifulSoup
from src.utils.http import get_html
from src.collectors.product_detail import fetch_title_price_by_asin


def fetch_top_n(keyword: str, n: int) -> tuple[list[dict], dict]:
    """
    キーワードでAmazon検索を行い、上位N件の商品情報を取得
    
    Returns:
        tuple[list[dict], dict]: (商品リスト, 統計情報)
            - 商品リスト: 検索結果
            - 統計情報: {'detail_fallback_used': int, ...}
    """
    DETAIL_MAX_FETCH_PER_KEYWORD = 8  # 1キーワードあたりのDP参照上限
    detail_used = 0
    detail_filled_title = 0
    detail_filled_price = 0
    detail_filled_any = 0

    try:
        # 検索URLを構築
        search_url = f"https://www.amazon.co.jp/s?k={quote(keyword)}"

        # HTMLを取得
        html = get_html(search_url)

        # BeautifulSoupでパース
        soup = BeautifulSoup(html, "lxml")

        # 検索結果カード（親スロット）
        main_slot = soup.select_one("div.s-main-slot")
        if not main_slot:
            print(f"[WARN] s-main-slot not found for keyword: {keyword}")
            return [], {'price_filled_by_detail': 0}

        cards = main_slot.select("div[data-asin]")
        results: list[dict] = []

        for card in cards:
            if len(results) >= n:
                break

            # data-asin が空の要素は除外
            asin = card.get("data-asin", "").strip()
            if not asin:
                continue

            # ---------- title ----------
            title = ""
            # a) h2 a span
            el = card.select_one("h2 a span")
            if el:
                title = el.get_text(" ", strip=True)
            else:
                # b) h2 a
                el = card.select_one("h2 a")
                if el:
                    title = el.get_text(" ", strip=True)
                else:
                    # c) h2
                    el = card.select_one("h2")
                    if el:
                        title = el.get_text(" ", strip=True)
                    else:
                        # d) 画像ALT
                        img = card.select_one("img.s-image")
                        if img:
                            title = (img.get("alt") or "").strip()

            # ---------- price ----------
            price_text = ""
            # a) .a-price .a-offscreen（最優先）
            el = card.select_one(".a-price .a-offscreen")
            if el:
                price_text = el.get_text(strip=True)
            else:
                # b) .a-price-whole + .a-price-fraction
                whole_el = card.select_one(".a-price-whole")
                if whole_el:
                    whole = whole_el.get_text(strip=True)
                    price_text = whole
                    frac_el = card.select_one(".a-price-fraction")
                    if frac_el:
                        frac = frac_el.get_text(strip=True)
                        if frac:
                            price_text = f"{whole}.{frac}"
                else:
                    # c) [data-a-color="base"] .a-offscreen
                    el = card.select_one('[data-a-color="base"] .a-offscreen')
                    if el:
                        price_text = el.get_text(strip=True)
                    else:
                        # d) .a-price-range .a-offscreen（レンジ表示）
                        el = card.select_one(".a-price-range .a-offscreen")
                        if el:
                            price_text = el.get_text(strip=True)
                        else:
                            # e) .a-text-price .a-offscreen（参考価格）
                            el = card.select_one(".a-text-price .a-offscreen")
                            if el:
                                price_text = el.get_text(strip=True)
            original_price_empty = not bool(price_text and price_text.strip())

            # ---------- url ----------
            url = ""
            a = card.select_one("h2 a")
            if a and "href" in a.attrs:
                href = a["href"]
                if href.startswith("/"):
                    url = urljoin("https://www.amazon.co.jp", href)
                elif href.startswith("http"):
                    url = href
                else:
                    url = urljoin("https://www.amazon.co.jp", href)

            # asin があれば dp で補完
            if not url and asin:
                url = f"https://www.amazon.co.jp/dp/{asin}"

            filled_by_detail = False

            # --- title / price フォールバック（DPページで補完） ---
            needs_title = not title.strip()
            needs_price = original_price_empty
            if (needs_title or needs_price) and asin and detail_used < DETAIL_MAX_FETCH_PER_KEYWORD:
                try:
                    t2, p2 = fetch_title_price_by_asin(asin)
                except Exception:
                    t2, p2 = (None, None)
                detail_used += 1
                if needs_title and t2:
                    title = t2
                    detail_filled_title += 1
                    filled_by_detail = True
                if needs_price and p2:
                    price_text = p2
                    detail_filled_price += 1
                    filled_by_detail = True
                if filled_by_detail:
                    detail_filled_any += 1

            # デバッグ
            if not title or not url:
                print(f"[WARN] missing field asin={asin} title={bool(title)} url={bool(url)}")

            results.append(
                {
                    "asin": asin,
                    "title": title,
                    "price": price_text,
                    "price_text": price_text,
                    "url": url,
                    "detail_filled": filled_by_detail,
                }
            )

        print(f"[{keyword}] detail_fallback_used={detail_used}")

        stats = {
            "detail_fallback_used": detail_used,
            "detail_filled_title": detail_filled_title,
            "detail_filled_price": detail_filled_price,
            "detail_filled_any": detail_filled_any,
        }
        return results, stats

    except Exception as e:
        print(f"[ERROR] fetch_top_n failed for keyword={keyword}: {e}")
        return [], {
            "detail_fallback_used": 0,
            "detail_filled_title": 0,
            "detail_filled_price": 0,
            "detail_filled_any": 0,
        }
