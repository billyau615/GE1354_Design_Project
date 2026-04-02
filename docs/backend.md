# Python Backend — Component Documentation

> Last updated: 2 April 2026 (UTC+8)

The backend is a Python application running on the server. It consists of three modules:

| File | Role |
|---|---|
| `server/app.py` | Flask web application — HTTP routes, template rendering, schedule persistence |
| `server/mqtt_bridge.py` | MQTT client — background thread, shared state, Telegram trigger |
| `server/telegram.py` | Telegram Bot API — sends alert messages to the user |

---

## Running the Server

```bash
cd server
python app.py <broker-host> <mqtt-user> <mqtt-pass>
# e.g. python app.py YOUR_MQTT_HOST YOUR_MQTT_USER secret123
```

Flask starts on `0.0.0.0:5000` (all interfaces). Use `screen` or `systemd` to keep it running after SSH logout.

**Dependencies:**
```bash
pip install flask paho-mqtt requests
```

---

## Data Files

Stored in `server/data/`. Created manually or auto-generated on first write.

| File | Format | Purpose |
|---|---|---|
| `schedules.json` | JSON array | Medication schedules. Example: `[{"time": "14:30", "type": "A"}]` |
| `settings.json` | JSON object | Telegram credentials and alert thresholds |
| `state.json` | JSON object | Last-known storage counts. Example: `{"a": 3, "b": 4}` |

`state.json` is written by `mqtt_bridge.py` whenever a `dispenser/storage` MQTT message is received. It is loaded on server startup so the dashboard shows the correct counts even before the first MQTT message arrives.

---

## `app.py` — Flask Web Application

### Startup

When run directly (`__main__`), it reads up to three CLI arguments (broker host, MQTT user, MQTT password), passes them to `mqtt_bridge.start()`, then starts Flask on `0.0.0.0:5000` with `debug=False`.

`mqtt_bridge.start()` is called **before** `app.run()`, ensuring the MQTT connection is established and `state.json` is loaded before the first HTTP request arrives.

### Routes

#### `GET /`

Renders the dashboard (`index.html`). Passes three template variables:

| Variable | Source | Description |
|---|---|---|
| `sensor` | `mqtt_bridge.get_sensor()` | Dict with `temp`, `humidity`, `updated` keys |
| `schedules` | `load_schedules()` | List from `schedules.json` |
| `countdown` | `next_countdown(schedules)` | String like `"1H 25M"` or `None` |

Storage is intentionally excluded — the page always starts with a `- / 4` placeholder and JavaScript immediately populates the real value on first poll, avoiding a stale flash from `state.json`.

#### `GET /api/storage`

Returns current storage counts and last update time: `{"a": 5, "b": 7, "updated": "01/04 14:32"}`.

`updated` is `null` if no storage MQTT message has been received since server start (i.e. the value came from `state.json`). Polled every **5 seconds** by the dashboard.

#### `GET /api/status`

Returns device online status: `{"online": true, "ip": "192.168.1.42"}`.

`online` is `true` if a `dispenser/ping` MQTT message was received within the last **15 seconds**. `ip` is `null` until the first sensor message arrives. Polled every **5 seconds** by the dashboard.

#### `GET /api/sensor`

Returns latest sensor data as JSON: `{"temp": 28.3, "humidity": 62.5, "updated": "Apr 01, 2026 14:32"}`.

The `updated` field is a server-side timestamp (`"Mmm DD, YYYY HH:MM"`) set at the moment the MQTT message was received. If no sensor data has been received since startup, all values are `null` and `updated` is `null`. Polled every **5 seconds** by the dashboard.

#### `GET /api/countdown`

Returns time until the next upcoming schedule: `{"countdown": "1H 25M"}` or `{"countdown": null}` if no schedules are configured.

Computed server-side using `next_countdown()` with the current system time. Polled every **5 seconds** by the dashboard.

#### `GET /POST /schedules`

- **GET**: Renders `schedules.html` with the current schedule list
- **POST**: Validates the submitted time and type, enforces a per-type limit of 4 (Type A and B counted independently; AB counts toward both), appends if within limits, sorts by time, saves to `schedules.json`, and publishes the full list to the MQTT broker via `mqtt_bridge.publish_schedules()`. Redirects to GET after processing.

#### `POST /schedules/delete/<int:idx>`

Removes the schedule at the given index (0-based), saves, and publishes the updated list. Redirects to `/schedules`.

#### `GET/POST /settings`

- **GET**: Renders `settings.html` with current values from `settings.json`
- **POST**: Updates `telegram_uid`, `temp_threshold`, and `humi_threshold`. Only updates `bot_token` if the submitted value is non-empty (prevents accidentally clearing the token on re-save). Saves to `settings.json`. Redirects to GET.

#### `POST /dispense`

Accepts a JSON body: `{"type": "A", "mode": "normal"}`.

- `mode = "normal"` → publishes `{"action": "dispense", "type": "A"}` to `dispenser/command`
- `mode = "manual"` → publishes `{"action": "manual", "type": "A"}` to `dispenser/command`

Returns `{"ok": true}`.

### `next_countdown()` helper

Reads the server's local time, computes the delta in minutes between now and each schedule's time using `(sched_mins - now_mins) % (24 * 60)`, and returns the minimum as `"XH XXM"` (e.g. `"1H 25M"`). Returns `None` if no schedules exist.

This function does not skip `delta == 0` (unlike MB1) because on the server side a delta of 0 means the schedule is firing right now — still valid to show on the countdown badge.

---

## `mqtt_bridge.py` — MQTT Bridge

Runs as a **background daemon thread** using `paho-mqtt`'s `loop_forever()`. All shared state is protected by a `threading.Lock` so Flask route handlers and the MQTT thread can read/write safely.

### Shared State

```python
_sensor  = {"temp": None, "humidity": None, "updated": None, "ip": None}
_storage = {"a": 4, "b": 4}
_ping_ts = 0.0
```

- `_sensor["updated"]` is a `"Mmm DD, YYYY HH:MM"` string (e.g. `"Apr 01, 2026 14:32"`) set whenever a sensor MQTT message is received
- `_sensor["ip"]` is populated from the `ip` field in the MQTT sensor payload
- `_ping_ts` is a Unix timestamp updated on each `dispenser/ping` message; used to compute online status

These are accessed by Flask routes via `get_sensor()`, `get_storage()`, and `get_status()`, which return shallow copies under the lock.

### Startup (`start()`)

1. Loads `state.json` and pre-populates `_storage` with persisted counts (keys `"a"` and `"b"`)
2. Creates a `paho.mqtt.Client` with client ID `"dispenser-server"`
3. Sets username/password if provided
4. Connects to the broker and starts `loop_forever()` in a daemon thread

### Subscribed Topics

| Topic | Handler behaviour |
|---|---|
| `dispenser/ping` | Updates `_ping_ts`. If the device was previously offline (last ping > 15s ago), immediately publishes `{"action": "set_storage", "a": a, "b": b}` to `dispenser/command` to push authoritative storage counts from `state.json` to MB1 — correcting any stale NVS value on the ESP32. |
| `dispenser/sensor` | Updates `_sensor` with temp, humidity, IP address, and `"Mmm DD, YYYY HH:MM"` timestamp. Checks values against thresholds. Sends Telegram alert if threshold exceeded and cooldown has elapsed. |
| `dispenser/storage` | Updates `_storage["a"]` and `_storage["b"]`. Writes to `state.json`. Sends Telegram alert if `empty_a` or `empty_b` flag is present. |
| `dispenser/dispense_done` | Prints to console (no further action currently). |

### Telegram Alert Cooldown & Toggles

Each alert type can be independently enabled or disabled via the Settings page:

| Setting | Key in settings.json | Default |
|---|---|---|
| Environment alerts | `notify_env` | `true` |
| Storage alerts | `notify_storage` | `true` |
| Cooldown (seconds) | `alert_cooldown` | `300` |

Environment alerts (temp/humidity) are rate-limited: a new alert fires only if at least `alert_cooldown` seconds have elapsed since the last alert **in that category** (`_last_temp_alert` and `_last_humi_alert` are tracked separately).

Storage-empty alerts **ignore the cooldown entirely** — they fire exactly once per empty event because the `EMPTY_X` flag is only sent by MB1 at the moment storage transitions to 0.

### Published Topics

| Function | Topic | Payload | `retain` |
|---|---|---|---|
| `publish_command(payload)` | `dispenser/command` | JSON object | No |
| `publish_schedules(schedules)` | `dispenser/schedules` | JSON array | **Yes** |

The `dispenser/schedules` topic is published with `retain=True`. This means the broker stores the last message and delivers it immediately to any client (including the ESP32) that subscribes — even if the ESP32 connects after the server last published. This ensures MB1 always receives the current schedule list on boot without requiring the server to republish.

---

## `telegram.py` — Alert Sender

A single function `send_alert(message)`.

1. Reads `bot_token` and `telegram_uid` from `data/settings.json`
2. If either is empty or missing, returns silently (no error)
3. POSTs to `https://api.telegram.org/bot{token}/sendMessage` with a 5-second timeout
4. On network error, prints to console and returns — never raises

This silent-fail design means a misconfigured or unreachable Telegram bot never disrupts the main MQTT processing loop.

### Multiple Recipients

`telegram_uid` in `settings.json` can hold a comma-separated list of user IDs (e.g. `"123456789,987654321"`). `send_alert()` splits on commas and sends to each ID independently. A delivery failure to one recipient does not prevent sending to the others.

### Alert Messages

| Event | Message |
|---|---|
| Storage A empty | `[Dispenser] Drug A is now empty. Please refill.` |
| Storage B empty | `[Dispenser] Drug B is now empty. Please refill.` |
| Temperature exceeded | `[Dispenser] Temperature too high: 36.2C (threshold: 35.0C)` |
| Humidity exceeded | `[Dispenser] Humidity too high: 83.0% (threshold: 80.0%)` |

---

## Data Flow Summary

```
MB1 ──UART──► ESP32 ──MQTT──► broker ──MQTT──► mqtt_bridge.py
                                                    │
                                          updates _sensor / _storage
                                          writes state.json
                                          triggers telegram.py
                                                    │
                                               app.py ──HTTP──► Browser
                                          (reads _sensor, _storage)

Browser ──POST /dispense──► app.py ──publish_command()──► broker ──MQTT──► ESP32 ──UART──► MB1
Browser ──POST /schedules──► app.py ──publish_schedules()──► broker (retained) ──MQTT──► ESP32 ──UART──► MB1
```
