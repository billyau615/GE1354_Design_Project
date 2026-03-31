// DS3231 Experiment — ESP32 NTP Time Provider
//
// Waits for TIME_REQ from Micro:bit, then sends TIME:HH:MM:SS every second
// until the Micro:bit replies with TIME_ACK.
//
// Wiring:
//   ESP32 GPIO17 (RX) ← Micro:bit P16 (TX)
//   ESP32 GPIO16 (TX) → Micro:bit P8  (RX)

#include <WiFi.h>
#include <time.h>

// ── Configuration ─────────────────────────────────────────────────────────────
const char* WIFI_SSID  = "";        // fill in
const char* WIFI_PASS  = "";        // fill in
const long  GMT_OFFSET = 8 * 3600; // UTC+8 Hong Kong
const int   DST_OFFSET = 0;

// ── Pin config ────────────────────────────────────────────────────────────────
#define MB_RX_PIN 17
#define MB_TX_PIN 16

// ── Globals ───────────────────────────────────────────────────────────────────
bool          req_received   = false;  // Micro:bit sent TIME_REQ
bool          ack_received   = false;  // Micro:bit sent TIME_ACK
unsigned long last_time_send = 0;
char          uart_buf[32];
int           uart_pos = 0;

// ── Setup ─────────────────────────────────────────────────────────────────────
void setup() {
    Serial.begin(115200);
    Serial1.begin(9600, SERIAL_8N1, MB_RX_PIN, MB_TX_PIN);

    // Connect WiFi
    Serial.print("Connecting WiFi");
    WiFi.begin(WIFI_SSID, WIFI_PASS);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println(" connected");

    // Sync NTP
    configTime(GMT_OFFSET, DST_OFFSET, "pool.ntp.org");
    Serial.print("Syncing NTP");
    struct tm t;
    while (!getLocalTime(&t)) { delay(500); Serial.print("."); }
    Serial.println(" synced");

    Serial.println("[ready] Waiting for TIME_REQ from Micro:bit...");
}

// ── Loop ──────────────────────────────────────────────────────────────────────
void loop() {
    // Read incoming UART from Micro:bit
    while (Serial1.available()) {
        char c = Serial1.read();
        if (c == '\n' || c == '\r') {
            if (uart_pos > 0) {
                uart_buf[uart_pos] = '\0';
                Serial.printf("[uart] recv: %s\n", uart_buf);
                if (strncmp(uart_buf, "TIME_REQ", 8) == 0) {
                    req_received = true;
                    last_time_send = 0;  // send immediately on next loop
                    Serial.println("[uart] TIME_REQ received, starting time broadcast");
                } else if (strncmp(uart_buf, "TIME_ACK", 8) == 0) {
                    ack_received = true;
                    Serial.println("[done] Micro:bit synced. DS3231 has been set.");
                }
                uart_pos = 0;
            }
        } else if (uart_pos < (int)sizeof(uart_buf) - 1) {
            uart_buf[uart_pos++] = c;
        }
    }

    // Once requested, send TIME: every second until ACK
    if (req_received && !ack_received) {
        unsigned long now = millis();
        if (now - last_time_send >= 1000) {
            last_time_send = now;
            struct tm t;
            if (getLocalTime(&t)) {
                char buf[16];
                strftime(buf, sizeof(buf), "%H:%M:%S", &t);
                Serial1.println(String("TIME:") + buf);
                Serial.printf("[uart] sent TIME:%s\n", buf);
            }
        }
    }
}
