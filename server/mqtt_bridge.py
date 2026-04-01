import json
import threading
import time

import paho.mqtt.client as mqtt

from telegram import send_alert

# ── Shared state ──────────────────────────────────────────────────────────────
_lock = threading.Lock()
_sensor = {"temp": None, "humidity": None, "updated": None, "updated_ts": 0, "ip": None}
_storage = {"a": 7, "b": 7, "updated": None}

# Rate-limit timestamps for threshold alerts (per category)
_last_temp_alert = 0
_last_humi_alert = 0

SETTINGS_FILE = "data/settings.json"
STATE_FILE = "data/state.json"

_client = None


# ── Public API ────────────────────────────────────────────────────────────────

def get_sensor():
    with _lock:
        return dict(_sensor)


def get_storage():
    with _lock:
        return dict(_storage)


def get_status():
    with _lock:
        ts = _sensor["updated_ts"]
        online = (time.time() - ts) < 90 if ts else False
        return {"online": online, "ip": _sensor["ip"], "last_seen": _sensor["updated"]}


def publish_command(payload: dict):
    if _client:
        _client.publish("dispenser/command", json.dumps(payload))


def publish_schedules(schedules: list):
    if _client:
        _client.publish("dispenser/schedules", json.dumps(schedules), retain=True)


# ── Internal helpers ──────────────────────────────────────────────────────────

def _load_settings():
    try:
        with open(SETTINGS_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


def _save_state():
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(_storage, f)
    except Exception as e:
        print(f"[mqtt] failed to save state: {e}")


# ── MQTT callbacks ─────────────────────────────────────────────────────────────

def _on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("[mqtt] connected to broker")
        client.subscribe("dispenser/sensor")
        client.subscribe("dispenser/storage")
        client.subscribe("dispenser/dispense_done")
    else:
        print(f"[mqtt] connect failed, rc={rc}")


def _on_message(client, userdata, msg):
    global _last_temp_alert, _last_humi_alert

    topic = msg.topic
    try:
        payload = json.loads(msg.payload.decode())
    except Exception:
        return

    if topic == "dispenser/sensor":
        now = time.strftime("%H:%M:%S")
        with _lock:
            _sensor["temp"] = payload.get("temp")
            _sensor["humidity"] = payload.get("humidity")
            _sensor["updated"] = now
            _sensor["updated_ts"] = time.time()
            if payload.get("ip"):
                _sensor["ip"] = payload.get("ip")

        settings = _load_settings()
        if settings.get("notify_env", True):
            temp_thresh = settings.get("temp_threshold", 35.0)
            humi_thresh = settings.get("humi_threshold", 80.0)
            cooldown = settings.get("alert_cooldown", 300)

            if payload.get("temp") is not None and payload["temp"] > temp_thresh:
                if time.time() - _last_temp_alert > cooldown:
                    _last_temp_alert = time.time()
                    send_alert(f"[Dispenser] Temperature too high: {payload['temp']}C (threshold: {temp_thresh}C)")

            if payload.get("humidity") is not None and payload["humidity"] > humi_thresh:
                if time.time() - _last_humi_alert > cooldown:
                    _last_humi_alert = time.time()
                    send_alert(f"[Dispenser] Humidity too high: {payload['humidity']}% (threshold: {humi_thresh}%)")

    elif topic == "dispenser/storage":
        with _lock:
            if "a" in payload:
                _storage["a"] = payload["a"]
            if "b" in payload:
                _storage["b"] = payload["b"]
            _storage["updated"] = time.strftime("%d/%m %H:%M")
            _save_state()

        settings = _load_settings()
        if settings.get("notify_storage", True):
            if payload.get("empty_a"):
                send_alert("[Dispenser] Drug A is now empty. Please refill.")
            if payload.get("empty_b"):
                send_alert("[Dispenser] Drug B is now empty. Please refill.")

    elif topic == "dispenser/dispense_done":
        print(f"[mqtt] dispense done: type={payload.get('type')}")


# ── Startup ───────────────────────────────────────────────────────────────────

def start(broker_host: str, broker_port: int = 1883,
          broker_user: str = None, broker_pass: str = None):
    global _client

    # Load persisted storage state on startup
    try:
        with open(STATE_FILE) as f:
            saved = json.load(f)
            with _lock:
                _storage["a"] = saved.get("a", 7)
                _storage["b"] = saved.get("b", 7)
    except Exception:
        pass

    _client = mqtt.Client(client_id="dispenser-server")
    _client.on_connect = _on_connect
    _client.on_message = _on_message
    if broker_user:
        _client.username_pw_set(broker_user, broker_pass)
    _client.connect(broker_host, broker_port)

    t = threading.Thread(target=_client.loop_forever, daemon=True)
    t.start()
    print(f"[mqtt] connecting to {broker_host}:{broker_port}")
