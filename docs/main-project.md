# Main Project Design

> Last updated: 30 March 2026

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
| MB→ESP | `TIME_ACK` | MB1 received time, ESP stops sending |
| ESP→MB | `TIME:14:30:00` | NTP time sync (sent every 1s until ACK) |
| ESP→MB | `SCHED:14:30:A,15:00:B` | up to 6 comma-separated schedules |
| ESP→MB | `STORAGE_SET:7,5` | push initial storage counts to MB1 |
| ESP→MB | `DISPENSE:A` | manual dispense command from web UI |

---

## MQTT Topics

**ESP32 ↔ Mosquitto broker ↔ Web Server**

| Direction | Topic | Payload |
|---|---|---|
| ESP→Broker | `dispenser/sensor` | `{"temp": 25.1, "humidity": 60.5}` |
| ESP→Broker | `dispenser/storage` | `{"a": 7, "b": 5}` or `{"a": 0, "b": 5, "empty_a": true}` |
| ESP→Broker | `dispenser/dispense_done` | `{"type": "A"}` |
| Server→Broker | `dispenser/command` | `{"action": "dispense", "type": "A"}` |
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

### Schedules
- Up to **6 medication times** configured via web UI
- Each schedule: time (HH:MM) + type (A, B, or AB)
- MB1 checks schedules on every minute tick; fires alarm + dispense on match
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
- On every boot, MB1 waits for ESP32 to send `TIME:HH:MM:SS` (NTP-sourced), writes it to the DS3231 RTC over I2C, then replies `TIME_ACK`
- Main loop reads DS3231 every second — no software clock is maintained
- DS3231 TCXO accuracy: ±2ppm (≈5s/month), eliminating the ~1–2s/hour drift of a software counter
- DS3231 battery backup (CR2032) retains time across power loss; NTP re-sync on next boot restores accuracy

### OLED display (MB1)
- Line 0: `HH:MM:SS` (read from DS3231 every second)
- Line 1: `H:60.5% T:25.1C`
- Line 2: `Next:02:15` (countdown to next schedule, or `No sched`)

---

## Config Checklist

| File | Key | Value |
|---|---|---|
| `esp32/main/main.ino` | `WIFI_SSID` / `WIFI_PASS` | Your WiFi credentials |
| `esp32/main/main.ino` | `MQTT_HOST` / `MQTT_PORT` | Mosquitto broker address |
| Settings page (web UI) | Bot Token | Telegram bot token from @BotFather |
| Settings page (web UI) | Telegram UID | Your Telegram user ID (from @userinfobot) |

---

## Running the Web Server

```bash
cd server
pip install flask paho-mqtt requests
python app.py <mqtt-broker-ip>
# e.g. python app.py 192.168.1.100
```

Accessible at `http://127.0.0.1:5000`. Reverse-proxy with nginx if external access is needed.

## Arduino Libraries Required

Install via Arduino IDE → Library Manager:
- **PubSubClient** by Nick O'Leary
- **ArduinoJson** by Benoit Blanchon (version 6.x)
- `Preferences` is built into the ESP32 Arduino core — no install needed

---

## Known Limitations

- Servo control (MB2) is stubbed — dispense command is sent via radio but no physical movement yet
- No authentication on the web UI
