"""
HTTP通信ユーティリティ
"""

import time
import random
import requests

# 価格補完用の設定定数
DETAIL_MAX_FETCH_PER_RUN = 12  # 過負荷防止
REQUEST_DELAY_SEC = 1.2  # リクエスト間隔
RETRY_MAX = 2  # 最大リトライ回数


def get_html(url: str) -> str:
    """
    URLからHTMLを取得する

    Args:
        url: 取得するURL

    Returns:
        str: HTMLコンテンツ
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
        "Accept-Language": "ja-JP,ja;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    retry_statuses = {429, 500, 502, 503, 504}
    backoff_schedule = [1.0, 2.0, 4.0]
    with requests.Session() as session:
        for attempt, backoff in enumerate(backoff_schedule):
            time.sleep(random.uniform(1.2, 2.5))
            try:
                response = session.get(url, headers=headers, timeout=(10, 15))
                if response.status_code in retry_statuses and attempt < len(backoff_schedule) - 1:
                    raise requests.exceptions.HTTPError(response=response)
                response.raise_for_status()
                return response.text
            except requests.exceptions.HTTPError as exc:
                status = getattr(exc.response, "status_code", None)
                if status not in retry_statuses or attempt == len(backoff_schedule) - 1:
                    break
                time.sleep(backoff)
            except requests.exceptions.RequestException:
                if attempt == len(backoff_schedule) - 1:
                    break
                time.sleep(backoff)

    raise ValueError("fetch failed")
