#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.patheffects import withStroke

PASTEL_PINKS = ["#F8BBD0", "#FADADD", "#FFCDD2", "#F48FB1", "#F06292", "#FDCFE8"]

def setup_japanese_font():
    try:
        yugoth = r"C:\Windows\Fonts\YuGothR.ttc"
        if os.path.exists(yugoth):
            fm.fontManager.addfont(yugoth)
            plt.rcParams["font.family"] = "Yu Gothic"
        else:
            plt.rcParams["font.sans-serif"] = ["Meiryo", "Noto Sans CJK JP", "Noto Sans JP", "DejaVu Sans"]
            plt.rcParams["font.family"] = "sans-serif"
    except Exception:
        plt.rcParams["font.sans-serif"] = ["Meiryo", "Noto Sans CJK JP", "Noto Sans JP", "DejaVu Sans"]
        plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["axes.unicode_minus"] = False

def _clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.rename(columns=lambda c: str(c).strip().replace("\ufeff", ""), inplace=True)
    return df

def _numeric_scores(series: pd.Series) -> pd.Series:
    s = (series.astype(str)
        .str.replace("点", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.replace("　", "", regex=False)
        .str.strip())
    return pd.to_numeric(s, errors="coerce")

# ---------- 円グラフ ----------
def create_pie_chart(df: pd.DataFrame, out_dir: Path) -> Path:
    print("📊 円グラフ（所属別参加者数）を生成中...")
    counts = df["所属"].value_counts().sort_values(ascending=False)
    out_path = out_dir / "pie_affiliation.png"
    if counts.empty:
        print("⚠️ 所属データがないため円グラフをスキップ")
        return out_path

    fig, ax = plt.subplots(figsize=(8, 6), dpi=200)
    colors = (PASTEL_PINKS * ((len(counts) // len(PASTEL_PINKS)) + 1))[: len(counts)]

    def autopct_fmt(pct):
        absolute = int(round(pct/100.0 * counts.sum()))
        return f"{pct:0.1f}%\n({absolute}名)"

    wedges, texts, autotexts = ax.pie(
        counts.values,
        labels=counts.index,
        autopct=autopct_fmt,
        colors=colors,
        startangle=90,
        pctdistance=0.75,
        textprops={"fontsize": 11},
        wedgeprops={"linewidth": 1.2, "edgecolor": "#E91E63"}
    )
    # 値ラベルに白縁取り（読みやすさUP）
    for t in autotexts:
        t.set_path_effects([withStroke(linewidth=3, foreground="white")])

    ax.set_title("所属別参加者数の割合", fontsize=18, fontweight="bold", pad=18)
    ax.legend(wedges, [f"{n}（{c}名）" for n, c in counts.items()],
            title="所属", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1), fontsize=10)
    ax.axis("equal")
    plt.tight_layout()
    plt.savefig(out_path, bbox_inches="tight", dpi=200)
    plt.close()
    print(f"✅ 円グラフを保存しました: {out_path}")
    return out_path

# ---------- 棒グラフ ----------
def create_bar_chart(df: pd.DataFrame, out_dir: Path) -> Path:
    print("📊 棒グラフ（参加者別平均スコア）を生成中...")
    out_path = out_dir / "bar_mean_score.png"

    mean_scores = (df.groupby("名前")["スコア"]
                    .mean().round(1).sort_values(ascending=False))
    if mean_scores.empty:
        print("⚠️ 平均スコアを計算できないため棒グラフをスキップ")
        return out_path

    # 棒が多いときは横幅を自動で広げる（1本あたり0.32インチ目安）
    width = max(8, 0.32 * len(mean_scores))
    fig, ax = plt.subplots(figsize=(width, 6), dpi=200)

    # 優しいグラデーション（パステルの繰り返し）
    colors = (PASTEL_PINKS * ((len(mean_scores) // len(PASTEL_PINKS)) + 1))[: len(mean_scores)]

    bars = ax.bar(range(len(mean_scores)), mean_scores.values,
                color=colors, edgecolor="#E91E63", linewidth=0.8, alpha=0.9)

    ax.set_xlabel("参加者", fontsize=12, fontweight="bold")
    ax.set_xticks(range(len(mean_scores)))
    ax.set_xticklabels(mean_scores.index, rotation=45, ha="right", fontsize=10)
    ax.set_ylabel("平均スコア", fontsize=12, fontweight="bold")
    ax.set_ylim(0, max(100, mean_scores.max() * 1.12))
    ax.margins(y=0.08)
    ax.set_title("参加者別平均スコア（降順）", fontsize=18, fontweight="bold", pad=14)
    ax.grid(True, axis="y", alpha=0.25, linestyle="--")

    # 数値注記：白縁取り＋少し上に
    for x, (bar, score) in enumerate(zip(bars, mean_scores.values)):
        txt = ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.8,
                    f'{int(round(score))}', ha="center", va="bottom", fontsize=10, fontweight="bold")
        txt.set_path_effects([withStroke(linewidth=3, foreground="white")])

    plt.tight_layout()
    plt.savefig(out_path, bbox_inches="tight", dpi=200)
    plt.close()
    print(f"✅ 棒グラフを保存しました: {out_path}")
    return out_path

# ---------- ヒストグラム ----------
def create_histogram(df: pd.DataFrame, out_dir: Path) -> Path:
    print("📊 ヒストグラム（スコア分布）を生成中...")
    out_path = out_dir / "hist_scores.png"
    scores = df["スコア"].dropna().values
    if scores.size == 0:
        print("⚠️ スコアがないためヒストグラムをスキップ")
        return out_path

    fig, ax = plt.subplots(figsize=(8, 6), dpi=200)

    # 視認性を優先して bins=15（データ量35前後にちょうど良い）
    n, bins, patches = ax.hist(scores, bins=15, color=PASTEL_PINKS[0],
                            edgecolor="#E91E63", linewidth=1, alpha=0.75)

    mean_score = float(np.mean(scores))
    median_score = float(np.median(scores))
    std_score = float(np.std(scores, ddof=1)) if scores.size > 1 else 0.0

    ax.axvline(mean_score, color="#F06292", linestyle="--", linewidth=2, label=f"平均: {mean_score:.1f}点")
    ax.axvline(median_score, color="#F48FB1", linestyle=":", linewidth=2, label=f"中央値: {median_score:.1f}点")

    # 余白＆コントラスト
    xmin, xmax = max(0, scores.min()-5), min(100, scores.max()+5)
    ax.set_xlim(xmin, xmax)
    ax.set_xlabel("スコア", fontsize=12, fontweight="bold")
    ax.set_ylabel("人数", fontsize=12, fontweight="bold")
    ax.set_title("全参加者スコアの分布", fontsize=18, fontweight="bold", pad=14)
    ax.grid(True, alpha=0.25, linestyle="--")

    # 凡例は枠外に逃がす
    ax.legend(loc="upper left", bbox_to_anchor=(1, 1))

    # 情報ボックス（読みやすい位置に）
    txt = f"データ数: {len(scores)}件\n標準偏差: {std_score:.1f}点"
    ax.text(0.02, 0.98, txt, transform=ax.transAxes, va="top",
            bbox=dict(boxstyle="round", facecolor="white", alpha=0.9))

    plt.tight_layout()
    plt.savefig(out_path, bbox_inches="tight", dpi=200)
    plt.close()
    print(f"✅ ヒストグラムを保存しました: {out_path}")
    return out_path

def main():
    print("🎯 CSVデータからグラフ生成プログラム")
    print("=" * 50)

    base_dir = Path(__file__).parent
    out_dir = base_dir / "output"
    out_dir.mkdir(exist_ok=True)

    csv_path = base_dir / "課題3.csv"
    print(f"📂 CSVファイルを読み込み中: {csv_path}")

    df = pd.read_csv(csv_path, encoding="utf-8-sig")
    _clean_columns(df)
    for col in ["名前", "所属", "スコア"]:
        if col not in df.columns:
            raise KeyError(f"必要な列が見つかりません: {col} / 実際: {list(df.columns)}")

    df["スコア"] = _numeric_scores(df["スコア"])
    df = df.dropna(subset=["スコア"])

    print(f"✅ 読み込み完了 | 件数: {len(df)} / 参加者: {df['名前'].nunique()}名 / 所属: {df['所属'].nunique()}")

    setup_japanese_font()
    print("🚀 グラフ生成を開始します...")

    pie = create_pie_chart(df, out_dir)
    bar = create_bar_chart(df, out_dir)
    hist = create_histogram(df, out_dir)

    print("\n" + "=" * 50)
    print("🎉 全てのグラフの生成が完了しました！")
    print("=" * 50)
    print(f"📊 円: {pie}")
    print(f"📊 棒: {bar}")
    print(f"📊 ヒ: {hist}")
    print(f"📁 出力: {out_dir.resolve()}")

if __name__ == "__main__":
    main()
