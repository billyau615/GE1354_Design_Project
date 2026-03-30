# Progress Report

## 29 March 2026

### Repository Setup
- Defined system architecture: 2 Micro:bits, ESP32 (MQTT bridge only), Python web server, external MQTT broker
- All inter-device communication via UART; ESP32 handles WiFi/MQTT only
- Documented hardware wiring and pin mappings

### Experiments Completed

| Experiment | Notes |
|---|---|
| DHT20 + OLED display | Reads temperature/humidity, displays on SSD1306 OLED (I2C) |
| Passive buzzer | PWM playback on P0, tested with music sequence |
| NTP clock via ESP32 | ESP32 fetches NTP time (UTC+8), sends to Micro:bit via UART once; Micro:bit runs clock independently and beeps at every minute |

### Hardware Validated
- DHT20 sensor (I2C 0x38)
- SSD1306 OLED 128x64 (I2C 0x3C)
- Passive buzzer (P0, PWM)
- ESP32 ↔ Micro:bit UART (ESP32 GPIO16/17 ↔ Micro:bit P8/P16)

---

## 30 March 2026

### New Experiments
- FC-51 IR obstacle sensor on P1 triggers buzzer on P0
- DS3231 RTC: ESP32 fetches NTP, sends to Micro:bit via UART, written to DS3231; time read from DS3231 and displayed on OLED every second; "No NTP signal" / "RTC Error" on failure

### Hardware Validated
- DS3231 RTC module (I2C 0x68, battery backup CR2032)

### Main Project — Complete

Full integrated system built across all components:

**Micro:bit #1** (`microbit/main/mb1/main.py`)
- On every boot, syncs time from ESP32 NTP and writes it to the DS3231 RTC
- Clock reads DS3231 every second — no software clock; DS3231 TCXO eliminates drift
- Reads DHT20 every 30s; displays live on OLED (time / humidity+temp / next schedule countdown)
- Checks up to 6 medication schedules per minute; triggers alarm and dispense on match
- Long-press A/B to enter refill mode; LED matrix shows slot count; press to advance
- Storage counts initialised from ESP32 NVS on boot; synced back on every change

**ESP32** (`esp32/main/main.ino`)
- WiFi + NTP; sends `TIME:` to MB1 every second until acknowledged
- Persistent storage counts in NVS (Preferences library); restored after power loss
- MQTT bridge: relays sensor/storage/dispense data MB1 → broker, and commands broker → MB1
- Subscribes to retained `dispenser/schedules`; reformats and pushes to MB1 on connect

**Web Server** (`server/`)
- Flask app on `127.0.0.1:5000`, reverse-proxy ready
- Dashboard: storage (A/B) and environment sensor both auto-refresh every 5s; connection-lost modal on repeated failures
- Schedule management: add/delete up to 6 schedules; pushed to MQTT (retained)
- Settings: Telegram bot token, UID, temp/humidity alert thresholds
- Telegram alerts: storage empty (immediately), threshold exceeded (5-min cooldown)

### Design Decisions
- MB1 ↔ MB2 uses **radio** (built-in 2.4GHz, group 42) — UART already occupied by ESP32
- Servo control (MB2) is **stubbed** pending servo hardware
- Software clock dropped in favour of DS3231 — eliminates drift, survives power loss
- All protocols documented in [docs/main-project.md](main-project.md)

## Up Next
- Micro:bit #2 servo motor control (hardware pending)
- Integration testing: boot sequence, schedule trigger, refill, Telegram alerts
