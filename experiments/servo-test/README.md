# Servo Test Experiment

Calibration experiment for the JX BLS-HV7146MG servo motors used in the pill dispenser mechanism.

## Hardware

- **Servo**: JX BLS-HV7146MG (180°, high voltage)
- **Signal pin**: P0 (one servo at a time)
- **Power**: 6–8.4V external supply (common GND with Micro:bit required)

## Mechanism

3D printed 8-spoke rotary wheel inside a ring casing. Each pill sits in one of the slots between spokes. The servo rotates the wheel to advance a slot to the dispense hole, dropping the pill.

Only 4 of the 8 slots are used (capacity of 4 pills per dispenser), covering the servo's full physical range.

## Calibration Results

Both Servo #1 (Type A) and Servo #2 (Type B) share the same values:

| Parameter | Value |
|---|---|
| Min pulse (0°) | 500 µs |
| Max pulse (180°) | 2500 µs |
| Home position (slot 0) | 500 µs |
| Slot 4 position | 2500 µs |
| Step per slot | 500 µs |
| Steps | 4 (slots 0→1→2→3→4) |
| PWM period | 20000 µs (50 Hz) |

Slot pulse widths:

| Slot | µs |
|---|---|
| 0 (home) | 500 |
| 1 | 1000 |
| 2 | 1500 |
| 3 | 2000 |
| 4 | 2500 |

## Controls

- **Button A** — advance one slot (0→1→2→3→4)
- **A + B** — reset to home (slot 0)
