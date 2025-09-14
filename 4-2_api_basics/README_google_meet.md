# Google Meet クライアント

Google Calendar API を使用して Google Meet 会議を作成する CLI ツールです。

## 機能

- Google Meet 会議の自動作成
- 参加者の自動招待
- 会議 URL の自動生成
- 詳細なログ出力（--verbose オプション）

## 前提条件

1. Google Cloud Console でプロジェクトを作成
2. Google Calendar API を有効化
3. OAuth2 認証情報をダウンロードして `credentials/google_credentials.json` に配置
4. 必要な Python パッケージをインストール

```bash
pip install -r requirements.txt
```

## 使用方法

### 基本的な使用方法

```bash
python google_meet_client.py --title "会議のタイトル" --start "2024-01-01 10:00" --end "2024-01-01 11:00"
```

### オプション

- `--title`: 会議のタイトル（必須）
- `--start`: 開始時刻（必須、例: "2024-01-01 10:00"）
- `--end`: 終了時刻（必須、例: "2024-01-01 11:00"）
- `--timezone`: タイムゾーン（デフォルト: Asia/Tokyo）
- `--description`: 会議の説明（任意）
- `--attendees`: 参加者のメールアドレス（カンマ区切り、任意）
- `--verbose`: 詳細ログを表示（任意）

### 使用例

#### 基本的な会議作成

```bash
python google_meet_client.py \
  --title "週次ミーティング" \
  --start "2024-01-15 14:00" \
  --end "2024-01-15 15:00"
```

#### 参加者を指定した会議作成

```bash
python google_meet_client.py \
  --title "プロジェクト会議" \
  --start "2024-01-15 10:00" \
  --end "2024-01-15 11:00" \
  --description "新機能の設計について議論" \
  --attendees "user1@example.com,user2@example.com" \
  --verbose
```

#### 異なるタイムゾーンでの会議作成

```bash
python google_meet_client.py \
  --title "国際会議" \
  --start "2024-01-15 09:00" \
  --end "2024-01-15 10:00" \
  --timezone "America/New_York"
```

## 出力形式

成功時は以下の JSON 形式で出力されます：

```json
{
  "eventId": "イベントID",
  "htmlLink": "Google Calendarのリンク",
  "meetUrl": "Google MeetのURL",
  "start": "開始時刻（ISO形式）",
  "end": "終了時刻（ISO形式）",
  "timeZone": "タイムゾーン"
}
```

## エラーハンドリング

- 認証エラー: 認証情報ファイルが見つからない、または無効な場合
- 日時解析エラー: 日時形式が正しくない場合
- API エラー: Google Calendar API でのエラー
- 失敗時は非 0 の終了コードで終了し、エラーメッセージを標準エラー出力に表示

## テスト

テストスクリプトを実行して動作確認ができます：

```bash
python test_google_meet.py
```

## 注意事項

- 初回実行時はブラウザで Google アカウントの認証が必要です
- 認証トークンは `tokens/token.json` に保存されます
- 会議の作成には Google Calendar API の適切な権限が必要です
