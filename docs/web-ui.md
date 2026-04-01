# Web UI — Component Documentation

> Last updated: 31 March 2026

The web UI is a multi-page Bootstrap 5 application served by the Flask backend. It provides real-time monitoring of the dispenser state, manual dispense controls, schedule management, and system settings. All pages are mobile-responsive and use a dark fixed-top navbar for navigation.

---

## Accessing the UI

The server listens on `0.0.0.0:5000`. Access it from any device on the same network:

```
http://<server-ip>:5000
```

---

## Navigation

A fixed dark navbar appears on every page with three links:

| Link | Route | Purpose |
|---|---|---|
| Dashboard | `/` | Live overview of storage, environment, and upcoming schedules |
| Schedules | `/schedules` | Add and delete medication schedules |
| Settings | `/settings` | Telegram credentials and alert thresholds |

On narrow screens the navbar collapses into a hamburger menu.

---

## Page: Dashboard (`/`)

The main page. It displays live data and dispense controls. Data is automatically refreshed every **5 seconds** via JavaScript `fetch()` calls — no page reload required.

### Section: Device

A single card showing the ESP32 connection status, updated every 5 seconds:

- **Status dot** — green (`#198754`) if online, red (`#dc3545`) if offline
- **Status text** — `"Online"` or `"Offline"`
- **IP address** — shown beside the status text once the first sensor message is received

The device is considered **online** if a `dispenser/ping` MQTT heartbeat was received within the last **15 seconds**. The ESP32 publishes a ping every 5 seconds; two missed pings plus the 5 s browser poll gives a maximum offline detection latency of ~20 seconds without a page reload.

### Section: Storage

Two cards (one per medication type) showing:

- **Type label** (Type A / Type B) — small uppercase label
- **Count** — large number in `X / 7` format (e.g. `5 / 7`)
- **Progress bar** — colour-coded pill bar:
  - Green (`#198754`) — 3 or more remaining
  - Amber (`#ffc107`) — 1 or 2 remaining
  - Red (`#dc3545`) — 0 remaining (empty)
- **Warning text** — shown when low or empty:
  - `"Low — refill soon"` (≤ 2 pills, amber)
  - `"Empty — please refill"` (0 pills, red)
  - Hidden when stock is sufficient

Both cards and their progress bars update every 5 seconds by polling `/api/storage`. When the device is offline, both counts display as `- / 7` with a grey bar.

### Section: Dispense

Two sub-cards for the two dispense modes:

**Normal — buzzer & alert**
- Buttons: `Type A`, `Type B`, `A + B`
- Triggers a full dispense: MB1 plays buzzer (NGGYU), OLED shows "Take meds", waits for IR sensor
- Confirmation dialog before sending

**Manual — silent drop**
- Buttons: `Type A`, `Type B`
- Silently activates MB2 servo and decrements storage — no buzzer, no OLED change
- Confirmation dialog before sending

Both modes send a `POST /dispense` request with the type and mode. If the request succeeds, the storage display is refreshed immediately.

### Section: Environment

Two cards showing the latest sensor reading from the DHT20:

| Card | Value | Colour |
|---|---|---|
| Temperature | e.g. `28.3°C` | Red (`text-danger`) |
| Humidity | e.g. `62.5%` | Blue (`text-info`) |

Below the section title, a timestamp shows when the reading was last received (e.g. `"Apr 01, 2026 14:32"`). If no reading has been received since the server started, it shows `"Not yet received"`. When the device is offline, the sensor values show `—`.

**Update frequency:** MB1 reads the DHT20 every **15 seconds** and sends the result over UART → MQTT → server. The dashboard polls `/api/sensor` every 5 seconds, so the displayed value may be up to 5 seconds behind the server's most recent value, and up to 20 seconds behind the physical sensor.

### Section: Upcoming Schedules

A compact table listing all configured schedules sorted by time:

| Column | Content |
|---|---|
| Time | 24-hour time (e.g. `14:30`) |
| Type | `Type A`, `Type B`, or `A + B` |

- If no schedules exist, a text prompt links to the Schedules page
- A **"Next in XH XXM"** badge appears in the section heading when at least one schedule is configured, showing the time until the next upcoming dose. This badge updates every 5 seconds by polling `/api/countdown`.
- A **"Manage schedules →"** button links to `/schedules`

### Connection Lost Modal

If 3 or more consecutive API poll failures occur (network error or non-2xx response), a full-screen modal appears with a "Refresh Page" button. The modal cannot be dismissed by clicking outside or pressing Escape (`data-bs-backdrop="static"`).

---

## Page: Schedules (`/schedules`)

Displays and manages medication schedules. Up to **6 schedules** can be configured.

### Schedule list

A table with columns: index, time (24h), type, and a Delete button. Clicking Delete shows a confirmation dialog before submitting a `POST /schedules/delete/<index>` form.

### Add Schedule form

Shown only when fewer than 6 schedules exist. Two fields:

| Field | Type | Values |
|---|---|---|
| Time | `<input type="time">` | Any 24-hour time (HH:MM) |
| Type | `<select>` | Type A, Type B, Both (A + B) |

On submit, the new schedule is appended, the list is sorted by time, and the updated list is immediately published to the MQTT broker (retained). MB1 receives the updated schedule on its next UART read.

When 6 schedules are already configured, the form is hidden and replaced with a warning message.

---

## Page: Settings (`/settings`)

A single form for Telegram notifications and alert thresholds. Maximum width of 480 px.

### Telegram Notifications

| Field | Description |
|---|---|
| Bot Token | The token from @BotFather. Password field — leave blank to keep the current token. |
| Telegram User ID(s) | One or more numeric user IDs separated by commas. Alerts are sent to all listed IDs. Find your ID via @userinfobot. |

### Notification Toggles

Two checkboxes to independently enable or disable each alert category:

| Checkbox | Controls |
|---|---|
| Environment alerts | Temperature and humidity threshold alerts |
| Storage empty alerts | Alerts sent when the last pill is dispensed |

### Alert Thresholds

| Field | Default | Description |
|---|---|---|
| Temperature (°C) | 35.0 | Alert sent if temperature exceeds this value |
| Humidity (%) | 80.0 | Alert sent if humidity exceeds this value |
| Environment Alert Cooldown (s) | 300 | Minimum seconds between repeated environment alerts. Storage alerts always send immediately and are not affected by this setting. |

Saving the form writes all values to `server/data/settings.json`. The bot token is only updated if the field is non-empty.

---

## Real-Time Polling (JavaScript)

The dashboard uses a single `poll()` function that runs on page load and then every **5 seconds** via `setInterval`. It fires three `fetch()` requests in parallel using `Promise.all`:

| Endpoint | Returns | Used for |
|---|---|---|
| `GET /api/storage` | `{"a": 5, "b": 7}` | Storage cards and progress bars (shown only when online) |
| `GET /api/status` | `{"online": true, "ip": "192.168.1.42"}` | Device status dot, IP; gates whether storage/sensor values display |
| `GET /api/sensor` | `{"temp": 28.3, "humidity": 62.5, "updated": "Apr 01, 2026 14:32"}` | Environment cards and timestamp (shown only when online) |
| `GET /api/countdown` | `{"countdown": "1H 25M"}` or `{"countdown": null}` | Next-dose badge |

If any of the three requests fails (network error or non-OK status), a failure counter increments. After **3 consecutive failures** the connection-lost modal is shown.

On a successful poll cycle, the failure counter resets to 0.

---

## Styling

Styles are defined in `base.html` and shared across all pages.

| Class | Used for |
|---|---|
| `.storage-count` | Large bold number (3.2rem) in storage cards |
| `.storage-label` | Small uppercase label (0.85rem) above the count |
| `.sensor-val` | Large value (2rem, `white-space: nowrap`) in environment cards |
| `.section-title` | Small uppercase section headings (0.75rem, letter-spaced) |
| `.pill-bar` | Grey background track for the storage progress bar |
| `.pill-bar-fill` | Coloured fill; smooth CSS transition on width and colour changes |

The layout uses Bootstrap 5.3.3 loaded from jsDelivr CDN. Container max-width is 900 px.
