import json
import requests

SETTINGS_FILE = "data/settings.json"


def send_alert(message: str):
    try:
        with open(SETTINGS_FILE) as f:
            settings = json.load(f)
    except Exception:
        return

    bot_token = settings.get("bot_token", "").strip()
    telegram_uid = settings.get("telegram_uid", "").strip()

    if not bot_token or not telegram_uid:
        return

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    try:
        requests.post(url, json={"chat_id": telegram_uid, "text": message}, timeout=5)
    except requests.exceptions.RequestException as e:
        print(f"[telegram] alert failed: {e}")
