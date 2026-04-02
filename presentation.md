# Presentation Outline

**Total Time:** 8 minutes · **Team:** 4 students · **Slides:** 13 (+ opening + ending)

---

## Speaker Distribution

| Student | Slides | Content |
|---|---|---|
| 1 | 1–3 | Problem Statement, System Architecture, Hardware |
| 2 | 4–7 | MB1 (sensors, scheduling, dispensing), MB2, Refill Mode |
| 3 | 8–11 | ESP32, Web UI ×2, Data Sync |
| 4 | 12–13 | Challenges & Solutions, Learnings & Future |

---

## Slide 1 — Problem Statement
**Student 1 · ~30s**

- Medication non-adherence is a real problem — elderly patients, multiple medications, fixed schedules
- Our solution: automated, scheduled, remotely monitored pill dispenser

---

## Slide 2 — System Architecture
**Student 1 · ~60s**

```
[MB1] ──radio──► [MB2]
  │
UART
  │
[ESP32] ──MQTT──► [Broker] ──MQTT──► [Web Server] ──HTTP──► [Browser]
                                            │
                                       [Telegram]
```

- Each node has one job — no overlap
- Why radio for MB1↔MB2: MB1's only UART is occupied by ESP32

---

## Slide 3 — Hardware Components
**Student 1 · ~30s**

*(Photo of assembled hardware)*

| Component | Role |
|---|---|
| Micro:bit #1 | Scheduler, sensors, OLED, buzzer |
| Micro:bit #2 | Drives 2 servo motors |
| ESP32 | WiFi + MQTT bridge |
| DHT20 | Temperature & humidity |
| DS3231 RTC | Battery-backed real-time clock |
| JX BLS-HV7146MG Servo ×2 | 4-slot rotary pill wheel |
| FC-51 IR sensor | Hand detection after dispense |
| SSD1306 OLED | Live time, sensor, next schedule |

---

## Slide 4 — Micro:bit #1: Sensors & Display
**Student 2 · ~45s**

- DS3231 RTC over I2C — reads time every second, survives power loss (battery-backed); no software clock drift
- DHT20 reads temperature & humidity every 15s
- OLED shows: current time / sensor readings / countdown to next dose
- IR sensor detects user's hand — confirms pill collected, stops buzzer

---

## Slide 5 — Micro:bit #1: Scheduling & Dispensing
**Student 2 · ~45s**

- Up to 4 schedules per medication type (A, B, or both)
- Checks DS3231 every second — triggers alarm exactly on time
- **Normal dispense**: buzzer plays, OLED shows "Take meds", waits for IR hand detection
- **Manual (silent) dispense**: web-triggered, no buzzer — for caregiver remote use
- Storage tracked per type; Telegram alert sent when a type runs empty

---

## Slide 6 — Micro:bit #2: Servo Control
**Student 2 · ~30s**

- Receives radio commands only — no UART, no sensors
- Two servos (Type A on P0, Type B on P1), 4 slots each
- Slot direction: slot 4 = full (pill at dispense hole), dispensing steps 4 → 3 → 2 → 1 → 0
- On boot: waits for `INIT:a,b` from MB1 before moving — pills not disrupted on reboot

---

## Slide 7 — Refill Mode
**Student 2 · ~30s**

- Long-press button A or B on MB1 → enter refill for that type
- Lid fixed; pills loaded through the dispense hole one at a time
- Servo resets to slot 0 → user drops pill → button press advances servo one slot → repeat
- MB1 LED shows current count (0–4); exit with other button → storage saved

---

## Slide 8 — ESP32: Bridge & Persistence
**Student 3 · ~45s**

- WiFi + NTP time sync; sends `TIME:HH:MM:SS` to MB1 every second until acknowledged
- Stores storage counts in NVS flash (Preferences library) — survives power loss
- MQTT relay: sensor/storage/dispense events MB1 → broker; commands broker → MB1
- Receives retained `dispenser/schedules` from broker on connect, reformats and pushes to MB1

---

## Slide 9 — Web UI: Dashboard
**Student 3 · ~45s**

*(Screenshot of dashboard)*

- Storage A/B: pill count with progress bar, low-warning highlight
- Environment: live temperature & humidity, last-updated timestamp
- Dispense section: Normal (A / B / A+B, triggers buzzer) and Manual (silent drop)
- Device status: Online/Offline indicator with IP address, updates every 2s

---

## Slide 10 — Web UI: Schedules & Settings
**Student 3 · ~45s**

*(Screenshot of schedules + settings pages)*

- **Schedules**: add/delete times per type; per-type limit of 4; shows `Type A: 2/4 | Type B: 1/4`
- **Settings**: Telegram bot token, user ID, temperature/humidity alert thresholds
- Schedule published as retained MQTT message → ESP32 receives on connect → pushed to MB1 — survives any reboot

---

## Slide 11 — Data Persistence & Sync
**Student 3 · ~30s**

One source of truth — `server/state.json`:

```
server/state.json  ← sole authority
      ↓ (on ESP32 reconnect)
   ESP32 NVS  →  UART  →  MB1 RAM
                               ↓ radio
                           MB2 servo position
```

After any reboot or reflash, all nodes re-sync from `state.json` — no stale counts.

---

## Slide 12 — Challenges & Solutions
**Student 4 · ~75s**

**1. Servo wasn't what we thought**
> Assumed 360° continuous rotation. Discovered mid-testing it is a 180° positional servo. Rebuilt wheel capacity 7 → 4 slots, rewrote all storage logic.

**2. Non-uniform slot spacing**
> Uniform 500µs steps didn't align the holes precisely. Built a dedicated MQTT-driven calibration experiment — publish `{"wheel": "A", "us": 1250}` to MQTT, servo moves immediately, no reflashing needed. Found and stored exact pulse widths for all 5 positions on both wheels.

**3. Storage mismatch after ESP32 reflash**
> ESP32 NVS resets to defaults after reflash, overwriting the actual pill count. Solution: `server/state.json` is the sole authority; on ESP32 reconnect, server pushes the correct count back down the chain to MB1 and MB2.

---

## Slide 13 — Learnings & Future Improvements
**Student 4 · ~45s**

**Key learnings:**
- Multi-device systems need a single source of truth — design it early
- Physical hardware surprises you — test each component in isolation first
- Incremental integration (experiment → verify → integrate) saves debugging time

**Future improvements:**
- Weight sensor to confirm pill actually dispensed
- Mobile app with push notifications
- Support more than 2 medication types
