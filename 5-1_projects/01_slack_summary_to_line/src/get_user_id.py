import requests
import os
from dotenv import load_dotenv

# .env の読み込み
BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # 01_slack_summary_to_line
load_dotenv(os.path.join(BASE_DIR, ".env"))

token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

url = "https://api.line.me/v2/bot/followers/ids"
headers = {"Authorization": f"Bearer {token}"}

res = requests.get(url, headers=headers)
print(res.json())
