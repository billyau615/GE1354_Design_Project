# Servo Calibration Experiment

Calibrate exact pulse widths for each slot on both servo wheels (A and B) without reflashing. Commands are sent via MQTT and flow through ESP32 → MB1 → MB2.

## Purpose

The JX BLS-HV7146MG servos may not align perfectly with uniform 500µs steps. This experiment lets you find the correct pulse width for each of the 5 slot positions (0–4) on both wheels independently, giving 10 calibration values total.

## Wiring

Same as the main project:

| ESP32 Pin | Micro:bit Pin | Direction |
|---|---|---|
| GPIO17 (RX) | P16 (TX) | MB1 → ESP32 |
| GPIO16 (TX) | P8 (RX) | ESP32 → MB1 |

MB2 servo wiring (unchanged):

| Servo | MB2 Pin |
|---|---|
| Wheel A | P0 |
| Wheel B | P1 |

## Files

| File | Flash to |
|---|---|
| `mb1/main.py` | Micro:bit #1 |
| `mb2/main.py` | Micro:bit #2 |
| `esp32/servo_cal/servo_cal.ino` | ESP32 |

## Setup

1. Fill in WiFi and MQTT credentials in `servo_cal.ino`
2. Flash all three files
3. MB1 LED shows `1`, MB2 LED shows `C` (calibration mode) when ready

## Sending Commands

Publish to MQTT topic `dispenser/cal` with JSON payload:

```json
{"wheel": "A", "us": 1250}
```

| Field | Values | Description |
|---|---|---|
| `wheel` | `"A"` or `"B"` | Which servo to move |
| `us` | 500 – 2500 | Pulse width in microseconds |

**Example using mosquitto_pub:**
```bash
mosquitto_pub -h <broker> -u <user> -P <pass> \
  -t dispenser/cal -m '{"wheel":"A","us":1250}'
```

MB2 LED briefly shows `A` or `B` on each move, then returns to `C`.

## Calibration Procedure

For each wheel, try different `us` values until the slot aligns with the dispense hole:

| Slot | Wheel A (µs) | Wheel B (µs) |
|---|---|---|
| 0 | | |
| 1 | | |
| 2 | | |
| 3 | | |
| 4 | | |

Fill in the table above as you find each value. Once complete, update `HOME_US`, `STEP_US` in the main project (`microbit/main/mb2/main.py`) — or switch to per-slot lookup tables if the spacing is non-uniform.

## Radio Group

This experiment uses radio **group 43** (main project uses group 42) so both can run simultaneously without interference.
