# Automated Drug Dispenser

An automated drug dispensing system built with Micro:bit, ESP32, and a web-based management interface. The system monitors environmental conditions, controls servo-driven dispensing mechanisms, and communicates via MQTT.

## System Overview

| Component | Role |
|---|---|
| **Micro:bit #1** | Connects to OLED display, passive buzzer, DHT20 sensor, and ESP32 |
| **Micro:bit #2** | Separate circuit for controlling servo motors |
| **ESP32** | WiFi connectivity and MQTT communication |
| **Web Server** | Python backend serving the management UI, bridging MQTT |
| **MQTT Server** | Message broker between ESP32 and web server |

## Repository Structure

```
├── experiments/           # Standalone test projects for individual components
│   ├── oled-dht20/
│   ├── buzzer-rickroll/
│   ├── ir-sensor/
│   └── ntp-clock/
│       ├── microbit/
│       └── esp32/
├── microbit/main/         # Micro:bit integrated code
│   ├── mb1/               # Micro:bit #1 (main logic)
│   └── mb2/               # Micro:bit #2 (servo, stub)
├── esp32/main/            # ESP32 Arduino firmware
├── server/                # Python web server + MQTT bridge
└── docs/                  # Project documentation
```

## Documentation

- [System Architecture](docs/architecture.md)
- [Hardware & Wiring](docs/hardware.md)
- [Main Project Design](docs/main-project.md) — protocols, features, config checklist
- [Progress Report](docs/progress-report.md)

## Main Code

| File | Description |
|---|---|
| [microbit/main/mb1/main.py](microbit/main/mb1/main.py) | Micro:bit #1 — main dispenser logic |
| [microbit/main/mb2/main.py](microbit/main/mb2/main.py) | Micro:bit #2 — servo actuator (stub) |
| [esp32/main/main.ino](esp32/main/main.ino) | ESP32 — WiFi + NTP + MQTT + UART bridge |
| [server/app.py](server/app.py) | Web server — Flask routes |
| [server/mqtt_bridge.py](server/mqtt_bridge.py) | MQTT background thread |
| [server/telegram.py](server/telegram.py) | Telegram alert helper |

## Experiments

Small test projects to validate individual components before integration:

| Experiment | Description |
|---|---|
| [oled-dht20](experiments/oled-dht20/) | Read DHT20 temperature/humidity and display on OLED |
| [buzzer-rickroll](experiments/buzzer-rickroll/) | Play "Never Gonna Give You Up" on a passive buzzer |
| [ntp-clock](experiments/ntp-clock/) | Sync time from ESP32 NTP and display datetime on OLED, beep every minute |
| [ir-sensor](experiments/ir-sensor/) | FC-51 IR obstacle sensor on P1 triggers buzzer on P0 |

## Web UI Preview

Static HTML mock-ups of the web interface — open directly in a browser, no server required.

| Page | File |
|---|---|
| Dashboard | [preview/dashboard.html](preview/dashboard.html) |
| Schedules | [preview/schedules.html](preview/schedules.html) |
| Settings | [preview/settings.html](preview/settings.html) |
