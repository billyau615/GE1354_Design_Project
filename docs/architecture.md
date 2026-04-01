# System Architecture

## Overview

```
┌──────────────────┐        UART        ┌─────────────┐     WiFi/MQTT     ┌─────────────┐
│  Micro:bit #1    │ ◄────────────────► │    ESP32    │ ◄──────────────► │ MQTT Server │
│                  │                    │             │                   │             │
│ - DHT20          │                    └─────────────┘                   └──────┬──────┘
│ - OLED           │  (main logic here)   (bridge only)                         │
│ - Passive Buzzer │                                                             │ MQTT
│ - DS3231 RTC     │       Radio                                                 │
│ - FC-51 IR sensor│ ◄────────────────► ┌─────────────┐       ┌────────────────┴────────┐
│                  │                    │ Micro:bit #2│       │    Web Server           │
└──────────────────┘                    │             │       │    (Python/Flask)       │
                                        │ - Servo A   │       └────────────┬────────────┘
                                        │ - Servo B   │                    │ HTTP
                                        └─────────────┘             ┌──────┴──────┐
                                                                     │   Browser   │
                                                                     │   (Web UI)  │
                                                                     └─────────────┘
```

## Components

### Micro:bit #1 — Main Controller
- Runs the **main application logic**
- Reads temperature and humidity from **DHT20** sensor (I2C 0x38)
- Displays time, sensor readings, and next-dose countdown on **OLED** (I2C 0x3C)
- Drives **passive buzzer** (P0, PWM) — plays alarm on scheduled dispense
- Keeps time via **DS3231 RTC** (I2C 0x68); synced from ESP32 NTP on every boot; battery-backed
- Detects hand under dispenser using **FC-51 IR obstacle sensor** (P1, digital); stops alarm when hand detected
- Sends/receives data to/from **ESP32** via UART (P8/P16, 9600 baud)
- Sends commands to **Micro:bit #2** via radio (built-in 2.4GHz, group 42)

### Micro:bit #2 — Dispensing Mechanism
- Controls **two servo motors** (JX BLS-HV7146MG, 180°) to dispense medication
  - Servo A (Type A dispenser) on P0; Servo B (Type B dispenser) on P1
  - HOME=500µs, STEP=500µs, 4 slots per wheel (4 pills max per type)
- Restores servo positions from storage counts on boot (via `INIT:a,b` radio message from MB1)
- Communicates with Micro:bit #1 via **radio** (built-in 2.4GHz, group 42)
- Radio commands: `INIT:a,b`, `DISPENSE:A/B/AB`, `REFILL:A/B`, `SERVO_STEP:A/B`

### ESP32 — MQTT Bridge
- Connects to WiFi; syncs NTP time (UTC+8) and forwards to MB1 on boot
- Forwards data between Micro:bit #1 and the MQTT server via **UART ↔ MQTT**
- Persists storage counts in NVS flash (survives power loss); sends to MB1 on connect
- Publishes a heartbeat ping every 5s (`dispenser/ping`) for online detection
- Contains no application logic — purely a network and persistence bridge

### Web Server (Python/Flask)
- Hosts the management web UI (dashboard, schedules, settings)
- Bridges MQTT: subscribes to device topics, publishes commands
- Sends **Telegram alerts** for empty storage and sensor threshold violations
- Persists last-known storage counts in `state.json`

### MQTT Server
- External broker
- Central message bus between ESP32 and web server

| Topic | Direction | Content |
|---|---|---|
| `dispenser/ping` | ESP32 → Server | Heartbeat every 5s (online detection) |
| `dispenser/sensor` | ESP32 → Server | `{"temp": 25.1, "humidity": 60.5, "ip": "..."}` |
| `dispenser/storage` | ESP32 → Server | `{"a": 4, "b": 3}` (with optional `empty_a/b` flags) |
| `dispenser/dispense_done` | ESP32 → Server | `{"type": "A"}` |
| `dispenser/command` | Server → ESP32 | `{"action": "dispense"/"manual", "type": "A"}` |
| `dispenser/schedules` | Server → ESP32 | `[{"time": "14:30", "type": "A"}, ...]` (retained) |

## Communication Flows

1. **Sensor data**: DHT20 → MB1 → UART → ESP32 → MQTT → Web Server → Browser
2. **Dispense (scheduled)**: DS3231 time match → MB1 → Radio → MB2 → Servo; MB1 buzzer on + waits for IR sensor hand detection → buzzer off
3. **Dispense (web)**: Browser → Web Server → MQTT → ESP32 → UART → MB1 → Radio → MB2 → Servo
4. **Refill**: MB1 button long-press → `REFILL:X` radio → MB2 servo resets to HOME; each MB1 button press → `SERVO_STEP:X` radio → MB2 advances one slot; user drops pill through dispense hole
5. **Alerts**: MB1 → UART → ESP32 → MQTT → Web Server → Telegram
6. **Boot sync**: ESP32 NTP → UART `TIME:` → MB1 → DS3231; ESP32 NVS → UART `STORAGE_SET:` → MB1 → Radio `INIT:a,b` → MB2 servo position restored
