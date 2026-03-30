# Automated Drug Dispenser

> GE1354 2025-26 Design Project

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
├── microbit/              # Micro:bit Python code
│   ├── experiments/       # Small test projects for individual components
│   └── main/              # Final integrated code (coming soon)
├── esp32/                 # ESP32 Arduino (C++) code
├── server/                # Python web server + MQTT bridge
├── docs/                  # Project documentation
│   ├── architecture.md    # System architecture & communication flow
│   └── hardware.md        # Wiring, components, and circuit info
└── Design Project Instruction.pdf
```

## Documentation

- [System Architecture](docs/architecture.md)
- [Hardware & Wiring](docs/hardware.md)
- [Progress Report](docs/progress-report.md)

## Main Code

| File | Description |
|---|---|
| [microbit/main/main.py](microbit/main/main.py) | Micro:bit #1 — main dispenser logic |
| [microbit/main/mb2_main.py](microbit/main/mb2_main.py) | Micro:bit #2 — servo actuator (stub) |
| [esp32/main/main/main.ino](esp32/main/main/main.ino) | ESP32 — WiFi + NTP + MQTT + UART bridge |
| [server/app.py](server/app.py) | Web server — Flask routes |
| [server/mqtt_bridge.py](server/mqtt_bridge.py) | MQTT background thread |
| [server/telegram.py](server/telegram.py) | Telegram alert helper |

## Experiments

Small test projects to validate individual components before integration:

| Experiment | Description |
|---|---|
| [oled-dht20](microbit/experiments/oled-dht20/) | Read DHT20 temperature/humidity and display on OLED |
| [buzzer-rickroll](microbit/experiments/buzzer-rickroll/) | Play "Never Gonna Give You Up" on a passive buzzer |
| [ntp-clock](microbit/experiments/ntp-clock/) | Sync time from ESP32 NTP and display datetime on OLED, beep every minute |
| [ir-sensor](microbit/experiments/ir-sensor/) | FC-51 IR obstacle sensor on P1 triggers buzzer on P0 |
