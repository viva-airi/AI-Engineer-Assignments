import os, requests
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # .../01_slack_summary_to_line
load_dotenv(os.path.join(BASE_DIR, ".env"))

token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
assert token, "LINE_CHANNEL_ACCESS_TOKEN が未設定です"

url = "https://api.line.me/v2/bot/message/broadcast"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}
payload = {
    "messages": [{"type": "text", "text": "✅ Broadcastテスト：届いてる？"}]
}

r = requests.post(url, headers=headers, json=payload, timeout=15)
print(r.status_code, r.text)
r.raise_for_status()
print("OK: 送信できました。")
