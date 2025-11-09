# 5-1-2 EC サイト情報取得 →Google スプレッドシート反映（スクレイピング版）

## 目的・スコープ

学習用・低頻度での EC サイト情報取得と Google スプレッドシートへの自動反映システム。
スクレイピング技術を用いて Amazon 等の EC サイトから商品情報を取得し、管理用スプレッドシートに格納します。

**⚠️ 現状は雛形のため実行ロジックは未実装 ⚠️**

## スプレッドシート構成（4 タブ）

### ASIN_LIST

- 管理対象 ASIN の一覧
- 列定義：
  - ASIN: 商品識別子
  - 商品名: 商品タイトル
  - 登録日: 管理開始日
  - ステータス: アクティブ/非アクティブ

### PRODUCTS_HISTORY

- 商品情報の履歴データ
- 列定義：
  - ASIN: 商品識別子
  - 取得日時: データ取得時刻
  - 価格: 現在価格
  - 在庫状況: 在庫有無
  - レビュー数: レビュー総数
  - 評価: 星評価

### KEYWORDS

- 検索キーワード管理
- 列定義：
  - キーワード: 検索用キーワード
  - カテゴリ: 商品カテゴリ
  - 優先度: 検索優先度
  - 最終実行: 最後の検索実行日時

### RANKING_SNAPSHOTS

- ランキング情報のスナップショット
- 列定義：
  - キーワード: 検索キーワード
  - 取得日時: スナップショット取得時刻
  - 順位: 検索結果順位
  - ASIN: 該当商品の ASIN
  - 商品名: 商品タイトル

## 実行モード（未実装）

### favorites_update

お気に入り商品の情報を定期的に更新するモード

- ASIN_LIST から対象商品を取得
- 各商品の最新情報をスクレイピング
- PRODUCTS_HISTORY に履歴データを追加

### compare_topN

指定キーワードでの検索結果上位 N 件を比較するモード

- KEYWORDS から検索キーワードを取得
- 検索結果の上位商品をスクレイピング
- RANKING_SNAPSHOTS に結果を記録

## セットアップ手順

### 前提条件

- Python 3.11 以上
- Google Cloud Platform アカウント（スプレッドシート API 有効化）
- サービスアカウント認証ファイル

### インストール手順

1. 仮想環境の作成とアクティベート

```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac
```

2. 依存関係のインストール

```bash
pip install -r requirements.txt
```

3. 環境変数の設定

```bash
cp .env.example .env
# .envファイルを編集して必要な値を設定
```

## 環境変数設定（.env）

```env
SPREADSHEET_ID=                    # GoogleスプレッドシートのID
WORKSHEET_ASIN_LIST=ASIN_LIST     # ASIN一覧タブ名
WORKSHEET_PRODUCTS=PRODUCTS_HISTORY # 商品履歴タブ名
WORKSHEET_KEYWORDS=KEYWORDS       # キーワードタブ名
WORKSHEET_RANKING=RANKING_SNAPSHOTS # ランキングタブ名
GOOGLE_APPLICATION_CREDENTIALS=credentials/service_account.json # 認証ファイルパス
REQUEST_TIMEOUT_SEC=15            # リクエストタイムアウト（秒）
```

## 将来の拡張予定

### 通知機能

- 価格変動アラート
- 在庫復活通知
- ランキング変動通知

### PA-API 連携

- より効率的なデータ取得
- レート制限の回避
- より詳細な商品情報取得

### データ分析機能

- 価格推移グラフ
- ランキング変動分析
- 競合商品比較

## 注意事項

- 本システムは学習目的で作成されています
- スクレイピングは対象サイトの利用規約を遵守してください
- 過度なリクエストは避け、適切な間隔を設けてください
- 商用利用の際は各サイトの API 利用を検討してください
