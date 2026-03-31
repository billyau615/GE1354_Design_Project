# DS3231 RTC Experiment

Validates the DS3231 real-time clock module before integrating it into the main project.

The ESP32 fetches the current time over NTP and sends it to the Micro:bit via UART. The Micro:bit writes the received time into the DS3231 over I2C, then reads it back and displays it on the OLED every second. If the ESP32 NTP signal doesn't arrive within 30 seconds, the OLED shows "No NTP signal". If the DS3231 read fails, it shows "RTC Error".

## Files

| File | Description |
|---|---|
| `microbit/main.py` | Micro:bit — waits for NTP via UART, writes DS3231, reads and displays time |
| `microbit/ds3231.py` | DS3231 I2C driver (read/write time, BCD encoding) |
| `microbit/oled.py` | SSD1306 OLED driver |
| `esp32/ds3231_ntp.ino` | ESP32 — connects to WiFi, syncs NTP, sends TIME: to Micro:bit |

## Hardware

| Component | Interface | Notes |
|---|---|---|
| Micro:bit V2 | — | Runs MicroPython |
| DS3231 RTC Module | I2C (addr `0x68`) | CR2032 battery keeps time across power loss |
| OLED SSD1306 (128×64) | I2C (addr `0x3C`) | Displays time |
| ESP32 | UART (9600 baud) | Provides NTP time to Micro:bit |

### Wiring

**I2C (Micro:bit)**

| Micro:bit Pin | Connected To |
|---|---|
| P19 (SCL) | DS3231 SCL, OLED SCL |
| P20 (SDA) | DS3231 SDA, OLED SDA |
| 3.3V | DS3231 VCC, OLED VCC |
| GND | DS3231 GND, OLED GND |

**UART (Micro:bit ↔ ESP32)**

| Micro:bit | ESP32 | Notes |
|---|---|---|
| P16 (TX) | GPIO17 (RX) | Micro:bit sends to ESP32 |
| P8 (RX) | GPIO16 (TX) | ESP32 sends to Micro:bit |
| GND | GND | Common ground required |

## Setup

### ESP32

1. Open `esp32/ds3231_ntp.ino` in Arduino IDE.
2. Fill in `WIFI_SSID` and `WIFI_PASS` at the top.
3. Adjust `GMT_OFFSET` if not UTC+8 (`8 * 3600` = Hong Kong / Singapore).
4. Flash to ESP32.

Required: no extra libraries — uses built-in `WiFi.h` and `time.h`.

### Micro:bit

Flash all three files onto the Micro:bit using a tool such as [Thonny](https://thonny.org/) or [micro:bit Python Editor](https://python.microbit.org/):

- `main.py`
- `ds3231.py`
- `oled.py`

## Boot Sequence

1. ESP32 connects to WiFi and syncs NTP.
2. Micro:bit sends `TIME_REQ` to ESP32 via UART.
3. ESP32 starts sending `TIME:HH:MM:SS` every second.
4. Micro:bit receives the time, writes it to DS3231 via I2C, and replies `TIME_ACK`.
5. ESP32 stops sending after receiving `TIME_ACK`.
6. Micro:bit reads DS3231 every second and displays `HH:MM:SS` on the OLED.

## Error States

| OLED Message | Cause |
|---|---|
| `Waiting NTP...` | Waiting for ESP32 to send time (normal during boot) |
| `No NTP signal` | No `TIME:` received within 30 seconds of `TIME_REQ` — check WiFi/UART wiring |
| `RTC Error` | DS3231 I2C read failed — check wiring and power |

## UART Protocol

| Direction | Message | Meaning |
|---|---|---|
| Micro:bit → ESP32 | `TIME_REQ` | Request current NTP time |
| ESP32 → Micro:bit | `TIME:14:30:00` | Current NTP time (sent every 1s until ACK) |
| Micro:bit → ESP32 | `TIME_ACK` | Time written to DS3231, ESP32 can stop sending |

## Notes

- The DS3231 uses a CR2032 battery for backup — once the time is set it persists across power loss.
- The DS3231 uses BCD encoding internally; the driver handles conversion automatically.
- The OLED and DS3231 share the I2C bus — both are on P19/P20.
- In the main project, this same flow runs on every boot to keep the DS3231 accurate via NTP.
