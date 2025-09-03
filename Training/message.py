import datetime

# 今日の日付を取得
today = datetime.date.today()

# 曜日を日本語に変換
weekdays = ["月", "火", "水", "木", "金", "土", "日"]
weekday = weekdays[today.weekday()]

print("おはようございます🌸")
print("今日は", today, f"({weekday}曜日) です！")
print("Python初挑戦、がんばろう💪")
