import requests
import sys

token = "8868627993:AAHynpw6p-1Ozrsn_caBonDo1yQiE-VFMt8"
url = f"https://api.telegram.org/bot{token}/deleteWebhook"

print(f"Deleting webhook for bot...")
try:
    response = requests.get(url, params={"drop_pending_updates": True}, timeout=10)
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")
