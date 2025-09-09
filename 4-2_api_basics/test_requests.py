import requests

r = requests.get("https://httpbin.org/get", timeout=10)
print(r.status_code)
print(r.json())
