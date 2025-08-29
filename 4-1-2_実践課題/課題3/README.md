# 課題 3: CSV データからグラフ生成

## 概要

CSV ファイル（課題 3.csv）から 3 種類のグラフを生成する Python プログラムです。

## 生成されるグラフ

### 1. 円グラフ（pie_affiliation.png）

- 所属ごとの参加者数の割合を表示
- パーセンテージとラベル付き
- 凡例付き

### 2. 棒グラフ（bar_mean_score.png）

- 参加者ごとの平均スコアを降順で表示
- 軸ラベル・タイトル・数値注記付き
- グリッド線付き

### 3. ヒストグラム（hist_scores.png）

- 全参加者スコアの分布（bins=20）
- 平均線・中央値線表示
- 統計情報付き

## ファイル構成

```
課題3/
├── csv_charts.py          # メインプログラム
├── requirements.txt       # 必要なライブラリ
├── README.md             # このファイル
└── output/               # 生成されたグラフの保存先
    ├── pie_affiliation.png
    ├── bar_mean_score.png
    └── hist_scores.png
```

## 必要な環境

- Python 3.6 以上
- pandas
- matplotlib
- numpy

## セットアップ

### 1. ライブラリのインストール

```bash
pip install -r requirements.txt
```

### 2. プログラムの実行

```bash
cd 課題3
python csv_charts.py
```

## 特徴

- **日本語フォント対応**: Yu Gothic、丸ゴ系、Meiryo、Noto Sans を自動検出
- **パステルピンク基調**: 統一された配色で美しいグラフ
- **高品質出力**: 8x6 インチ、200dpi で高解像度
- **自動レイアウト**: 余白の自動調整
- **エラーハンドリング**: ファイル読み込みエラーの適切な処理

## 出力ファイル

- `pie_affiliation.png`: 所属別参加者数の円グラフ
- `bar_mean_score.png`: 参加者別平均スコアの棒グラフ
- `hist_scores.png`: スコア分布のヒストグラム

## 注意事項

- CSV ファイルは UTF-8-SIG エンコーディングで保存されている必要があります
- 列名は「名前」「所属」「スコア」である必要があります
- 出力ディレクトリ（output/）は自動的に作成されます
