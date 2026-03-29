// NTP Clock — fetches time and sends to Micro:bit over UART every second.
//
// Wiring:
//   ESP32 GPIO11 (RX) ← Micro:bit P16 (TX)
//   ESP32 GPIO12 (TX) → Micro:bit P8  (RX)
//
// WARNING: GPIO11 is part of the SPI flash interface on most ESP32 boards.
// If the board fails to boot or connect, use a different RX pin (e.g. GPIO16)
// and update MB_RX_PIN below.

#include <WiFi.h>
#include <time.h>

// ── User configuration ──────────────────────────────────────────────────────
const char* WIFI_SSID    = "your_ssid";
const char* WIFI_PASS    = "your_password";
const char* NTP_SERVER   = "pool.ntp.org";
const long  GMT_OFFSET   = 8 * 3600;   // UTC+8 (Hong Kong)
const int   DST_OFFSET   = 0;

// ── Pin configuration ───────────────────────────────────────────────────────
#define MB_RX_PIN 11   // receives from Micro:bit P16
#define MB_TX_PIN 12   // sends to Micro:bit P8

void setup() {
    Serial.begin(115200);
    Serial1.begin(9600, SERIAL_8N1, MB_RX_PIN, MB_TX_PIN);

    Serial.print("Connecting to WiFi");
    WiFi.begin(WIFI_SSID, WIFI_PASS);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println(" connected");

    configTime(GMT_OFFSET, DST_OFFSET, NTP_SERVER);

    // Wait for NTP sync
    struct tm timeinfo;
    Serial.print("Syncing NTP");
    while (!getLocalTime(&timeinfo)) {
        delay(500);
        Serial.print(".");
    }
    Serial.println(" synced");
}

void loop() {
    struct tm timeinfo;
    if (!getLocalTime(&timeinfo)) {
        delay(1000);
        return;
    }

    // Send "YYYY-MM-DD HH:MM:SS\n" to Micro:bit
    char buf[20];
    strftime(buf, sizeof(buf), "%Y-%m-%d %H:%M:%S", &timeinfo);
    Serial1.println(buf);
    Serial.println(buf);  // debug via USB

    delay(1000);
}
