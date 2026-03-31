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
    if not bot_token:
        return

    uids = [uid.strip() for uid in settings.get("telegram_uid", "").split(",") if uid.strip()]
    if not uids:
        return

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    for uid in uids:
        try:
            requests.post(url, json={"chat_id": uid, "text": message}, timeout=5)
        except requests.exceptions.RequestException as e:
            print(f"[telegram] alert failed for {uid}: {e}")
