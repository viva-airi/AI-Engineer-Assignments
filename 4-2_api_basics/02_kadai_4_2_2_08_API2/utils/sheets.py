"""
Google Sheets操作ユーティリティ
"""
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from google.oauth2 import service_account
from googleapiclient.discovery import build


# プロジェクトのルートディレクトリを取得
BASE_DIR = Path(__file__).resolve().parent.parent


# =========================
# 内部ヘルパー
# =========================
def _get_credentials():
    """サービスアカウントの認証情報を取得"""
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not credentials_path:
        raise ValueError("GOOGLE_APPLICATION_CREDENTIALS環境変数が設定されていません")

    if not os.path.exists(credentials_path):
        raise FileNotFoundError(f"認証ファイルが見つかりません: {credentials_path}")

    return service_account.Credentials.from_service_account_file(
        credentials_path,
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )


def _get_service():
    """Google Sheets APIサービスを取得"""
    creds = _get_credentials()
    return build("sheets", "v4", credentials=creds)


def _ensure_sheet_exists(service, spreadsheet_id: str, sheet_name: str) -> None:
    """シート（タブ）が無ければ作成する"""
    meta = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    titles = [s["properties"]["title"] for s in meta.get("sheets", [])]
    if sheet_name in titles:
        return

    # シート作成
    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={
            "requests": [
                {"addSheet": {"properties": {"title": sheet_name}}}
            ]
        },
    ).execute()


def _get_values(
    service, spreadsheet_id: str, range_a1: str, unformatted: bool = True
) -> List[List]:
    """
    値を取得（unformatted=True のときはシリアル日付やチェックボックスの真偽値をそのまま取得）
    """
    params = {
        "spreadsheetId": spreadsheet_id,
        "range": range_a1,
    }
    if unformatted:
        params["valueRenderOption"] = "UNFORMATTED_VALUE"
    resp = service.spreadsheets().values().get(**params).execute()
    return resp.get("values", [])


def _normalize_date_cell(cell) -> Optional[str]:
    """
    セルの値を 'm/d' 文字列に正規化。
    - 数字（シリアル日付）/ 'yyyy/m/d' / 'm/d' を許容
    - 空や不正は None
    """
    if cell is None:
        return None
    s = str(cell).strip()
    if s == "":
        return None

    # シリアル日付（数値）
    try:
        n = float(s)
        # Google Sheets シリアル起点は 1899-12-30
        base = datetime(1899, 12, 30)
        d = base + timedelta(days=int(n))
        return f"{d.month}/{d.day}"
    except Exception:
        pass

    # 文字列（yyyy/m/d or m/d）
    s = s.replace("-", "/")
    parts = s.split("/")
    try:
        if len(parts) == 3:  # yyyy/m/d
            y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
            return f"{m}/{d}"
        if len(parts) == 2:  # m/d
            m, d = int(parts[0]), int(parts[1])
            return f"{m}/{d}"
    except Exception:
        return None

    return None


def _to_bool(cell) -> bool:
    """チェックボックスの値を真偽値に丸める"""
    if isinstance(cell, bool):
        return cell
    s = str(cell).strip().upper()
    return s in ("TRUE", "1", "YES", "Y", "はい", "○")


def _to_float(cell) -> float:
    """数値化（空は0.0）"""
    try:
        if cell is None or str(cell).strip() == "":
            return 0.0
        return float(cell)
    except Exception:
        return 0.0


def _digits_to_int(s: str) -> Optional[int]:
    """文字列から数字だけ抜き出して int に。数字が無ければ None"""
    digits = "".join(ch for ch in str(s) if ch.isdigit())
    if digits == "":
        return None
    try:
        return int(digits)
    except Exception:
        return None


# =========================
# 公開関数
# =========================
def get_attendance(date_str: str, sheet_name: str) -> List[Dict]:
    """
    指定日付の勤怠データを取得（チェック=TRUEの行のみ）
    - A:日付, B:氏名, C:出勤, D:退勤, E:休憩(合計), F:勤務時間(h), G:チェック
    - 日付セルが結合で空の場合は直前の値を引き継ぐ（forward-fill）
    - 日付は 'm/d' に正規化して比較
    """
    spreadsheet_id = os.getenv("SPREADSHEET_ID")
    if not spreadsheet_id:
        raise ValueError("SPREADSHEET_ID環境変数が設定されていません")

    service = _get_service()

    try:
        values = _get_values(
            service, spreadsheet_id, f"'{sheet_name}'!A2:G1000", unformatted=True
        )
        if not values:
            return []

        rows: List[Dict] = []
        current_date_md: Optional[str] = None
        target_md = _normalize_date_cell(date_str) or date_str  # 念のため正規化

        for r in values:
            # セーフにカラム取得
            a = r[0] if len(r) > 0 else None  # 日付
            b = r[1] if len(r) > 1 else ""    # 氏名
            c = r[2] if len(r) > 2 else ""    # 出勤
            d = r[3] if len(r) > 3 else ""    # 退勤
            e = r[4] if len(r) > 4 else ""    # 休憩(合計)
            f = r[5] if len(r) > 5 else ""    # 勤務時間(h)
            g = r[6] if len(r) > 6 else False # チェック

            nd = _normalize_date_cell(a)
            if nd:
                current_date_md = nd
            elif current_date_md:
                nd = current_date_md  # forward-fill

            if nd != target_md:
                continue

            checked = _to_bool(g)
            if not checked:
                continue

            hours = _to_float(f)

            rows.append(
                {
                    "date": nd,
                    "name": str(b).strip(),
                    "in": str(c).strip(),
                    "out": str(d).strip(),
                    "break": str(e).strip(),
                    "hours": hours,
                    "checked": True,
                }
            )

        return rows

    except Exception as e:
        raise RuntimeError(f"Sheets read failed: {e}")


def get_wages(sheet_name: str) -> Dict[str, int]:
    """
    時給データを取得
    Returns:
        {'氏名': 1200, ...}
    """
    spreadsheet_id = os.getenv("SPREADSHEET_ID")
    if not spreadsheet_id:
        raise ValueError("SPREADSHEET_ID環境変数が設定されていません")

    service = _get_service()

    try:
        values = _get_values(
            service, spreadsheet_id, f"'{sheet_name}'!A2:B1000", unformatted=True
        )
        if not values:
            return {}

        wages: Dict[str, int] = {}
        for row in values:
            if len(row) < 2:
                continue
            name = str(row[0]).strip()
            wage_raw = row[1]
            # そのまま数値なら優先、文字列なら数字抽出
            if isinstance(wage_raw, (int, float)):
                wage = int(wage_raw)
            else:
                w = _digits_to_int(wage_raw)
                wage = w if w is not None else 0

            if name and wage > 0:
                wages[name] = wage

        return wages

    except Exception as e:
        raise RuntimeError(f"Sheets read failed: {e}")


def get_sales(date_str: str, sheet_name: str) -> int:
    """
    指定日付の売上を取得（未入力は0）
    - 日付は 'm/d' に正規化して比較
    """
    spreadsheet_id = os.getenv("SPREADSHEET_ID")
    if not spreadsheet_id:
        raise ValueError("SPREADSHEET_ID環境変数が設定されていません")

    service = _get_service()

    try:
        values = _get_values(
            service, spreadsheet_id, f"'{sheet_name}'!A2:B1000", unformatted=True
        )
        if not values:
            return 0

        target_md = _normalize_date_cell(date_str) or date_str

        for row in values:
            if len(row) < 2:
                continue
            row_date_md = _normalize_date_cell(row[0])
            if row_date_md != target_md:
                continue

            amount_cell = row[1]
            if isinstance(amount_cell, (int, float)):
                return int(amount_cell)
            v = _digits_to_int(amount_cell)
            return v if v is not None else 0

        return 0

    except Exception as e:
        raise RuntimeError(f"Sheets read failed: {e}")


def append_runlog(row: Dict) -> None:
    """
    runlogシートにログを追加（無ければシート作成→ヘッダー投入）
    keys: timestamp_jst, date, people, amount_total, sales, gross, success, skipped, errors
    """
    spreadsheet_id = os.getenv("SPREADSHEET_ID")
    if not spreadsheet_id:
        raise ValueError("SPREADSHEET_ID環境変数が設定されていません")

    sheet_name = os.getenv("SHEET_RUNLOG", "runlog")
    service = _get_service()

    try:
        # シートを確実に作成してからヘッダー確認
        _ensure_sheet_exists(service, spreadsheet_id, sheet_name)

        # ヘッダーが無ければ入れる（A1が空なら入れる）
        values = _get_values(
            service, spreadsheet_id, f"'{sheet_name}'!A1:I1", unformatted=True
        )
        if not values or not values[0]:
            header_row = [
                "timestamp_jst",
                "date",
                "people",
                "amount_total",
                "sales",
                "gross",
                "success",
                "skipped",
                "errors",
            ]
            service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=f"'{sheet_name}'!A1:I1",
                valueInputOption="RAW",
                body={"values": [header_row]},
            ).execute()

        log_row = [
            row.get("timestamp_jst", ""),
            row.get("date", ""),
            row.get("people", ""),
            row.get("amount_total", ""),
            row.get("sales", ""),
            row.get("gross", ""),
            row.get("success", ""),
            row.get("skipped", ""),
            row.get("errors", ""),
        ]

        service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=f"'{sheet_name}'!A:I",
            valueInputOption="RAW",
            body={"values": [log_row]},
        ).execute()

    except Exception as e:
        raise RuntimeError(f"Runlog append failed: {e}")


def get_incomplete_rows(date_str: str, sheet_name: str) -> List[str]:
    """
    未入力の行（氏名）を取得
    - A:日付が結合で空のときは直前日付を引き継ぐ
    - 出勤/退勤/休憩/勤務時間(h) のいずれかが空欄なら未入力とみなす
    """
    spreadsheet_id = os.getenv("SPREADSHEET_ID")
    if not spreadsheet_id:
        raise ValueError("SPREADSHEET_ID環境変数が設定されていません")

    service = _get_service()

    try:
        values = _get_values(
            service, spreadsheet_id, f"'{sheet_name}'!A2:G1000", unformatted=True
        )
        if not values:
            return []

        target_md = _normalize_date_cell(date_str) or date_str
        current_date_md: Optional[str] = None
        incomplete: List[str] = []

        for r in values:
            a = r[0] if len(r) > 0 else None  # 日付
            b = r[1] if len(r) > 1 else ""    # 氏名
            c = r[2] if len(r) > 2 else ""    # 出勤
            d = r[3] if len(r) > 3 else ""    # 退勤
            e = r[4] if len(r) > 4 else ""    # 休憩(合計)
            f = r[5] if len(r) > 5 else ""    # 勤務時間(h)

            nd = _normalize_date_cell(a)
            if nd:
                current_date_md = nd
            elif current_date_md:
                nd = current_date_md

            if nd != target_md:
                continue

            name = str(b).strip()
            in_time = str(c).strip()
            out_time = str(d).strip()
            break_time = str(e).strip()
            hours_str = str(f).strip()

            if name and (not in_time or not out_time or not break_time or not hours_str):
                incomplete.append(name)

        return incomplete

    except Exception as e:
        raise RuntimeError(f"Sheets read failed: {e}")
