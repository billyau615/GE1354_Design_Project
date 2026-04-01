# Micro:bit #1 — Component Documentation

> Last updated: 31 March 2026

Micro:bit #1 is the central logic node of the drug dispenser. It manages the real-time clock, sensor readings, medication schedules, dispensing logic, and the OLED display. It communicates with the ESP32 over UART and with Micro:bit #2 over the built-in 2.4 GHz radio.

---

## Hardware Connections

| Component | Interface | Pin(s) | Notes |
|---|---|---|---|
| ESP32 (UART) | UART | P8 (RX), P16 (TX) | 9600 baud, 3.3V TTL |
| SSD1306 OLED 128×64 | I2C | P19 (SCL), P20 (SDA) | Address 0x3C |
| DHT20 temperature/humidity | I2C | P19 (SCL), P20 (SDA) | Address 0x38 |
| DS3231 RTC | I2C | P19 (SCL), P20 (SDA) | Address 0x68 |
| Passive buzzer | PWM | P0 | Active-low via `music.pitch` / `music.play` |
| FC-51 IR obstacle sensor | Digital in | P1 | LOW (0) = obstacle detected |
| Micro:bit #2 (radio) | 2.4 GHz radio | Built-in | `group=42` |

The I2C bus is shared between three devices (OLED 0x3C, DHT20 0x38, DS3231 0x68). MicroPython on Micro:bit is single-threaded so all I2C access is sequential with no conflicts.

---

## Source Files

All files are located in `microbit/main/mb1/`.

| File | Purpose |
|---|---|
| `main.py` | Main application: boot sequence, all logic, main loop |
| `oled.py` | SSD1306 OLED driver: init, clear, 1× and 2× text rendering |
| `dht20.py` | DHT20 sensor driver: single-shot measurement |
| `ds3231.py` | DS3231 RTC driver: read/write time, BCD encode/decode |

> **Flashing:** Files must be transferred individually using **Thonny** (View → Files → right-click each `.py` → Upload to /). The Micro:bit web editor has a size limit (~8 KB) that these files exceed when combined.

---

## Boot Sequence

The boot sequence runs once at startup before the main loop begins. It performs three blocking waits in order:

### 1. NTP time sync (blocking — no timeout)

MB1 sends `TIME_REQ` to the ESP32 over UART. It repeats this request every 2 seconds until a valid `TIME:HH:MM:SS` response is received. This is necessary because MB1 boots faster than the ESP32 (which must connect to WiFi and sync NTP before it can respond). Once the time is received, MB1 writes it to the DS3231 RTC and replies `TIME_ACK` to stop further broadcasts.

```
MB1 ──TIME_REQ──► ESP32   (repeats every 2s)
MB1 ◄──TIME:14:30:22── ESP32   (every 1s once WiFi+NTP ready)
MB1 writes to DS3231
MB1 ──TIME_ACK──► ESP32   (ESP32 stops sending)
```

The OLED shows "Waiting NTP..." during this phase.

### 2. Schedule receive (non-blocking, 3-second timeout)

Immediately after time sync, MB1 polls UART for up to 3 seconds waiting for a `SCHED:` message. The ESP32 publishes the retained `dispenser/schedules` MQTT topic on connect, which triggers the UART push. If no schedule arrives within 3 seconds, MB1 continues with an empty schedule list.

### 3. Storage count receive (non-blocking, 3-second timeout)

Similarly, MB1 polls for `STORAGE_SET:a,b` for up to 3 seconds. The ESP32 reads its NVS flash on connect and sends the persisted counts. If nothing arrives, storage defaults to 4/4.

After all three waits, the OLED is cleared, the first DHT20 reading is taken, and the main loop starts.

---

## Main Loop

The main loop runs once per second (`sleep(1000)` at the end). Each iteration:

1. **`read_uart()`** — reads any pending bytes from the ESP32 and dispatches complete lines
2. **`check_long_press()`** — detects held buttons for refill mode entry
3. **`read_ds3231()`** — reads current time from RTC; if successful, updates `h/m/s` and checks if the minute has changed
4. **`check_schedules()`** — compares current `h:m` against all stored schedules; fires dispense if match found and not yet dispensed this minute
5. **Sensor timer** — counts down; when it reaches 0, reads DHT20 and resets to 15 (i.e., sensor read every ~15 seconds)
6. **`update_oled()`** — redraws all four OLED lines

---

## Timekeeping

The DS3231 is a hardware real-time clock with a temperature-compensated crystal oscillator (TCXO), accurate to ±2 ppm (approximately 5 seconds per month). It maintains time across power loss using a CR2032 coin cell battery.

MB1 does **not** maintain a software clock. Every second, it reads the current time directly from DS3231. If a read fails (returns `None, None, None`), the previous values of `h`, `m`, `s` are kept unchanged until the next successful read.

**Schedule trigger reliability:** `check_schedules()` is called on every main loop iteration (every second), not only when the minute changes. The `dispensed_this_minute` flag (reset on minute change) prevents double-firing. This means even if the DS3231 I2C read fails at the exact second a new minute begins, the schedule will still be triggered on the next successful read within that minute.

---

## Dispensing

### Normal dispense (`DISPENSE:type` via UART or scheduled)

Triggered by:
- A scheduled time match in `check_schedules()`
- A `DISPENSE:` UART command from the ESP32 (web UI normal dispense)

Behaviour:
1. **Stock check** — if the required type is at 0, sends `STORAGE:...:EMPTY_X` back to ESP32 and returns without dispensing
2. **Radio** — sends `DISPENSE:type` to MB2 to activate the servo
3. **OLED** switches to alert screen (see OLED section)
4. **Buzzer** — plays *Never Gonna Give You Up* on loop (`music.play(..., loop=True, wait=False)`)
5. **IR wait** — polls P1 every 50 ms; blocks until `pin1.read_digital() == 0` (hand detected under dispenser)
6. **Buzzer stop** — `music.stop(pin0)`
7. **Decrement storage** — reduces `storage_a` and/or `storage_b`; appends `:EMPTY_X` flag if now 0
8. **UART reports** — sends `STORAGE:a,b[:EMPTY_X]` then `DISPENSE_DONE:type`
9. **OLED restored** — `update_oled()` called immediately

### Manual (silent) dispense (`MANUAL:type` via UART)

Triggered by a `MANUAL:` UART command from the ESP32 (web UI manual dispense).

Behaviour:
1. Stock check (same as above)
2. Radio — sends `DISPENSE:type` to MB2
3. Decrement storage
4. UART reports
5. **No buzzer, no OLED change, no IR wait**

---

## Schedules

Schedules are stored as a list of `(hour, minute, type_str)` tuples in memory. The list is populated at boot from the `SCHED:` UART message and updated at any time via subsequent `SCHED:` messages.

Format received: `SCHED:14:30:A,15:00:B,16:00:AB`

The parser splits on `,`, then uses `rfind(":")` to separate the time portion from the type, allowing types like `AB` that themselves contain no colon.

Each entry supports type `A`, `B`, or `AB`. Scheduled dispenses always use the normal dispense path (buzzer + OLED + IR wait).

---

## Refill Mode

Entered by holding button A (Type A) or button B (Type B) for approximately 1 second. The long-press is detected by counting consecutive `is_pressed()` readings in the main loop (2 consecutive = ~2 seconds given the 1000 ms sleep).

**If pills remain** when entering refill mode:
- OLED shows `"X has Y left"` and `"A=reset B=cancel"`
- The code waits for both buttons to be fully released (drains `was_pressed()` state) before entering the confirm loop, preventing the long-press release from immediately dismissing the screen
- Button A confirms zero-reset; Button B cancels without changes

**Refill counting loop:**
- Before the loop starts, MB1 sends `REFILL:X` to MB2, which resets that servo to HOME (slot 0, 500µs) — dispense hole is now at the first empty slot
- OLED shows `"Refill X"` (small text); LED matrix shows current slot count (0–4)
- Press the same button (A for Type A, B for Type B) once per pill: MB1 increments the count and sends `SERVO_STEP:X` to MB2, advancing the servo one slot so the next empty slot is at the dispense hole
- Press the other button to exit

On exit, the new count is saved to `storage_a`/`storage_b` and reported via UART (`STORAGE:a,b`).

---

## Sensors

### DHT20 (temperature and humidity)

- Read every **15 seconds** (15 main loop iterations of 1 second each)
- On success: values stored in `last_temp`, `last_humi`; sent to ESP32 as `SENSOR:temp,humi`
- On failure: previous values retained; OLED shows `"Sensor..."` until first successful read

### DS3231 (real-time clock)

- Read every **1 second** (each main loop iteration)
- Returns `(None, None, None)` on I2C error — previous time values are kept

---

## OLED Display

The SSD1306 is a 128×64 pixel display divided into 8 horizontal pages (each 8 px tall). All four display lines use `write_oled_large` which renders text at 2× scale (16 px tall = 2 pages per line), giving a maximum of approximately 10 characters per line.

### Normal display layout

| Pages | Content | Example | Update rate |
|---|---|---|---|
| 0–1 | Current time (12-hour, AM/PM) | `1:30 PM` (no leading zero) | Every second |
| 2–3 | Humidity | `H:62.5%` | Every 30 seconds |
| 4–5 | Temperature | `T:28.3C` | Every 30 seconds |
| 6–7 | Countdown to next dose | `Nx:1H 25M` or `No sched` | Every second |

The countdown skips schedules whose `delta == 0` (the current minute), so immediately after a dose is dispensed it shows the next future event rather than `0H 00M`.

### Dispense alert layout

Shown from the moment a normal dispense starts until the IR sensor is triggered:

| Pages | Content | Example |
|---|---|---|
| 0–1 | Alert heading | `Take meds` |
| 2–3 | Type being dispensed | `A`, `B`, or `A+B` |
| 4–5 | Current time | `02:30 PM` |
| 6–7 | Blank | |

### Font

`oled.py` contains a full 5×8 pixel bitmap font covering ASCII 32–126 (95 characters). The `write_oled_large` function doubles each pixel horizontally and vertically using bit-level nibble expansion (`_scale_nibble`), rendering at 10×16 px per character with 2 px horizontal spacing (12 px stride).

---

## UART Protocol (MB1 ↔ ESP32)

9600 baud, 8N1, newline-terminated ASCII strings.

| Direction | Message | Meaning |
|---|---|---|
| MB→ESP | `TIME_REQ` | Request current NTP time |
| MB→ESP | `TIME_ACK` | Time received and written to DS3231 |
| MB→ESP | `SENSOR:25.1,60.5` | Temperature (°C), humidity (%) |
| MB→ESP | `STORAGE:4,3` | Current storage counts after dispense or refill |
| MB→ESP | `STORAGE:0,3:EMPTY_A` | Storage update with empty flag (triggers Telegram) |
| MB→ESP | `DISPENSE_DONE:A` | Confirmed dispense complete |
| ESP→MB | `TIME:14:30:22` | NTP time (sent every 1s after TIME_REQ until ACK) |
| ESP→MB | `SCHED:14:30:A,15:00:B` | Full schedule list (comma-separated) |
| ESP→MB | `STORAGE_SET:4,3` | Initial storage counts from NVS on boot |
| ESP→MB | `DISPENSE:A/B/AB` | Normal dispense command from web UI |
| ESP→MB | `MANUAL:A/B` | Silent dispense command from web UI |

---

## Radio Protocol (MB1 ↔ MB2)

`radio.config(group=42)`, default power and data rate.

| Direction | Message | Meaning |
|---|---|---|
| MB1→MB2 | `DISPENSE:A/B/AB` | Activate servo for dispensing |
| MB1→MB2 | `INIT:a,b` | On boot — restore servo positions from storage counts |
| MB1→MB2 | `REFILL:A/B` | Reset servo to HOME before refill counting loop |
| MB1→MB2 | `SERVO_STEP:A/B` | Advance servo one slot per button press during refill |
