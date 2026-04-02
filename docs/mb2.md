# Micro:bit #2 — Component Documentation

> Last updated: 2 April 2026 (UTC+8)

Micro:bit #2 is the actuation node of the drug dispenser. It listens for radio commands from MB1 and drives two servo motors to dispense or load pills. It has no UART, no sensors, and no display logic beyond a status indicator.

---

## Hardware Connections

| Component | Interface | Pin(s) | Notes |
|---|---|---|---|
| Servo A (Type A dispenser) | PWM | P0 | 500–2500µs, 50 Hz, 6–8.4V external supply |
| Servo B (Type B dispenser) | PWM | P1 | 500–2500µs, 50 Hz, same supply as Servo A |
| Micro:bit #1 (radio) | 2.4 GHz radio | Built-in | `group=42` |

> **Power:** Servos must be powered from a 6–8.4V external supply, **not** the Micro:bit 3.3V pin. Signal logic is 3.3V (Micro:bit pin direct — compatible). The servo PSU GND and Micro:bit GND must be joined (common ground).

---

## Source Files

| File | Purpose |
|---|---|
| `microbit/main/mb2/main.py` | Main application: servo control, radio command handler |

No additional driver files are required. The servo is driven directly via `pin.set_analog_period_microseconds()` and `pin.write_analog()`.

> **Flashing:** Use the **Micro:bit web editor** to flash `main.py`.

---

## Servo Calibration

Both servos use identical calibration values (JX BLS-HV7146MG, 180°):

| Parameter | Value | Notes |
|---|---|---|
| `MAX_SLOTS` | 4 | Slots 0 → 1 → 2 → 3 → 4 |
| `PERIOD_US` | 20000µs | 50 Hz PWM signal |

Slot pulse widths (calibrated per-wheel — spacing is non-uniform):

| Slot | Wheel A (µs) | Wheel B (µs) | State |
|---|---|---|---|
| 0 | 500 | 500 | Empty — all pills dispensed, slot 0 at hole |
| 1 | 900 | 970 | 1 pill remaining |
| 2 | 1400 | 1450 | 2 pills remaining |
| 3 | 1900 | 1970 | 3 pills remaining |
| 4 | 2400 | 2450 | Full (4 pills) — slot 4 at hole, ready to dispense |

PWM is kept active continuously — releasing the signal causes servo hunting.

---

## Boot Sequence

1. Radio enabled (`radio.on()`, `radio.config(group=42)`)
2. LED matrix shows `"2"` (ready indicator)
3. Servos are **not** moved — MB2 waits for an `INIT:a,b` message from MB1 before positioning

This prevents unwanted rotation on reboot when pills are still in the wheel.

---

## Radio Protocol

All messages are received from MB1 (`radio.receive()`). MB2 sends no messages back.

| Message | Action |
|---|---|
| `INIT:a,b` | Restore servo positions from storage counts: `slot = count`, move each servo to `HOME_US + slot * STEP_US` |
| `DISPENSE:A` | If `slot_a > 0`: `slot_a -= 1`, move Servo A back one step (pill drops) |
| `DISPENSE:B` | If `slot_b > 0`: `slot_b -= 1`, move Servo B back one step |
| `DISPENSE:AB` | Decrement both servos (each independently guarded) |
| `REFILL:A` | `slot_a = 0`, move Servo A to HOME (500µs) |
| `REFILL:B` | `slot_b = 0`, move Servo B to HOME (500µs) |
| `SERVO_STEP:A` | If `slot_a < 4`: `slot_a += 1`, advance Servo A one step (used during MB1 refill mode) |
| `SERVO_STEP:B` | If `slot_b < 4`: `slot_b += 1`, advance Servo B one step |

### INIT position restore

When MB1 boots, it receives storage counts from the ESP32 (`STORAGE_SET:a,b`) and immediately sends `INIT:a,b` via radio. MB2 sets slot positions directly from the counts:

```
slot_a = storage_a    # e.g. storage_a=3 → slot_a=3 → 2000µs
slot_b = storage_b
```

This positions each servo at the correct angle for the next dispense without resetting to home.

### DISPENSE guard

If a dispense command arrives when `slot_a == 0` (empty), the servo does not move and the LED shows ✗ instead of the arrow.

---

## Refill Flow

The lid is fixed in place. Pills are loaded through the dispense hole one at a time:

1. MB1 sends `REFILL:A` (or B) → MB2 resets servo to HOME (slot 0, 500µs) — dispense hole is now at the first empty slot
2. User drops one pill into the dispense hole
3. MB1 sends `SERVO_STEP:A` (on each MB1 button press) → MB2 advances servo one step — next empty slot is now at the dispense hole
4. Repeat until all slots are filled (up to 4)
5. MB1 sends final `STORAGE:a,b` to ESP32 to persist the new count

---

## LED Matrix

| State | Display |
|---|---|
| Idle / waiting | `"2"` |
| DISPENSE:A or DISPENSE:AB — servo moved | Arrow right (→), 500ms |
| DISPENSE:B — servo moved | Arrow left (←), 500ms |
| DISPENSE received but `slot == 0` (empty) | ✗ (NO image), 500ms |
