# System Architecture

## Overview

```
┌─────────────┐        UART        ┌─────────────┐     WiFi/MQTT     ┌─────────────┐
│ Micro:bit #1│ ◄────────────────► │    ESP32    │ ◄──────────────► │ MQTT Server │
│             │                    │             │                   │             │
│ - DHT20     │                    └─────────────┘                   └──────┬──────┘
│ - OLED      │  (main logic here)   (MQTT only)                           │
│ - Buzzer    │                                                             │ MQTT
│             │        UART                                                 │
│             │ ◄────────────────► Micro:bit #2               ┌────────────┴────────┐
└─────────────┘                    │                           │    Web Server       │
                                   │ - Servos                 │    (Python)         │
                                   │  (dispenser)             └────────────┬────────┘
                                   └─────────────┘                        │ HTTP
                                                                    ┌──────┴──────┐
                                                                    │   Browser   │
                                                                    │   (Web UI)  │
                                                                    └─────────────┘
```

## Components

### Micro:bit #1 — Main Controller
- Runs the **main application logic**
- Reads temperature and humidity from **DHT20** sensor (I2C)
- Displays status on **OLED** screen (I2C)
- Drives **passive buzzer** for alerts/notifications
- Sends/receives data to/from **ESP32** via UART
- Sends/receives commands to/from **Micro:bit #2** via UART

### Micro:bit #2 — Dispensing Mechanism
- Controls **servo motors** to dispense medication
- Communicates with Micro:bit #1 via **UART**

### ESP32 — MQTT Bridge only
- Connects to WiFi
- Forwards data between Micro:bit #1 and the MQTT server via **UART ↔ MQTT**
- Contains no application logic — purely a network bridge

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

1. **Sensor data flow**: DHT20 → Micro:bit #1 → UART → ESP32 → MQTT → Web Server → Browser
2. **Dispense command**: Browser → Web Server → MQTT → ESP32 → UART → Micro:bit #1 → UART → Micro:bit #2 → Servo
3. **Alerts**: Micro:bit #1 → Buzzer / OLED (local), and → ESP32 → MQTT → Web Server (remote)
