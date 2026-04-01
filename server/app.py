import json
import os

from flask import Flask, jsonify, redirect, render_template, request, url_for

import mqtt_bridge

app = Flask(__name__)

DATA_DIR = "data"
SCHEDULES_FILE = os.path.join(DATA_DIR, "schedules.json")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")
STATE_FILE = os.path.join(DATA_DIR, "state.json")


# ── Helpers ───────────────────────────────────────────────────────────────────

def load_json(path, default=None):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return default if default is not None else {}


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def load_schedules():
    return load_json(SCHEDULES_FILE, default=[])


def save_schedules(schedules):
    save_json(SCHEDULES_FILE, schedules)
    mqtt_bridge.publish_schedules(schedules)


def next_countdown(schedules):
    """Return 'hh:mm' until the next upcoming schedule, or None."""
    import time
    now = time.localtime()
    now_mins = now.tm_hour * 60 + now.tm_min
    min_delta = None
    for sched in schedules:
        t = sched.get("time", "")
        if len(t) == 5 and t[2] == ":":
            try:
                sh, sm = int(t[:2]), int(t[3:])
            except ValueError:
                continue
            sched_mins = sh * 60 + sm
            delta = (sched_mins - now_mins) % (24 * 60)
            if min_delta is None or delta < min_delta:
                min_delta = delta
    if min_delta is None:
        return None
    return f"{min_delta // 60}H {min_delta % 60:02d}M"


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    schedules = load_schedules()
    return render_template(
        "index.html",
        storage=mqtt_bridge.get_storage(),
        sensor=mqtt_bridge.get_sensor(),
        schedules=schedules,
        countdown=next_countdown(schedules),
    )


@app.route("/schedules", methods=["GET", "POST"])
def schedules():
    current = load_schedules()
    if request.method == "POST":
        t = request.form.get("time", "").strip()
        med_type = request.form.get("type", "A").strip()
        if t and len(current) < 6:
            current.append({"time": t, "type": med_type})
            current.sort(key=lambda x: x["time"])
            save_schedules(current)
        return redirect(url_for("schedules"))
    return render_template("schedules.html", schedules=current)


@app.route("/schedules/delete/<int:idx>", methods=["POST"])
def delete_schedule(idx):
    current = load_schedules()
    if 0 <= idx < len(current):
        current.pop(idx)
        save_schedules(current)
    return redirect(url_for("schedules"))


@app.route("/settings", methods=["GET", "POST"])
def settings():
    current = load_json(SETTINGS_FILE, default={})
    if request.method == "POST":
        current["telegram_uid"] = request.form.get("telegram_uid", "").strip()
        bot_token = request.form.get("bot_token", "").strip()
        if bot_token:  # only update if non-empty (avoid wiping on re-save)
            current["bot_token"] = bot_token
        current["notify_env"] = "notify_env" in request.form
        current["notify_storage"] = "notify_storage" in request.form
        try:
            current["temp_threshold"] = float(request.form.get("temp_threshold", 35.0))
            current["humi_threshold"] = float(request.form.get("humi_threshold", 80.0))
            current["alert_cooldown"] = int(request.form.get("alert_cooldown", 300))
        except ValueError:
            pass
        save_json(SETTINGS_FILE, current)
        return redirect(url_for("settings"))
    return render_template("settings.html", settings=current)


@app.route("/dispense", methods=["POST"])
def dispense():
    data = request.get_json(force=True)
    med_type = data.get("type", "A")
    mode = data.get("mode", "normal")
    action = "manual" if mode == "manual" else "dispense"
    mqtt_bridge.publish_command({"action": action, "type": med_type})
    return jsonify(ok=True)


@app.route("/api/sensor")
def api_sensor():
    return jsonify(mqtt_bridge.get_sensor())


@app.route("/api/storage")
def api_storage():
    return jsonify(mqtt_bridge.get_storage())


@app.route("/api/status")
def api_status():
    return jsonify(mqtt_bridge.get_status())


@app.route("/api/countdown")
def api_countdown():
    return jsonify({"countdown": next_countdown(load_schedules())})


# ── Startup ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    broker = sys.argv[1] if len(sys.argv) > 1 else "localhost"
    user   = sys.argv[2] if len(sys.argv) > 2 else None
    passwd = sys.argv[3] if len(sys.argv) > 3 else None
    mqtt_bridge.start(broker, broker_user=user, broker_pass=passwd)
    app.run(host="0.0.0.0", port=5000, debug=False)
