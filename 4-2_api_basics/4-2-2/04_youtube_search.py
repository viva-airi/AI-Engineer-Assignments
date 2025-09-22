#!/usr/bin/env python3
"""
YouTube Data API v3 動画検索スクリプト

使用例:
    python 4-2-2/04_youtube_search.py --q "python 入門"
    python 4-2-2/04_youtube_search.py --q "機械学習" --max-results 10
    python 4-2-2/04_youtube_search.py --q "プログラミング" --csv output.csv
"""

import argparse
import csv
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests
from utils.env_loader import load_env


class YouTubeSearcher:
    """YouTube Data API v3を使用した動画検索クラス"""

    BASE_URL = "https://www.googleapis.com/youtube/v3/search"
    TIMEOUT = 20

    def __init__(self, api_key: str):
        self.api_key = api_key

    def search_videos(
        self,
        query: str,
        channel_id: Optional[str] = None,
        published_after: Optional[str] = None,
        duration: str = "any",
        order: str = "relevance",
        region_code: str = "JP",
        lang: str = "ja",
        max_results: int = 5,
        page_token: Optional[str] = None,
        exact: bool = False,
    ) -> Tuple[List[Dict], Optional[str]]:
        """YouTube動画を検索する"""
        if exact:
            query = f'"{query}"'

        params = {
            "part": "snippet",
            "type": "video",
            "q": query,
            "key": self.api_key,
            "maxResults": min(max_results, 50),
            "order": order,
            "regionCode": region_code,
            "relevanceLanguage": lang,
        }
        if channel_id:
            params["channelId"] = channel_id
        if published_after:
            params["publishedAfter"] = published_after
        if duration != "any":
            params["videoDuration"] = duration
        if page_token:
            params["pageToken"] = page_token

        try:
            r = requests.get(self.BASE_URL, params=params, timeout=self.TIMEOUT)
            r.raise_for_status()
            data = r.json()

            videos = []
            for item in data.get("items", []):
                vid = item["id"]["videoId"]
                title = item["snippet"]["title"]
                url = f"https://www.youtube.com/watch?v={vid}"
                videos.append({"title": title, "url": url, "video_id": vid})

            return videos, data.get("nextPageToken")
        except requests.exceptions.HTTPError as e:
            print(f"HTTPエラー: {e.response.status_code}")
            print(f"レスポンス: {e.response.text}")
            print(f"URL: {e.response.url}")
            sys.exit(1)
        except requests.exceptions.RequestException as e:
            print(f"リクエストエラー: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"予期しないエラー: {e}")
            sys.exit(1)


def load_youtube_api_key() -> str:
    """YouTube APIキーを環境変数から読み込む（スクリプト基準の絶対パス）"""
    script_dir = Path(__file__).resolve().parent
    env_path = script_dir / "env" / "youtube.env"

    if not env_path.exists():
        raise FileNotFoundError(f".env が見つかりません: {env_path}")

    env_vars = load_env(str(env_path))
    api_key = env_vars.get("YOUTUBE_API_KEY")
    if not api_key:
        raise RuntimeError("YOUTUBE_API_KEY が設定されていません")
    return api_key


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="YouTube Data API v3を使用した動画検索",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  %(prog)s --q "python 入門"
  %(prog)s --q "機械学習" --max-results 10
  %(prog)s --q "プログラミング" --channel-id UCxxxxxxx
  %(prog)s --q "チュートリアル" --published-after 2025-01-01T00:00:00Z
  %(prog)s --q "検索語" --exact --csv results.csv
        """,
    )
    parser.add_argument("--q", "--query", type=str, default="Python tutorial", help="検索クエリ")
    parser.add_argument("--channel-id", type=str, help="チャンネルID")
    parser.add_argument("--published-after", type=str, help="公開日時以降（ISO 8601: 2025-09-01T00:00:00Z）")
    parser.add_argument("--duration", type=str, choices=["any", "short", "medium", "long"], default="any")
    parser.add_argument("--order", type=str, choices=["relevance", "date", "viewCount", "rating"], default="relevance")
    parser.add_argument("--region-code", type=str, default="JP")
    parser.add_argument("--lang", type=str, default="ja")
    parser.add_argument("--max-results", type=int, default=5)
    parser.add_argument("--pages", type=int, default=1)
    parser.add_argument("--exact", action="store_true", help="完全一致検索（クエリをダブルクォートで囲む）")
    parser.add_argument("--csv", type=str, help="結果をCSV保存（UTF-8）")
    return parser.parse_args()


def validate_arguments(args: argparse.Namespace) -> None:
    if not 1 <= args.max_results <= 50:
        print("エラー: --max-resultsは1-50の範囲で指定してください")
        sys.exit(1)
    if not 1 <= args.pages <= 5:
        print("エラー: --pagesは1-5の範囲で指定してください")
        sys.exit(1)


def search_videos_with_pagination(searcher: YouTubeSearcher, args: argparse.Namespace) -> List[Dict]:
    all_videos: List[Dict] = []
    page_token: Optional[str] = None

    for _ in range(args.pages):
        videos, next_token = searcher.search_videos(
            query=args.q,
            channel_id=args.channel_id,
            published_after=args.published_after,
            duration=args.duration,
            order=args.order,
            region_code=args.region_code,
            lang=args.lang,
            max_results=args.max_results,
            page_token=page_token,
            exact=args.exact,
        )
        all_videos.extend(videos)
        if not next_token:
            break
        page_token = next_token

    return all_videos


def output_results(videos: List[Dict], csv_path: Optional[str] = None) -> None:
    if not videos:
        print("該当なし")
        return

    if csv_path:
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["タイトル", "URL"])
            for v in videos:
                w.writerow([v["title"], v["url"]])
        print(f"結果を {csv_path} に保存しました（{len(videos)}件）")
    else:
        for v in videos:
            print(f"{v['title']} - {v['url']}")


def main():
    args = parse_arguments()
    validate_arguments(args)

    # ←ここが今回の修正ポイント
    api_key = load_youtube_api_key()

    searcher = YouTubeSearcher(api_key)
    videos = search_videos_with_pagination(searcher, args)
    output_results(videos, args.csv)


if __name__ == "__main__":
    main()
