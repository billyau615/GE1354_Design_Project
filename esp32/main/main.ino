// Automated Drug Dispenser — ESP32 MQTT Bridge
//
// Wiring:
//   ESP32 GPIO17 (RX) ← Micro:bit P16 (TX)
//   ESP32 GPIO16 (TX) → Micro:bit P8  (RX)
//
// Required libraries (Arduino Library Manager):
//   - PubSubClient by Nick O'Leary
//   - ArduinoJson by Benoit Blanchon (v6.x)

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <Preferences.h>
#include <time.h>

// ── Configuration ─────────────────────────────────────────────────────────────
const char* WIFI_SSID  = "YOUR_WIFI_SSID";        // fill in
const char* WIFI_PASS  = "YOUR_WIFI_PASSWORD";        // fill in
const char* MQTT_HOST  = "YOUR_MQTT_HOST";        // fill in (e.g. "192.168.1.100")
const int   MQTT_PORT  = 1883;
const char* MQTT_USER  = "YOUR_MQTT_USER";        // fill in
const char* MQTT_PASS  = "YOUR_MQTT_PASSWORD";        // fill in
const long  GMT_OFFSET = 8 * 3600; // UTC+8 Hong Kong
const int   DST_OFFSET = 0;

// ── Pin config ────────────────────────────────────────────────────────────────
#define MB_RX_PIN 17
#define MB_TX_PIN 16

// ── Globals ───────────────────────────────────────────────────────────────────
WiFiClient   wifiClient;
PubSubClient mqttClient(wifiClient);
Preferences  prefs;

bool     req_received  = false;   // MB1 sent TIME_REQ
bool     init_done     = false;   // MB1 sent TIME_ACK
unsigned long last_time_send = 0;

char     uart_buf[128];
int      uart_pos = 0;

int reconnect_fails = 0;
unsigned long last_ping_ms = 0;

// ── Forward declarations ──────────────────────────────────────────────────────
void mqtt_callback(char* topic, byte* payload, unsigned int length);
void connect_mqtt();
void reconnect_mqtt();
void send_time_to_mb();
void read_mb_uart();
void handle_mb_line(const char* line);
void push_init_to_mb();

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

    // MQTT
    mqttClient.setServer(MQTT_HOST, MQTT_PORT);
    mqttClient.setCallback(mqtt_callback);
    mqttClient.setBufferSize(512);
    connect_mqtt();

    prefs.begin("dispenser", false);
}

// ── Loop ──────────────────────────────────────────────────────────────────────
void loop() {
    if (!mqttClient.connected()) {
        reconnect_mqtt();
    }
    mqttClient.loop();

    // Once MB1 requests time, send every second until acknowledged
    if (req_received && !init_done) {
        unsigned long now = millis();
        if (now - last_time_send >= 1000) {
            last_time_send = now;
            send_time_to_mb();
        }
    }

    // Heartbeat ping every 5 seconds for server online detection
    if (mqttClient.connected()) {
        unsigned long now = millis();
        if (now - last_ping_ms >= 5000) {
            last_ping_ms = now;
            mqttClient.publish("dispenser/ping", "1");
        }
    }

    read_mb_uart();
}

// ── MQTT ──────────────────────────────────────────────────────────────────────
void connect_mqtt() {
    if (mqttClient.connect("dispenser-esp32", MQTT_USER, MQTT_PASS)) {
        Serial.println("[mqtt] connected");
        mqttClient.subscribe("dispenser/command");
        mqttClient.subscribe("dispenser/schedules");
        reconnect_fails = 0;
        push_init_to_mb();
    } else {
        Serial.printf("[mqtt] connect failed, rc=%d\n", mqttClient.state());
    }
}

void reconnect_mqtt() {
    Serial.print("[mqtt] reconnecting...");
    delay(5000);
    if (mqttClient.connect("dispenser-esp32", MQTT_USER, MQTT_PASS)) {
        Serial.println(" reconnected");
        mqttClient.subscribe("dispenser/command");
        mqttClient.subscribe("dispenser/schedules");
        reconnect_fails = 0;
        push_init_to_mb();
    } else {
        reconnect_fails++;
        Serial.printf(" failed (attempt %d)\n", reconnect_fails);
        if (reconnect_fails >= 5) {
            Serial.println("[mqtt] too many failures, rebooting");
            ESP.restart();
        }
    }
}

void mqtt_callback(char* topic, byte* payload, unsigned int length) {
    // Copy payload to null-terminated string
    char buf[512];
    unsigned int len = length < sizeof(buf) - 1 ? length : sizeof(buf) - 1;
    memcpy(buf, payload, len);
    buf[len] = '\0';

    Serial.printf("[mqtt] %s: %s\n", topic, buf);

    if (strcmp(topic, "dispenser/command") == 0) {
        StaticJsonDocument<256> doc;
        if (deserializeJson(doc, buf) != DeserializationError::Ok) return;

        const char* action = doc["action"];
        const char* type   = doc["type"] | "A";

        if (strcmp(action, "dispense") == 0) {
            char line[32];
            snprintf(line, sizeof(line), "DISPENSE:%s", type);
            Serial1.println(line);
        } else if (strcmp(action, "manual") == 0) {
            char line[32];
            snprintf(line, sizeof(line), "MANUAL:%s", type);
            Serial1.println(line);
        } else if (strcmp(action, "set_storage") == 0) {
            int a = doc["a"] | 4;
            int b = doc["b"] | 4;
            char line[32];
            snprintf(line, sizeof(line), "STORAGE_SET:%d,%d", a, b);
            Serial1.println(line);
            prefs.putInt("storage_a", a);
            prefs.putInt("storage_b", b);
        }

    } else if (strcmp(topic, "dispenser/schedules") == 0) {
        // Parse JSON array and build SCHED: line for MB1
        StaticJsonDocument<512> doc;
        if (deserializeJson(doc, buf) != DeserializationError::Ok) return;

        JsonArray arr = doc.as<JsonArray>();
        if (arr.isNull()) return;

        char sched_line[128] = "SCHED:";
        bool first = true;
        for (JsonObject entry : arr) {
            const char* t_time = entry["time"] | "";
            const char* t_type = entry["type"] | "A";
            if (strlen(t_time) != 5) continue;
            if (!first) strncat(sched_line, ",", sizeof(sched_line) - strlen(sched_line) - 1);
            char entry_str[16];
            snprintf(entry_str, sizeof(entry_str), "%s:%s", t_time, t_type);
            strncat(sched_line, entry_str, sizeof(sched_line) - strlen(sched_line) - 1);
            first = false;
        }
        if (!first) {
            Serial1.println(sched_line);
            Serial.printf("[uart] sent: %s\n", sched_line);
        } else {
            Serial1.println("SCHED:");
            Serial.println("[uart] sent: SCHED: (clear)");
        }
    }
}

// ── MB1 communication ─────────────────────────────────────────────────────────
void send_time_to_mb() {
    struct tm t;
    if (!getLocalTime(&t)) return;
    char buf[16];
    strftime(buf, sizeof(buf), "%H:%M:%S", &t);
    Serial1.println(String("TIME:") + buf);
    Serial.printf("[uart] sent TIME:%s\n", buf);
}

void push_init_to_mb() {
    // Push stored storage counts to MB1 on (re)connect via UART only.
    // Do NOT publish to MQTT here — the server's state.json is the source
    // of truth and must not be overwritten by ESP32 NVS defaults.
    int a = prefs.getInt("storage_a", 4);
    int b = prefs.getInt("storage_b", 4);
    char line[32];
    snprintf(line, sizeof(line), "STORAGE_SET:%d,%d", a, b);
    Serial1.println(line);
    Serial.printf("[uart] sent %s\n", line);
}

void read_mb_uart() {
    while (Serial1.available()) {
        char c = Serial1.read();
        if (c == '\n' || c == '\r') {
            if (uart_pos > 0) {
                uart_buf[uart_pos] = '\0';
                handle_mb_line(uart_buf);
                uart_pos = 0;
            }
        } else if (uart_pos < (int)sizeof(uart_buf) - 1) {
            uart_buf[uart_pos++] = c;
        }
    }
}

void handle_mb_line(const char* line) {
    Serial.printf("[uart] recv: %s\n", line);

    if (strncmp(line, "TIME_REQ", 8) == 0) {
        req_received = true;
        last_time_send = 0;   // send immediately on next loop
        Serial.println("[uart] TIME_REQ received, starting time broadcast");

    } else if (strncmp(line, "TIME_ACK", 8) == 0) {
        init_done = true;
        Serial.println("[uart] MB1 time synced");

    } else if (strncmp(line, "SENSOR:", 7) == 0) {
        // SENSOR:temp,humi
        float temp = 0, humi = 0;
        sscanf(line + 7, "%f,%f", &temp, &humi);
        StaticJsonDocument<128> doc;
        doc["temp"] = temp;
        doc["humidity"] = humi;
        doc["ip"] = WiFi.localIP().toString();
        char buf[128];
        serializeJson(doc, buf);
        mqttClient.publish("dispenser/sensor", buf);

    } else if (strncmp(line, "STORAGE:", 8) == 0) {
        // STORAGE:a,b  or  STORAGE:a,b:EMPTY_A  or  STORAGE:a,b:EMPTY_B
        int a = 0, b = 0;
        sscanf(line + 8, "%d,%d", &a, &b);
        prefs.putInt("storage_a", a);
        prefs.putInt("storage_b", b);

        bool empty_a = strstr(line, "EMPTY_A") != nullptr;
        bool empty_b = strstr(line, "EMPTY_B") != nullptr;

        StaticJsonDocument<64> doc;
        doc["a"] = a;
        doc["b"] = b;
        if (empty_a) doc["empty_a"] = true;
        if (empty_b) doc["empty_b"] = true;
        char buf[64];
        serializeJson(doc, buf);
        mqttClient.publish("dispenser/storage", buf);

    } else if (strncmp(line, "DISPENSE_DONE:", 14) == 0) {
        const char* type = line + 14;
        StaticJsonDocument<32> doc;
        doc["type"] = type;
        char buf[32];
        serializeJson(doc, buf);
        mqttClient.publish("dispenser/dispense_done", buf);
    }
}
