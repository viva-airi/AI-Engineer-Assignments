# Slack-LINE Mirror

Slack の特定チャンネルの新着メッセージを取得し、LINE へミラー通知する CLI ツールです。

## 機能

- Slack チャンネルの新着メッセージを自動取得
- 取得したメッセージを LINE Messaging API v2 で通知
- 重複通知を防ぐためのタイムスタンプ管理
- エラーハンドリングとログ出力

## セットアップ

### 1. 依存関係のインストール

```bash
# 既存の .venv をアクティベート
.venv\Scripts\activate

# 必要なパッケージがインストールされていることを確認
pip install requests python-dotenv
```

### 2. Slack Bot の設定

1. [Slack API](https://api.slack.com/apps) でアプリを作成
2. 以下の権限を追加:
   - `channels:history` - チャンネルの履歴を読み取り
   - `chat:read` - メッセージを読み取り
3. Bot Token を取得 (`xoxb-` で始まる)
4. 監視したいチャンネルに Bot を招待

### 3. LINE Bot の設定

1. [LINE Developers Console](https://developers.line.biz/console/) でプロバイダーとチャンネルを作成
2. Messaging API チャンネルの Channel Access Token を取得
3. 通知先のユーザー ID を取得（webhook イベントまたは友達追加後のイベントから）

### 4. 環境設定ファイルの作成

```bash
# 例ファイルをコピー
copy 4-2-2\env\slack_line_mirror.env.example 4-2-2\env\slack_line_mirror.env

# 実際の値を設定
notepad 4-2-2\env\slack_line_mirror.env
```

必要な環境変数:

- `SLACK_BOT_TOKEN`: Slack Bot Token
- `SLACK_CHANNEL_ID`: 監視するチャンネル ID (C で始まる)
- `LINE_CHANNEL_ACCESS_TOKEN`: LINE Channel Access Token
- `LINE_TO_USER_ID`: 通知先の LINE ユーザー ID

## 使用方法

### 基本的な実行

```bash
# 環境変数のデフォルトチャンネルを使用
python -m kadai_4_2_2_08_API2.slack_line_mirror.pull

# 特定のチャンネルを指定
python -m kadai_4_2_2_08_API2.slack_line_mirror.pull --channel C1234567890

# 取得件数を指定
python -m kadai_4_2_2_08_API2.slack_line_mirror.pull --limit 100
```

### 実行例

```bash
> python -m kadai_4_2_2_08_API2.slack_line_mirror.pull --channel C1234567890 --limit 50
Slackチャンネル C1234567890 から新着メッセージを取得中...
[OK] Slack fetched: 5 messages (new=3)
[OK] LINE pushed: 3 / 3
[OK] latest_ts updated: 1726459123.456
```

## コマンドライン引数

- `--channel`, `-c`: 監視する Slack チャンネル ID (未指定時は環境変数を使用)
- `--limit`, `-l`: 取得するメッセージ数の上限 (デフォルト: 50)

## ファイル構成

```
kadai_4_2_2_08_API2/slack_line_mirror/
├── __init__.py
├── pull.py                    # メインエントリポイント
├── utils/
│   ├── __init__.py
│   ├── env_loader.py          # 環境変数読み込み
│   ├── slack_client.py        # Slack API クライアント
│   └── line_client.py         # LINE API クライアント
└── state/
    ├── .gitkeep
    └── slack_latest_ts.json   # 最新タイムスタンプ保存 (自動生成)
```

## 状態管理

- `kadai_4_2_2_08_API2/slack_line_mirror/state/slack_latest_ts.json` に最新のメッセージタイムスタンプを保存
- 重複通知を防ぐため、前回処理したタイムスタンプ以降のメッセージのみを取得

## エラーハンドリング

### よくあるエラーと対処法

#### `invalid_auth` (Slack API)

- **原因**: Slack Bot Token が無効または権限不足
- **対処法**:
  - Token が正しく設定されているか確認
  - 必要な権限 (`channels:history`, `chat:read`) が付与されているか確認
  - Bot がチャンネルに招待されているか確認

#### `channel_not_found` (Slack API)

- **原因**: 指定されたチャンネル ID が存在しない、または Bot がアクセスできない
- **対処法**:
  - チャンネル ID が正しいか確認 (C で始まる)
  - Bot がチャンネルに招待されているか確認
  - プライベートチャンネルの場合は Bot に適切な権限を付与

#### `401 Unauthorized` (LINE API)

- **原因**: LINE Channel Access Token が無効
- **対処法**:
  - Token が正しく設定されているか確認
  - Token の有効期限を確認
  - LINE Developers Console で新しい Token を生成

#### `403 Forbidden` (LINE API)

- **原因**: ユーザー ID が無効、または Bot がユーザーと友達でない
- **対処法**:
  - ユーザー ID が正しいか確認
  - Bot とユーザーが友達になっているか確認
  - ユーザーが Bot をブロックしていないか確認

## スクリーンショット撮影

以下のファイル名でスクリーンショットを撮影してください:

- `4-2-2/4-2-2_screenshots/08_slack_line_mirror_runlog.png` - 実行ログ
- `4-2-2/4-2-2_screenshots/08_slack_line_mirror_img.png` - 実行結果（LINE 通知の表示など）

## 技術仕様

### Slack API

- エンドポイント: `https://slack.com/api/conversations.history`
- 認証: Bearer Token
- パラメータ: `channel`, `limit`, `oldest`

### LINE Messaging API

- エンドポイント: `https://api.line.me/v2/bot/message/push`
- 認証: Bearer Token
- メッセージ形式: テキストメッセージ

### メッセージ整形

- フォーマット: `[#channel] user: text`
- 長文の場合は省略して Slack パーマリンクを付加
- 文字数制限: 1000 文字（LINE API 制限を考慮）

## トラブルシューティング

### 環境変数が読み込まれない

- ファイルパスが正しいか確認: `4-2-2/env/slack_line_mirror.env`
- ファイルの文字エンコーディングが UTF-8 か確認
- 改行コードが適切か確認

### 権限エラーが発生する

- Slack Bot の権限スコープを再確認
- チャンネルへの招待状況を確認
- LINE Bot の友達状況を確認

### メッセージが送信されない

- ネットワーク接続を確認
- API Token の有効性を確認
- ユーザー ID の形式を確認

## ライセンス

このプロジェクトは学習目的で作成されています。
