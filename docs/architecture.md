# System Architecture

## Overview

```
┌─────────────┐     serial/I2C     ┌─────────────┐     WiFi/MQTT     ┌─────────────┐
│ Micro:bit #1│ ◄──────────────► │    ESP32    │ ◄──────────────► │ MQTT Server │
│             │                    │             │                   │             │
│ - DHT20     │                    └─────────────┘                   └──────┬──────┘
│ - OLED      │                                                            │
│ - Buzzer    │                                                            │ MQTT
│             │                                                            │
└─────────────┘                                                     ┌──────┴──────┐
                                                                    │  Web Server │
┌─────────────┐                                                     │  (Python)   │
│ Micro:bit #2│                                                     │             │
│             │                                                     └──────┬──────┘
│ - Servos    │                                                            │
│  (dispenser)│                                                            │ HTTP
└─────────────┘                                                            │
                                                                    ┌──────┴──────┐
                                                                    │   Browser   │
                                                                    │   (Web UI)  │
                                                                    └─────────────┘
```

## Components

### Micro:bit #1 — Sensors & Display
- Reads temperature and humidity from **DHT20** sensor (I2C)
- Displays status on **OLED** screen (I2C)
- Drives **passive buzzer** for alerts/notifications
- Communicates with ESP32 for network connectivity

### Micro:bit #2 — Dispensing Mechanism
- Controls **servo motors** to dispense medication
- Operates on a separate circuit
- Communication method with Micro:bit #1: TBD (wireless radio / via ESP32)

### ESP32 — Network Bridge
- Connects to WiFi
- Publishes sensor data and receives commands via **MQTT**
- Bridges Micro:bit #1 to the network

### Web Server (Python)
- Hosts the management web UI
- Subscribes to MQTT topics for live data
- Publishes MQTT commands (e.g., trigger dispensing)
- Reverse-proxied in deployment

### MQTT Server
- External broker (already available)
- Central message bus between ESP32 and web server
- Topic structure: TBD

## Communication Flow

1. **Sensor data flow**: DHT20 → Micro:bit #1 → ESP32 → MQTT → Web Server → Browser
2. **Dispense command**: Browser → Web Server → MQTT → ESP32 → Micro:bit → Servo
3. **Alerts**: Micro:bit #1 → Buzzer / OLED (local), and ESP32 → MQTT → Web Server (remote)
