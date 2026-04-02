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

---

## 30 March 2026

### New Experiments
- FC-51 IR obstacle sensor on P1 triggers buzzer on P0
- DS3231 RTC: ESP32 fetches NTP, sends to Micro:bit via UART, written to DS3231; time read from DS3231 and displayed on OLED every second; "No NTP signal" / "RTC Error" on failure

### Hardware Validated
- FC-51 IR obstacle sensor

### Main Project — Complete

Full integrated system built across all components:

**Micro:bit #1** (`microbit/main/mb1/main.py`)
- On every boot, syncs time from ESP32 NTP and writes it to the DS3231 RTC
- Clock reads DS3231 every second — no software clock; DS3231 TCXO eliminates drift
- Reads DHT20 every 30s; displays live on OLED (time / humidity+temp / next schedule countdown)
- Checks up to 6 medication schedules per minute; triggers alarm and dispense on match
- Long-press A/B to enter refill mode; LED matrix shows slot count; press to advance
- Storage counts initialised from ESP32 NVS on boot; synced back on every change

**ESP32** (`esp32/main/main.ino`)
- WiFi + NTP; sends `TIME:` to MB1 every second until acknowledged
- Persistent storage counts in NVS (Preferences library); restored after power loss
- MQTT bridge: relays sensor/storage/dispense data MB1 → broker, and commands broker → MB1
- Subscribes to retained `dispenser/schedules`; reformats and pushes to MB1 on connect

**Web Server** (`server/`)
- Flask app on `127.0.0.1:5000`, reverse-proxy ready
- Dashboard: storage (A/B) and environment sensor both auto-refresh every 5s; connection-lost modal on repeated failures
- Schedule management: add/delete up to 6 schedules; pushed to MQTT (retained)
- Settings: Telegram bot token, UID, temp/humidity alert thresholds
- Telegram alerts: storage empty (immediately), threshold exceeded (5-min cooldown)

### Design Decisions
- MB1 ↔ MB2 uses **radio** (built-in 2.4GHz, group 42) — UART already occupied by ESP32
- Servo control (MB2) is **stubbed** pending servo hardware
- Software clock dropped in favour of DS3231 — eliminates drift, survives power loss
- All protocols documented in [docs/main-project.md](main-project.md)

---

## 31 March 2026

### MB1 — Dispense UX

- **Normal dispense**: OLED switches to "Take meds / type / time"; buzzer plays Never Gonna Give You Up on loop; waits for FC-51 IR sensor (P1) to detect the user's hand before stopping music and restoring the display
- **Manual (silent) dispense**: drops pills via radio to MB2 with no buzzer or OLED change — useful for remote or caregiver-initiated doses

### MB1 — OLED improvements

- All four display lines now use `write_oled_large` (2× scale) — consistent font size throughout
- Time format changed to 12-hour AM/PM (`12:30 PM`); seconds removed
- Countdown format: `Nx:1H 25M` (or `No sched`); skips current-minute schedules immediately after dispensing to avoid showing `0H 00M`

### MB1 — Schedule reliability

- `check_schedules()` now called every second instead of only on minute-change detection
- `dispensed_this_minute` flag prevents double-firing; reset each time the minute advances
- Eliminates missed-dose risk if the DS3231 I2C read happens to fail at the exact second a minute begins

### MB1 — Source size

- All comments stripped from MB1 `.py` files to reduce combined source from ~20 KB to ~16 KB
- Files can be flashed via the **Micro:bit web editor**

### Web dashboard

- Storage cards now show counts only (dispense buttons removed)
- New **Dispense** section with two cards:
  - *Normal* — A, B, A+B buttons (triggers buzzer + alert)
  - *Manual* — A, B buttons (silent drop)
- Countdown badge format changed to `XH XXM` (e.g. "Next in 1H 25M")

### Protocol additions

| Layer | Addition |
|---|---|
| UART | `MANUAL:A/B` — ESP32 → MB1 for silent dispense |
| MQTT | `action=manual` in `dispenser/command` |

### Tested & Verified
- Telegram alerts confirmed working (storage empty + threshold exceeded)

---

## 1 April 2026

### Dashboard — offline detection & UX

- Device online/offline now detected via dedicated `dispenser/ping` heartbeat (ESP32 publishes every 5s); threshold 15s — max browser latency ~20s with no page reload
- Sensor read interval reduced from 30s to 15s
- Sensor last-updated timestamp format changed to `"Apr 01, 2026 14:32:05"` with seconds; font matched to section title
- IP address hidden when device is offline
- When offline: storage counts show `- / 7` (grey bar), sensor values show `—`
- Storage last-updated timestamp removed from dashboard

### Bug fixes

- **Storage resets to 7/7 on device reboot**: root cause was `push_init_to_mb()` publishing `dispenser/storage` from ESP32 NVS defaults on every reconnect, overwriting the server's `state.json`. Fixed by removing the MQTT publish from `push_init_to_mb()` — server `state.json` is now the sole source of truth

### Servo calibration — MB2

- Confirmed servo type: JX BLS-HV7146MG — discovered during testing that it is a **180° servo** (not 360° as initially assumed); physical range 500–2500µs extended
- Dispenser mechanism: 3D printed 8-spoke rotary wheel; tested with one servo at a time on P0
- Calibrated both Servo #1 (Type A) and Servo #2 (Type B) — identical values
- `HOME_US = 500`, `MAX_US = 2500`, `STEP_US = 500`, 4 steps (slots 0–4)
- The 180° constraint limits each wheel to **4 usable slots** (previously assumed 7) — storage capacity and all related logic will need to be updated accordingly
- Calibration documented in `experiments/servo-test/README.md` and `docs/hardware.md`

---

## 2 April 2026

Based on the 180° servo limitation discovered during calibration, the storage capacity was revised from 7 to 4 pills per type. The servo is now fully integrated into the main project with all dependent components updated to reflect the new capacity.

### MB2 — Servo integration (full rewrite)

- Rewrote `microbit/main/mb2/main.py` with `MAX_SLOTS=4`, `PERIOD_US=20000`; Servo A on P0, Servo B on P1
- Servo does **not** home on startup — waits for `INIT:a,b` from MB1 to restore position from storage counts (`slot_a = a` directly), so remaining pills are not disrupted on reboot
- **Slot direction clarified**: full (4 pills) = slot 4 at dispense hole; dispensing decrements 4 → 3 → 2 → 1 → 0 (slot 0 = empty, hole at lowest position)
- Radio commands handled: `INIT:a,b`, `DISPENSE:A/B/AB`, `REFILL:A/B`, `SERVO_STEP:A/B`
- Refill loads pills through the fixed dispense hole: `REFILL` resets servo to slot 0 (500µs), then `SERVO_STEP` advances one slot per button press as the user drops each pill
- Manual A/B button testing removed (calibration complete; buttons no longer needed)

### MB2 — Per-slot lookup tables (non-uniform spacing)

- Servo-cal experiment (`experiments/servo-cal/`) run to find exact pulse widths per slot: MQTT-driven, radio group 43, no reflashing required
- Calibration revealed non-uniform slot spacing; replaced `HOME_US + slot × STEP_US` formula with per-wheel lookup arrays:
  - `SLOTS_A = [500, 900, 1400, 1900, 2400]`
  - `SLOTS_B = [500, 970, 1450, 1970, 2450]`
- All `set_servo()` calls now index `SLOTS_A[slot_a]` / `SLOTS_B[slot_b]`

### MB1 — Storage cap + refill improvements

- Storage defaults changed: `storage_a/b = 7` → `4`; refill loop cap `< 7` → `< 4`
- After `STORAGE_SET:` received (boot or runtime reconnect), MB1 immediately sends `INIT:a,b` radio to MB2 to restore servo positions
- Refill mode: sends `REFILL:X` before count loop; sends `SERVO_STEP:X` on each button press; sends `INIT:a,b` again after refill completes so MB2 is positioned at the correct slot
- **Button release guard added**: refill entry waits for all buttons released and clears `was_pressed()` before starting the count loop — prevents spurious first-step advance caused by the long-press still being held
- Main loop body wrapped in `try/except` — catches crashes during refill/dispense, refreshes OLED, and continues running

### System — 4-pill capacity throughout

- Dashboard storage: `/7` → `/4`; low warning threshold revised to 1 pill remaining; storage card always starts as `- / 4` placeholder (no stale Jinja flash on page load)
- Dashboard poll interval reduced 5s → 2s for faster storage updates after dispense
- Schedule page: per-type limit of 4 (A and B independently); shows `Type A: X/4 | Type B: X/4`; type dropdown hides types at their limit
- ESP32 NVS defaults, `mqtt_bridge.py` in-memory defaults, all docs updated to reflect capacity of 4

### Storage sync — reconnect handling

- `mqtt_bridge.py` detects first `dispenser/ping` after a >15s gap (ESP32 was offline); on reconnect, pushes authoritative `set_storage` from `state.json` to MB1 via MQTT → ESP32 → UART — prevents stale ESP32 NVS overwriting the correct count

### Bug fixes

- **Storage count wrong after reconnect**: ESP32 NVS defaulted to 4 after reflash, sent `STORAGE_SET:4,4` overwriting actual 2. Fixed by mqtt_bridge pushing correct count from `state.json` on first ping after offline
- **MB2 shows X when pills remain (post-web-dispense)**: MB2 slot counter was stale. Fixed by MB1 resending `INIT:a,b` whenever `STORAGE_SET` is received at runtime
- **MB2 shows X after refill**: After refill, MB2 slot counter sat at `MAX_SLOTS` from repeated `SERVO_STEP`. Fixed by MB1 sending `INIT:storage_a,storage_b` after refill completes
- **Arrow shown but servo not moving**: `display.show(ARROW_E)` was outside the `slot_a > 0` guard — showed arrow even when guard failed. Moved inside guard; shows `Image.NO` when slot is already 0
- **Slot 0 advance on refill entry**: Long-press left button held; `was_pressed()` returned True immediately in refill loop. Fixed by explicit wait-for-release before loop starts

### Demo site (`demo.html`)

- Added Settings page (Telegram UID, bot token, notification toggles, temp/humidity alert thresholds) — fully dummy, editable for screenshots
- Fixed dispense alert wording to match real app (`'Dispense command sent for type A'`, not `'✅ Dispense command sent for type A (normal)'`)
- Removed stale `preview/` folder and related docs references
- Added direct `demo.html` link to root `README.md`

### Experiment: servo-cal

- Created `experiments/servo-cal/` — MQTT-driven per-slot pulse width calibration, no reflashing needed
- MB1 bridges UART → radio (group 43); MB2 receives `CAL:A,us` and sets servo PWM directly
- ESP32 subscribes to `dispenser/cal`, validates JSON `{wheel, us}`, forwards to MB1
- Calibration table documented in `experiments/servo-cal/README.md`; values applied to main project after calibration
