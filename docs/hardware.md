# Hardware & Wiring

## Component List

| Component | Qty | Interface | Connected To |
|---|---|---|---|
| Micro:bit V2 | 2 | — | — |
| DHT20 (temp/humidity sensor) | 1 | I2C (addr `0x38`) | Micro:bit #1 |
| OLED Display (SSD1306, 128x64) | 1 | I2C (addr `0x3C`) | Micro:bit #1 |
| Passive Buzzer (無源) | 1 | PWM | Micro:bit #1 |
| FC-51 IR Obstacle Sensor | 1 | Digital | Micro:bit #1 |
| ESP32 | 1 | UART | Micro:bit #1 |
| Servo Motor(s) | TBD | PWM | Micro:bit #2 |

## Pin Mappings

### Micro:bit #1

| Pin | Connected To | Notes |
|---|---|---|
| P19 / P20 (I2C) | DHT20, OLED | Shared I2C bus |
| P0 | Passive Buzzer | PWM output |
| P1 | FC-51 IR Sensor OUT | Digital input (LOW = obstacle) |
| P16 (TX) | ESP32 GPIO17 (RX) | UART to ESP32 |
| P8 (RX) | ESP32 GPIO16 (TX) | UART from ESP32 |

### Micro:bit #2

| Pin | Connected To | Notes |
|---|---|---|
| TBD | Servo(s) | PWM output |
| TBD | Micro:bit #1 TX/RX | UART communication |

### ESP32

| Pin | Connected To | Notes |
|---|---|---|
| GPIO17 (RX) | Micro:bit #1 P16 (TX) | UART from Micro:bit |
| GPIO16 (TX) | Micro:bit #1 P8 (RX) | UART to Micro:bit |
| WiFi | MQTT Server | Wireless |

## Circuit Diagrams

*To be added — diagrams will be created as hardware integration progresses.*
