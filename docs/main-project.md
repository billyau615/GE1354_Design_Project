# Main Project Design

> Last updated: 31 March 2026

This document covers the design decisions, protocols, and file structure for the integrated drug dispenser system.

## System Architecture

```
Micro:bit #1 ──UART──► ESP32 ──MQTT──► Broker ──MQTT──► Web Server ──HTTP──► Browser
(main logic)  ◄──UART──        ◄──MQTT──         ◄──MQTT──

Micro:bit #1 ──radio──► Micro:bit #2  (deferred — servo control)
             ◄──radio──
```

**Why radio for MB1 ↔ MB2:** MB1's UART is occupied by the ESP32 connection (P8/P16). MicroPython on Micro:bit only has one UART object and does not support software UART. The built-in 2.4GHz radio requires zero extra wiring.

---

## File Structure

```
microbit/main/
├── mb1/
│   ├── main.py     — Micro:bit #1: dispenser logic, OLED, DHT20, buzzer, radio
│   ├── oled.py     — SSD1306 driver
│   ├── dht20.py    — DHT20 driver
│   └── ds3231.py   — DS3231 RTC driver
└── mb2/
    └── main.py     — Micro:bit #2: radio listener + servo stub

esp32/main/
└── main.ino        — WiFi + NTP + MQTT + UART bridge

server/
├── app.py          — Flask web app
├── mqtt_bridge.py  — paho-mqtt background thread
├── telegram.py     — Telegram Bot API alerts
├── data/
│   ├── schedules.json  — persistent schedule list
│   ├── settings.json   — Telegram config + alert thresholds
│   └── state.json      — last-known storage counts
└── templates/
    ├── base.html
    ├── index.html      — dashboard
    ├── schedules.html
    └── settings.html
```

---

## UART Protocol

**Micro:bit #1 ↔ ESP32** at 9600 baud. Pins: MB P16 (TX) → ESP GPIO17, MB P8 (RX) ← ESP GPIO16.

All messages are newline-terminated ASCII.

| Direction | Message | Meaning |
|---|---|---|
| MB→ESP | `SENSOR:25.1,60.5` | temperature (°C), humidity (%) |
| MB→ESP | `STORAGE:7,5` | type A count, type B count |
| MB→ESP | `STORAGE:0,5:EMPTY_A` | storage update + empty flag (triggers Telegram) |
| MB→ESP | `DISPENSE_DONE:A` | confirms dispense completed |
| MB→ESP | `TIME_REQ` | MB1 requests current time from ESP32 |
| MB→ESP | `TIME_ACK` | MB1 wrote time to DS3231, ESP stops sending |
| ESP→MB | `TIME:14:30:00` | NTP time (sent every 1s after TIME_REQ, until ACK) |
| ESP→MB | `SCHED:14:30:A,15:00:B` | up to 6 comma-separated schedules |
| ESP→MB | `STORAGE_SET:7,5` | push initial storage counts to MB1 |
| ESP→MB | `DISPENSE:A/B/AB` | normal dispense from web UI (triggers buzzer + OLED alert) |
| ESP→MB | `MANUAL:A/B` | manual (silent) dispense from web UI — no buzzer or OLED alert |

---

## MQTT Topics

**ESP32 ↔ Mosquitto broker ↔ Web Server**

| Direction | Topic | Payload |
|---|---|---|
| ESP→Broker | `dispenser/sensor` | `{"temp": 25.1, "humidity": 60.5, "ip": "192.168.1.42"}` |
| ESP→Broker | `dispenser/storage` | `{"a": 7, "b": 5}` or `{"a": 0, "b": 5, "empty_a": true}` |
| ESP→Broker | `dispenser/dispense_done` | `{"type": "A"}` |
| Server→Broker | `dispenser/command` | `{"action": "dispense", "type": "A"}` or `{"action": "manual", "type": "A"}` |
| Server→Broker | `dispenser/schedules` | `[{"time":"14:30","type":"A"}, ...]` (retained) |

---

## Radio Protocol

**MB1 ↔ MB2**, `radio.config(group=42)`.

| Direction | Message |
|---|---|
| MB1→MB2 | `DISPENSE:A`, `DISPENSE:B`, `DISPENSE:AB` |
| MB1→MB2 | `SERVO_STEP` (refill mode, advance one slot) |
| MB2→MB1 | `DONE:A`, `DONE:B`, `DONE:AB` |

---

## Key Features

### Drug storage
- 2 types (A and B), 8 slots each, 1 always left empty = **7 pills max per type**
- Wheel mechanic: each dispense command turns the servo one slot (MB2, currently stubbed)

### Dispense modes
- **Normal dispense** (A, B, or A+B): plays Never Gonna Give You Up on buzzer, OLED shows "Take meds / type / current time". Waits for FC-51 IR sensor (P1) to detect hand before stopping buzzer and returning to normal display.
- **Manual dispense** (A or B only): silently sends radio command to MB2 and decrements storage — no buzzer, no OLED change, no IR wait.

### Schedules
- Up to **6 medication times** configured via web UI
- Each schedule: time (HH:MM) + type (A, B, or AB)
- MB1 calls `check_schedules()` every second (guarded by `dispensed_this_minute` flag); resets flag on minute change. This ensures a skipped DS3231 read at the start of a minute cannot cause a missed dose.
- Schedules persisted in `server/data/schedules.json`; pushed to MB1 via retained MQTT on every boot

### Data persistence across reboots
- **ESP32 NVS (`Preferences`)**: stores `storage_a` and `storage_b` — survives power loss
- On ESP32 boot: reads NVS, pushes `STORAGE_SET` to MB1, publishes to MQTT
- **Server `state.json`**: updated on every `dispenser/storage` MQTT message; used by web dashboard

### Refill mode
- **Long-press A** (≥1s) → refill Type A; **long-press B** → refill Type B
- LED matrix shows current slot count (0–7)
- Press same button to advance one slot (servo step — stubbed)
- Press other button to exit; count is saved and synced via UART
- If pills remain when entering: OLED warning — A=reset to 0, B=cancel

### Alerts (Telegram)
- **Storage empty**: sent immediately when the last pill is dispensed (storage → 0)
- **Temp/humidity threshold**: sent when sensor reading exceeds configured threshold
  - 5-minute cooldown per category to avoid flooding
- Bot token and Telegram UID configured in Settings page

### Timekeeping (MB1)
- On every boot, MB1 sends `TIME_REQ` to ESP32; ESP32 starts sending `TIME:HH:MM:SS` every second; MB1 writes the first valid time to DS3231 and replies `TIME_ACK`; ESP32 stops
- Main loop reads DS3231 every second — no software clock is maintained
- DS3231 TCXO accuracy: ±2ppm (≈5s/month), eliminating the ~1–2s/hour drift of a software counter
- DS3231 battery backup (CR2032) retains time across power loss; NTP re-sync on next boot restores accuracy

### OLED display (MB1)
All four lines use `write_oled_large` (2× scale, 16px tall). Max ~10 chars per line.

| Pages | Content | Example |
|---|---|---|
| 0–1 | Current time (12-hour) | `1:30 PM` (no leading zero) |
| 2–3 | Humidity | `H:60.5%` |
| 4–5 | Temperature | `T:25.1C` |
| 6–7 | Countdown to next dose | `Nx:1H 25M` or `No sched` |

Countdown skips `delta == 0` so it shows the next *future* schedule immediately after a dose is taken, rather than showing `0H 00M`.

During a normal dispense, the display switches to: `Take meds` / type (`A`, `B`, or `A+B`) / current time. Restores automatically when IR sensor is triggered.

---

## Config Checklist

| File | Key | Value |
|---|---|---|
| `esp32/main/main.ino` | `WIFI_SSID` / `WIFI_PASS` | Your WiFi credentials |
| `esp32/main/main.ino` | `MQTT_HOST` / `MQTT_PORT` | Mosquitto broker address |
| `esp32/main/main.ino` | `MQTT_USER` / `MQTT_PASS` | MQTT broker credentials |
| Settings page (web UI) | Bot Token | Telegram bot token from @BotFather |
| Settings page (web UI) | Telegram UID | Your Telegram user ID (from @userinfobot) |

---

## Running the Web Server

```bash
cd server
pip install flask paho-mqtt requests
python app.py <broker-host> <mqtt-user> <mqtt-pass>
# e.g. python app.py YOUR_MQTT_HOST myuser mypassword
```

Accessible at `http://0.0.0.0:5000` (all interfaces). Use screen or systemd to keep running.

## Arduino Libraries Required

Install via Arduino IDE → Library Manager:
- **PubSubClient** by Nick O'Leary
- **ArduinoJson** by Benoit Blanchon (version 6.x)
- `Preferences` is built into the ESP32 Arduino core — no install needed

---

## Known Limitations

- Servo control (MB2) pending hardware — radio link is functional; MB2 scrolls the received command on its LED matrix and sends `DONE:` back to MB1 so the full flow can be tested without servos
- No authentication on the web UI
