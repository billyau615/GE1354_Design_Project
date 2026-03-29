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

## Up Next
- Micro:bit #2 servo motor control
- ESP32 MQTT integration
- Python web server and management UI
- Full system integration
