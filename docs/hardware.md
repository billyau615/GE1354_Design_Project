# Hardware & Wiring

## Component List

| Component | Qty | Interface | Connected To |
|---|---|---|---|
| Micro:bit V2 | 2 | — | — |
| DHT20 (temp/humidity sensor) | 1 | I2C (addr `0x38`) | Micro:bit #1 |
| OLED Display (SSD1306, 128x64) | 1 | I2C (addr `0x3C`) | Micro:bit #1 |
| Passive Buzzer (無源) | 2 | PWM (shared, P0) | Micro:bit #1 |
| DS3231 RTC Module | 1 | I2C (addr `0x68`) | Micro:bit #1 |
| FC-51 IR Obstacle Sensor | 1 | Digital | Micro:bit #1 |
| ESP32 | 1 | UART | Micro:bit #1 |
| JX BLS-HV7146MG Servo | 2 | PWM (500–2500µs) | Micro:bit #2 |

## Pin Mappings

### Micro:bit #1

| Pin | Connected To | Notes |
|---|---|---|
| P19 / P20 (I2C) | DHT20, OLED, DS3231 | Shared I2C bus (`0x38`, `0x3C`, `0x68`) |
| P0 | Passive Buzzer | PWM output |
| P1 | FC-51 IR Sensor OUT | Digital input (LOW = obstacle) |
| P16 (TX) | ESP32 GPIO17 (RX) | UART to ESP32 |
| P8 (RX) | ESP32 GPIO16 (TX) | UART from ESP32 |

### Micro:bit #2

| Pin | Connected To | Notes |
|---|---|---|
| P0 | Servo A (Type A dispenser) | PWM output |
| P1 | Servo B (Type B dispenser) | PWM output |

### Servo Calibration (JX BLS-HV7146MG)

Both servos (#1 and #2) share the same calibration values:

| Parameter | Value | Notes |
|---|---|---|
| `HOME_US` | 500µs | Slot 0 — home/resting position |
| `MAX_US` | 2500µs | Slot 4 — full 180° extent |
| `STEP_US` | 500µs | Per slot (4 slots total: 0→1→2→3→4) |
| `PERIOD_US` | 20000µs | 50 Hz PWM signal |
| Power supply | 6–8.4V | Must NOT use Micro:bit 3V pin |
| Signal logic | 3.3V | Micro:bit pin direct — compatible |
| Common GND | Required | Servo PSU GND and Micro:bit GND must be joined |

### ESP32

| Pin | Connected To | Notes |
|---|---|---|
| GPIO17 (RX) | Micro:bit #1 P16 (TX) | UART from Micro:bit |
| GPIO16 (TX) | Micro:bit #1 P8 (RX) | UART to Micro:bit |
| WiFi | MQTT Server | Wireless |

## I2C Device Map (Micro:bit #1)

| Address | Device | Notes |
|---|---|---|
| `0x38` | DHT20 | Temperature and humidity sensor |
| `0x3C` | SSD1306 OLED | 128×64 display |
| `0x68` | DS3231 RTC | Real-time clock with battery backup (CR2032) |

## Circuit Diagrams

*To be added — diagrams will be created as hardware integration progresses.*
