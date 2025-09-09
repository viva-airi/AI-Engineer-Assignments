# API Basics - 最小実装

ChatGPT、Google Sheets、Google Calendar API の最小実装です。

## プロジェクト構成

```
4-2_api_basics/
├── chatgpt_client.py          # ChatGPT API クライアント
├── google_sheets_client.py    # Google Sheets API クライアント
├── google_calendar_client.py  # Google Calendar API クライアント
├── requirements.txt           # 必要なパッケージ
├── env_example.txt           # 環境変数の例
├── .gitignore               # Git管理除外設定
├── credentials/             # Google API認証情報（Git管理外）
└── tokens/                  # 認証トークン（Git管理外）
```

## セットアップ

### 1. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 2. 環境変数の設定

`env_example.txt`を参考に`.env`ファイルを作成してください：

```bash
# ChatGPT API設定
OPENAI_API_KEY=your_openai_api_key_here

# Google API設定
GOOGLE_APPLICATION_CREDENTIALS=credentials/google_credentials.json
GOOGLE_SHEETS_CREDENTIALS=credentials/google_credentials.json
GOOGLE_CALENDAR_CREDENTIALS=credentials/google_credentials.json

# スプレッドシートID（Google Sheets用）
SPREADSHEET_ID=your_spreadsheet_id_here

# カレンダーID（Google Calendar用）
CALENDAR_ID=your_calendar_id_here
```

### 3. API 認証情報の設定

#### ChatGPT API

1. [OpenAI Platform](https://platform.openai.com/)でアカウントを作成
2. API Key を生成
3. `.env`ファイルの`OPENAI_API_KEY`に設定

#### Google API

1. [Google Cloud Console](https://console.cloud.google.com/)でプロジェクトを作成
2. 以下の API を有効化：
   - Google Sheets API
   - Google Calendar API
3. 認証情報を作成（OAuth 2.0 クライアント ID）
4. 認証情報を`credentials/google_credentials.json`として保存

## 使用方法

### ChatGPT API

```python
from chatgpt_client import ChatGPTClient

# クライアントを初期化
chatgpt = ChatGPTClient()

# メッセージを送信
response = chatgpt.send_message("こんにちは！")
print(response)

# システムプロンプト付きで送信
response = chatgpt.send_message(
    "Pythonについて教えて",
    system_prompt="あなたはプログラミングの専門家です"
)
print(response)
```

### Google Sheets API

```python
from google_sheets_client import GoogleSheetsClient

# クライアントを初期化
sheets = GoogleSheetsClient()

# データを読み取り
data = sheets.read_range('Sheet1!A1:C10')
print(data)

# データを書き込み
values = [['名前', '年齢', '職業'], ['田中', '25', 'エンジニア']]
sheets.write_range('Sheet1!A1:C2', values)

# 新しい行を追加
new_row = ['佐藤', '30', 'デザイナー']
sheets.append_row('Sheet1!A:C', new_row)
```

### Google Calendar API

```python
from google_calendar_client import GoogleCalendarClient
from datetime import datetime, timedelta

# クライアントを初期化
calendar = GoogleCalendarClient()

# イベント一覧を取得
events = calendar.get_events(max_results=10)
for event in events:
    print(f"{event['summary']}: {event['start']}")

# 新しいイベントを作成
start_time = datetime.now() + timedelta(hours=1)
end_time = start_time + timedelta(hours=2)
event = calendar.create_event(
    summary="会議",
    start_time=start_time,
    end_time=end_time,
    description="重要な会議です"
)
```

## テスト実行

各クライアントを個別にテストできます：

```bash
# ChatGPT API テスト
python chatgpt_client.py

# Google Sheets API テスト
python google_sheets_client.py

# Google Calendar API テスト
python google_calendar_client.py
```

## 注意事項

- `.env`ファイル、`credentials/`ディレクトリ、`tokens/`ディレクトリは Git 管理から除外されています
- 初回実行時に Google API の認証フローがブラウザで開かれます
- 認証トークンは`tokens/`ディレクトリに保存され、次回以降は自動的に使用されます
- スプレッドシート ID は、Google Sheets の URL から取得できます
- カレンダー ID は通常`primary`で問題ありませんが、特定のカレンダーを使用する場合は設定してください

## トラブルシューティング

### よくあるエラー

1. **認証エラー**: 認証情報ファイルが正しく配置されているか確認
2. **API Key エラー**: 環境変数が正しく設定されているか確認
3. **権限エラー**: Google API のスコープが正しく設定されているか確認

### ログの確認

エラーが発生した場合は、コンソールに表示されるエラーメッセージを確認してください。
