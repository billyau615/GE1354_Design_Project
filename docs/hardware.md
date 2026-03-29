# Hardware & Wiring

## Component List

| Component | Qty | Interface | Connected To |
|---|---|---|---|
| Micro:bit V2 | 2 | — | — |
| DHT20 (temp/humidity sensor) | 1 | I2C (addr `0x38`) | Micro:bit #1 |
| OLED Display (SSD1306, 128x64) | 1 | I2C (addr `0x3C`) | Micro:bit #1 |
| Passive Buzzer (無源) | 1 | PWM | Micro:bit #1 |
| ESP32 | 1 | UART | Micro:bit #1 |
| Servo Motor(s) | TBD | PWM | Micro:bit #2 |

## Pin Mappings

### Micro:bit #1

| Pin | Connected To | Notes |
|---|---|---|
| I2C (pin19/pin20) | DHT20, OLED | Shared I2C bus |
| pin1 | Passive Buzzer | PWM output |
| TBD | ESP32 TX/RX | Serial communication |

### Micro:bit #2

| Pin | Connected To | Notes |
|---|---|---|
| TBD | Servo(s) | PWM output |
| TBD | Micro:bit #1 TX/RX | UART communication |

### ESP32

| Pin | Connected To | Notes |
|---|---|---|
| TBD | Micro:bit #1 TX/RX | Serial communication |
| WiFi | MQTT Server | Wireless |

## Circuit Diagrams

*To be added — diagrams will be created as hardware integration progresses.*
