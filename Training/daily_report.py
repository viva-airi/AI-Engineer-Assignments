# daily_report.py
from __future__ import annotations
import csv, json, re, os
import datetime as dt
from pathlib import Path
import textwrap

# ====== パス設定 ======
DATA_DIR     = Path("data")
COUNTER_FILE = DATA_DIR / "counter.json"           # No.の保存
CASH_DIR     = DATA_DIR / "cashflow"               # 月次CSV
BASE_DIR     = DATA_DIR / "cashflow_base"          # 月初累計の基準
REPORTS_DIR  = Path("reports")

# ====== 初期値 ======
START_NO = 7  # ← No.8から始めたい場合は 7 のまま（初回 +1 されて8から開始）

LIFE_VISION = textwrap.dedent("""
🔴自分を守る力を手に入れ、誰にも支配されず、自分らしく誇りを持って生きる
 →力をつけることで不安から自由になり、大切な人や同じように苦しむ人を守れる存在になる！

【自ら稼ぐ力を手に入れ、自分の価値を上げる（経済力・ビジネス力の強化）
辻さんのマインドセットを実践し、未来を築き上げる（思考・判断力の強化）
過去にとらわれず、マイナスを食べて強くなる（メンタル・自己肯定感）
1日30分以上の運動習慣を継続する（健康・体力づくり）
信頼できる辻さんのもとで学び、3年以内に驚かせる（環境・師匠との約束）
学びを継続し、教養を深めて視野を広げる（知識・インプット）
人に感動を与えるアウトプットを積み重ねる（仕事・自己表現）
大切な人を守り、同じように苦しむ人の力になる（使命・人間関係）】
""").strip()

GOALS_YEAR = [
    "AIエンジニア養成講座の基礎カリキュラムを年内に修了する",
    "毎日氷水顔つけ＋30分運動を継続する（体力・習慣）",
    "自分の弱み（体調・感情の波）を把握し、必要性でコントロールできる状態にする",
    "業務委託の美顔器バナー制作で「現場での流れ」と「オンラインでの仕事のやりとり」を体験し、掴む",
]

GOALS_MONTH = [
    "毎日マインドセット0.1.2を読むor聴く",
    "自己流でしない。疑問やわからないときはすぐ辻さんに聞く。",
    "氷水顔つけ＋30分運動　を習慣化する",
    "今月の目標を守り続ける",
]

# ====== ユーティリティ ======
def ensure_dirs():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CASH_DIR.mkdir(parents=True, exist_ok=True)
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

def normalize_int(s: str) -> int:
    """'145.815' や '145,815' を 145815 に正規化（空や不正は0）"""
    if not s:
        return 0
    s2 = re.sub(r"[,\.\s]", "", s)
    return int(s2) if s2.isdigit() else 0

def load_no() -> int:
    if COUNTER_FILE.exists():
        try:
            return json.loads(COUNTER_FILE.read_text(encoding="utf-8")).get("no", START_NO)
        except Exception:
            return START_NO
    return START_NO

def save_no(no: int):
    COUNTER_FILE.write_text(json.dumps({"no": no}, ensure_ascii=False, indent=2), encoding="utf-8")

def month_key(d: dt.date) -> str:
    return d.strftime("%Y-%m")

def month_csv_path(d: dt.date) -> Path:
    return CASH_DIR / f"{month_key(d)}.csv"

def month_base_path(d: dt.date) -> Path:
    return BASE_DIR / f"{month_key(d)}.json"

def read_month_rows(d: dt.date):
    p = month_csv_path(d)
    rows = []
    if p.exists():
        with p.open("r", encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                rows.append(r)
    return rows

def append_month_row(d: dt.date, income: int, expense: int, note: str):
    p = month_csv_path(d)
    is_new = not p.exists()
    with p.open("a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["date","income","expense","note"])
        if is_new:
            w.writeheader()
        w.writerow({"date": d.isoformat(), "income": income, "expense": expense, "note": note})

def read_month_base(d: dt.date):
    bp = month_base_path(d)
    if bp.exists():
        try:
            j = json.loads(bp.read_text(encoding="utf-8"))
            return int(j.get("base_income", 0)), int(j.get("base_expense", 0))
        except Exception:
            return 0, 0
    return 0, 0

def write_month_base(d: dt.date, base_income: int, base_expense: int):
    bp = month_base_path(d)
    bp.write_text(json.dumps({"base_income": base_income, "base_expense": base_expense},
    ensure_ascii=False, indent=2), encoding="utf-8")

def month_totals_with_base(d: dt.date):
    base_inc, base_exp = read_month_base(d)
    inc = exp = 0
    for r in read_month_rows(d):
        try:
            inc += int(r.get("income", 0))
            exp += int(r.get("expense", 0))
        except ValueError:
            pass
    return base_inc + inc, base_exp + exp

def polite_wrap(s: str) -> str:
    """軽い整形：段落トリム＋句点付与"""
    lines = [ln.strip(" 　") for ln in s.strip().splitlines() if ln.strip()]
    def fix(p: str) -> str:
        if not p: return ""
        return p if p[-1] in "。！？!?" else p + "。"
    return "\n".join(fix(p) for p in lines)

def grand_total():
    """全期間の収支累計（基準＋CSV合算）"""
    total = 0
    for csv_file in CASH_DIR.glob("*.csv"):
        with csv_file.open("r", encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                try:
                    total += int(r.get("income", 0)) - int(r.get("expense", 0))
                except ValueError:
                    pass
    for base_file in BASE_DIR.glob("*.json"):
        j = json.loads(base_file.read_text(encoding="utf-8"))
        bi = int(j.get("base_income", 0))
        be = int(j.get("base_expense", 0))
        total += (bi - be)
    return total

# ====== GPT整形（任意） ======
def gpt_polish_or_fallback(text: str) -> str:
    """
    OPENAI_API_KEY が設定されていれば GPT-4o-mini で“丁寧・礼儀正しい一人称”に整形。
    失敗時や未設定時は polite_wrap で返す。
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return polite_wrap(text)
    try:
        # OpenAI Python SDK v1 以降
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        sys = (
            "あなたは丁寧で礼儀正しい日本語ライターです。"
            "口語のメモを、落ち着いた一人称（私は〜）で簡潔に整えます。"
            "過剰な誇張や絵文字は避け、端的で前向きな言い回しにしてください。"
        )
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": sys},
                {"role": "user", "content": text.strip()},
            ],
            temperature=0.4,
        )
        out = resp.choices[0].message.content.strip()
        return out or polite_wrap(text)
    except Exception:
        return polite_wrap(text)

# ====== メイン ======
def main():
    ensure_dirs()
    today = dt.date.today()
    wd = ["月","火","水","木","金","土","日"][today.weekday()]

    # No.管理
    no = load_no() + 1
    save_no(no)

    # 入力
    print("=== 日報入力 ===")
    expense_line = input("今日の支出（例: 3929 ／空=0）：").strip()
    diary_raw = input("今日の振り返り（自由文。改行は \\n ）：\n").replace("\\n","\n")

    # 支出（数値だけ）
    expense_i = normalize_int(expense_line)

    # 今月の基準（必要に応じて上書き）
    print("\n=== 今月の基準累計（必要なら入力） ===")
    base_inc_in = input("今月の収入累計（基準） 上書き（空=変更なし）：").strip()
    base_exp_in = input("今月の支出累計（基準） 上書き（空=変更なし）：").strip()
    if base_inc_in or base_exp_in:
        base_inc = normalize_int(base_inc_in)
        base_exp = normalize_int(base_exp_in)
        write_month_base(today, base_inc, base_exp)
        print(f"→ 基準を設定：収入{base_inc:,}円 / 支出{base_exp:,}円")

    # 今日の行をCSVへ追記（支出のみ）
    append_month_row(today, 0, expense_i, "auto")

    # 合計（基準＋CSV）
    month_inc_total, month_exp_total = month_totals_with_base(today)
    month_net = month_inc_total - month_exp_total

    # 表示を手入力で上書きするか？（ズレた時の調整用）
    print("\n=== 表示の手動上書き（ズレ調整用） ===")
    use_override = input("画面表示の今月累計を手入力で上書きしますか？ [y/n]：").strip().lower() == "y"
    if use_override:
        disp_inc_in = input("表示用：今月の収入（例: 145,815）：").strip()
        disp_exp_in = input("表示用：今月の支出（例: 84,519）：").strip()
        disp_inc = normalize_int(disp_inc_in)
        disp_exp = normalize_int(disp_exp_in)
        disp_net = disp_inc - disp_exp
        # その値を「今後の基準」として保存するか？
        commit = input("この表示値を基準値として保存しますか？ [y/n]：").strip().lower() == "y"
        if commit:
            write_month_base(today, disp_inc, disp_exp)
            month_inc_total, month_exp_total = disp_inc, disp_exp
            month_net = disp_net
        else:
            # 保存はせず、今回の出力だけ差し替え
            month_inc_total, month_exp_total, month_net = disp_inc, disp_exp, disp_net

    # 総累計
    g_total = grand_total()
    if use_override and not commit:
        # 表示のみ上書きの場合、総累計も表示だけ調整（CSV値との差分は無視）
        # ここでは「総累計＝表示用の今月差引＋過去月分（近似）」とせず、簡潔に今月表示に合わせる
        pass  # 必要になったらロジックを追加

    # 目標チェック（y=できた / n=未達）
    print("\n=== 今月の目標チェック（y=できた / n=未達） ===")
    checks = []
    for g in GOALS_MONTH:
        ans = input(f"- {g} ? [y/n]: ").strip().lower()
        checks.append((g, ans == "y"))

    # 振り返り：GPT or 簡易整形
    use_gpt = input("\n振り返りをGPTで整形しますか？ [y/n]：").strip().lower() == "y"
    diary = gpt_polish_or_fallback(diary_raw) if use_gpt else polite_wrap(diary_raw)

    # 出力先
    out_dir = REPORTS_DIR / today.strftime("%Y") / today.strftime("%Y-%m")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{today.strftime('%Y-%m-%d')}_日報.txt"

    # 目標の表示（先頭：y[🌸] / n[💀]、行末に絵文字は付けない）
    goals_year_txt  = "\n".join(f"{i+1}. {g}" for i,g in enumerate(GOALS_YEAR))
    goals_month_txt = "\n".join(
        (("[🌸]" if ok else "[💀]") + " " + g) for g,ok in checks
    )

    # テキスト生成
    txt = f"""日報 No.{no}
日付: {today}（{wd}曜日）

[経営会議報告]
本日の日報（プチ経営会議）を共有させていただきます！

・人生ビジョン、人生理念またはテーマ
{LIFE_VISION}

・12/31までの目標
{goals_year_txt}

●今月の目標（チェック）
{goals_month_txt}

●今月のキャッシュフロー
→収入 {month_inc_total:,}円ー支出 {month_exp_total:,}円＝ {month_net:,}円予定

●今日の支出
→ {expense_i:,}円

●今月累計
→ {month_net:,}円

【総累計 {g_total:,}円】

[今日の振り返り]
{diary}
""".strip() + "\n"

    out_path.write_text(txt, encoding="utf-8")
    print("\n✅ 日報を保存しました：", out_path.resolve())
    print("   月次CSV：", month_csv_path(today).resolve())
    print("   月初基準：", month_base_path(today).resolve())

if __name__ == "__main__":
    main()
