# 5-1-1 Slack 要約 LINE 送信ツール

## 🎯 概要

Slack チャンネル内の直近 N 時間のメッセージを取得し、OpenAI で要約して LINE に自動送信するツールです。  
`LINE_USER_ID` が設定されている場合は **個別送信（push）**、未設定の場合は **全員送信（broadcast）** になります。

---

## 🗂 フォルダ構成

5-1_projects/
└── 01_slack_summary_to_line/
├── src/
│ ├── slack_client.py
│ ├── summarizer.py
│ └── line_client.py
├── runlogs/
├── .env.example
├── main.py
└── README.md

yaml
コードをコピーする

---

## ⚙️ 使用技術

| 項目           | 内容                                          |
| -------------- | --------------------------------------------- |
| 言語           | Python 3.13                                   |
| 仮想環境       | .venv（共通環境）                             |
| 使用 API       | Slack API / OpenAI API / LINE Messaging API   |
| 主要ライブラリ | slack_sdk / requests / openai / python-dotenv |

---

## 🔑 .env 設定例

Slack
SLACK_BOT_TOKEN= xoxb-******\*******
SLACK_CHANNEL_ID= C******\*******

LINE
LINE_CHANNEL_ACCESS_TOKEN= ******\*******

任意（個別送信する場合のみ設定）
LINE_USER_ID= U******\*******

OpenAI
OPENAI_API_KEY= sk-******\*******

要約範囲（時間）
SUMMARY_TIME_RANGE_HOURS=12

yaml
コードをコピーする

---

## ▶️ 実行方法

```powershell
cd C:\Dev\projects\AI_Assignments\5-1_projects
.\.venv\Scripts\activate
cd 01_slack_summary_to_line
pip install slack_sdk openai requests python-dotenv  # 初回のみ
python .\main.py --hours 12
📱 実行結果
ターミナル出力

makefile
コードをコピーする
Slack要約LINE送信を開始します（直近12時間）...
Slackメッセージを取得中...
取得したメッセージ数: 5件
LINEに送信中...
LINE送信が完了しました。
処理が完了しました。
LINE通知例

コードをコピーする
【Slackまとめ（直近12h）】
・本日の作業を開始します
・API連携テスト完了
・明日はREADME整理予定
🧾 Runlog & スクリーンショット
保存先	内容
runlogs/	実行ごとの結果ログ（JSONL形式）
screenshots/01_slack_summary_to_line/	提出用画像（Slack権限 / 実行 / LINE受信など）

🧠 トラブルシュート
症状	対応
.venv を有効化できない	PowerShellで Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass を実行
.env コピー時にエラー	cd 01_slack_summary_to_line で正しいフォルダに移動してから実行
Slackメッセージが0件	Botをチャンネルに /invite して、直近に投稿を追加する
LINE送信時にuserId不要？	友だち＝自分1人なら broadcast でOK（今回はこちらで動作確認済み）

✅ Definition of Done
 フォルダ・.env.example 構成済み

 Slack → OpenAI → LINE連携動作確認

 実行ログ・スクショ保存方針提示

 CLIで12h範囲の要約送信が成功

🚀 今後の改善案
LINE送信文のフォーマットを整形（改行・箇条書きの最適化）

Slackスレッドや投稿者名を含む要約へ拡張

APIエラー（429, 5xx）リトライ制御の追加

common/line_client.py として再利用可能化

作者メモ
今回最も時間を取ったのは「LINE_USER_IDの扱い」でした。
最終的に broadcast（全員送信） でも動作し、
Push送信（個別） が必要な場合のみ LINE_USER_ID を設定すればよいと理解しました。
Broadcastで送っても、友だちが自分1人なら結果は同じになるため、MVPとしては十分でした。
```
