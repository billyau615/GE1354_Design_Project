# ESP32 — Component Documentation

> Last updated: 2 April 2026

The ESP32 acts as a **network bridge** between Micro:bit #1 and the MQTT broker. It handles WiFi connectivity, NTP time synchronisation, MQTT publish/subscribe, and bidirectional UART relay to MB1. It also persists storage counts across reboots using its internal NVS flash.

---

## Hardware Connections

| Connection | ESP32 Pin | MB1 Pin | Notes |
|---|---|---|---|
| UART TX → MB1 RX | GPIO16 | P8 | 9600 baud, 3.3V TTL |
| UART RX ← MB1 TX | GPIO17 | P16 | 9600 baud, 3.3V TTL |
| USB (Serial monitor) | USB / GPIO1/3 | — | 115200 baud, debug output |

---

## Source File

`esp32/main/main.ino` — single Arduino sketch.

### Required Libraries (Arduino Library Manager)

| Library | Author | Version |
|---|---|---|
| PubSubClient | Nick O'Leary | any recent |
| ArduinoJson | Benoit Blanchon | 6.x |
| Preferences | Built into ESP32 core | — |

---

## Configuration

All credentials and connection settings are defined as constants at the top of `main.ino`:

| Constant | Default | Description |
|---|---|---|
| `WIFI_SSID` | — | WiFi network name |
| `WIFI_PASS` | — | WiFi password |
| `MQTT_HOST` | — | MQTT broker hostname or IP |
| `MQTT_PORT` | `1883` | MQTT broker port |
| `MQTT_USER` | — | MQTT username |
| `MQTT_PASS` | — | MQTT password |
| `GMT_OFFSET` | `8 * 3600` | UTC+8 (Hong Kong) |
| `DST_OFFSET` | `0` | No daylight saving |

---

## Setup Sequence (`setup()`)

1. **Serial** — opens Serial (USB) at 115200 baud for debug output
2. **Serial1** — opens Serial1 at 9600 baud on GPIO16 (TX) / GPIO17 (RX) for MB1 communication
3. **WiFi** — connects using `WiFi.begin()`; blocks until `WL_CONNECTED`
4. **NTP** — calls `configTime(GMT_OFFSET, DST_OFFSET, "pool.ntp.org")`; blocks until `getLocalTime()` succeeds
5. **MQTT** — sets server, callback, and buffer size (512 bytes); calls `connect_mqtt()`
6. **NVS** — opens the `"dispenser"` Preferences namespace

---

## Main Loop (`loop()`)

The loop runs continuously with no fixed delay. Each iteration:

1. **MQTT keepalive** — if disconnected, calls `reconnect_mqtt()` (5-second blocking delay per attempt); if connected, calls `mqttClient.loop()` to process incoming messages and maintain the heartbeat
2. **Time broadcast** — if `req_received` is true and `init_done` is false, checks whether 1 second has elapsed since the last send; if so, calls `send_time_to_mb()`
3. **Heartbeat ping** — if connected and 5 seconds have elapsed since the last ping, publishes `"1"` to `dispenser/ping`. The server uses this to determine online/offline status with a 15-second timeout.
4. **`read_mb_uart()`** — reads any available bytes from Serial1 and dispatches complete lines

---

## MQTT Connection

Client ID: `"dispenser-esp32"`

On successful connect:
- Subscribes to `dispenser/command`
- Subscribes to `dispenser/schedules`
- Resets `reconnect_fails` counter
- Calls `push_init_to_mb()` to immediately send storage counts and current schedule to MB1

**Reconnection logic:** If the connection drops, `reconnect_mqtt()` waits 5 seconds then retries. After 5 consecutive failures it calls `ESP.restart()` to reboot the device. This prevents the ESP32 from running indefinitely without a broker connection.

**MQTT buffer:** Set to 512 bytes via `mqttClient.setBufferSize(512)`. The default 256-byte buffer is insufficient for schedule payloads containing multiple entries.

---

## MQTT Callback (`mqtt_callback`)

### Topic: `dispenser/command`

Parses a JSON object with `action` and `type` fields.

| `action` value | Behaviour |
|---|---|
| `"dispense"` | Sends `DISPENSE:<type>` over UART to MB1 — triggers normal dispense (buzzer + OLED alert + IR wait) |
| `"manual"` | Sends `MANUAL:<type>` over UART to MB1 — triggers silent dispense |
| `"set_storage"` | Sends `STORAGE_SET:a,b` to MB1 and writes `a`/`b` to NVS |

### Topic: `dispenser/schedules`

Receives a JSON array such as `[{"time":"14:30","type":"A"}, ...]`. Reformats it into the compact UART schedule line: `SCHED:14:30:A,15:00:B`. If the array is empty, sends `SCHED:` (empty body) so MB1 clears its schedule list.

---

## NTP Time Synchronisation

The ESP32 uses the Arduino `configTime` / `getLocalTime` API to maintain a system clock synchronised to `pool.ntp.org` at UTC+8.

**Time handshake with MB1:**

1. MB1 sends `TIME_REQ` over UART (repeated every 2 seconds)
2. On receiving `TIME_REQ`, the ESP32 sets `req_received = true` and starts sending `TIME:HH:MM:SS` once per second
3. When MB1 replies `TIME_ACK`, `init_done` is set to `true` and time broadcasts stop

This design handles the timing race where MB1 boots faster than the ESP32 can connect to WiFi and sync NTP.

---

## NVS Storage Persistence (`Preferences`)

The ESP32 stores `storage_a` and `storage_b` integers in its internal NVS flash under the namespace `"dispenser"`. These values survive power loss and reboots.

**On connect:** `push_init_to_mb()` reads the NVS values and:
- Sends `STORAGE_SET:a,b` to MB1 so it initialises with the correct counts
- Publishes `{"a": a, "b": b}` to `dispenser/storage` so the server dashboard is up to date immediately

**On dispense:** When MB1 reports `STORAGE:a,b` back over UART, the new counts are written to NVS and published to MQTT.

---

## UART Receive (`read_mb_uart` / `handle_mb_line`)

Bytes are read one at a time from Serial1 into a 128-byte buffer. On `\n` or `\r`, the buffer is null-terminated and dispatched to `handle_mb_line`.

| Received message | Action |
|---|---|
| `TIME_REQ` | Sets `req_received = true`; resets timer so next send is immediate |
| `TIME_ACK` | Sets `init_done = true`; time broadcasts cease |
| `SENSOR:temp,humi` | Parses two floats; publishes `{"temp": x, "humidity": y, "ip": "192.168.x.x"}` to `dispenser/sensor` |
| `STORAGE:a,b[:EMPTY_X]` | Parses counts; writes to NVS; publishes to `dispenser/storage` with optional `empty_a`/`empty_b` flags |
| `DISPENSE_DONE:type` | Publishes `{"type": "A"}` to `dispenser/dispense_done` |

---

## MQTT Topics Published

| Topic | Payload | Trigger |
|---|---|---|
| `dispenser/ping` | `"1"` | Every **5 seconds** while connected; used by server to detect online/offline |
| `dispenser/sensor` | `{"temp": 25.1, "humidity": 60.5, "ip": "192.168.1.42"}` | On each `SENSOR:` UART message from MB1 (~every 15s) |
| `dispenser/storage` | `{"a": 7, "b": 5}` or `{"a": 0, "b": 5, "empty_a": true}` | On `STORAGE:` UART message; also on connect via `push_init_to_mb()` |
| `dispenser/dispense_done` | `{"type": "A"}` | On `DISPENSE_DONE:` UART message |

---

## Debug Output (Serial Monitor, 115200 baud)

All key events are logged to the USB serial port:

```
Connecting WiFi... connected
Syncing NTP... synced
[mqtt] connected
[uart] sent STORAGE_SET:4,4
[uart] recv: TIME_REQ
[uart] sent TIME:14:30:22
[uart] recv: TIME_ACK
[mqtt] dispenser/command: {"action":"dispense","type":"A"}
[uart] sent: DISPENSE:A
[uart] recv: STORAGE:6,7
[mqtt] dispenser/schedules: [{"time":"14:30","type":"A"}]
[uart] sent: SCHED:14:30:A
```
