// Servo Calibration Experiment
// Subscribes to MQTT topic dispenser/cal and forwards pulse width commands to MB1.
//
// MQTT payload: {"wheel": "A", "us": 1250}
//   wheel — "A" or "B"
//   us    — pulse width in microseconds (500–2500)
//
// Send example (mosquitto_pub):
//   mosquitto_pub -h <broker> -u <user> -P <pass> -t dispenser/cal -m '{"wheel":"A","us":1250}'
//
// Wiring (same as main project):
//   ESP32 GPIO17 (RX) ← Micro:bit P16 (TX)
//   ESP32 GPIO16 (TX) → Micro:bit P8  (RX)

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// ── Configuration ─────────────────────────────────────────────────────────────
const char* WIFI_SSID = "YOUR_WIFI_SSID";   // fill in
const char* WIFI_PASS = "YOUR_WIFI_PASSWORD";   // fill in
const char* MQTT_HOST = "YOUR_MQTT_HOST";   // fill in (e.g. "192.168.1.100")
const int   MQTT_PORT = 1883;
const char* MQTT_USER = "YOUR_MQTT_USER";   // fill in
const char* MQTT_PASS = "YOUR_MQTT_PASSWORD";   // fill in

#define MB_RX_PIN 17
#define MB_TX_PIN 16

// ── Globals ───────────────────────────────────────────────────────────────────
WiFiClient   wifiClient;
PubSubClient mqttClient(wifiClient);

// ── MQTT callback ─────────────────────────────────────────────────────────────
void mqtt_callback(char* topic, byte* payload, unsigned int length) {
    char buf[128];
    unsigned int len = length < sizeof(buf) - 1 ? length : sizeof(buf) - 1;
    memcpy(buf, payload, len);
    buf[len] = '\0';

    Serial.printf("[mqtt] %s: %s\n", topic, buf);

    StaticJsonDocument<128> doc;
    if (deserializeJson(doc, buf) != DeserializationError::Ok) return;

    const char* wheel = doc["wheel"] | "";
    int us = doc["us"] | 0;

    if ((strcmp(wheel, "A") == 0 || strcmp(wheel, "B") == 0)
            && us >= 500 && us <= 2500) {
        char line[32];
        snprintf(line, sizeof(line), "CAL:%s,%d", wheel, us);
        Serial1.println(line);
        Serial.printf("[uart] sent: %s\n", line);
    } else {
        Serial.println("[mqtt] ignored: invalid wheel or us out of range (500-2500)");
    }
}

// ── MQTT connect ──────────────────────────────────────────────────────────────
void connect_mqtt() {
    while (!mqttClient.connected()) {
        Serial.print("[mqtt] connecting...");
        if (mqttClient.connect("servo-cal-esp32", MQTT_USER, MQTT_PASS)) {
            Serial.println(" connected");
            mqttClient.subscribe("dispenser/cal");
            Serial.println("[mqtt] subscribed to dispenser/cal");
        } else {
            Serial.printf(" failed rc=%d, retry in 5s\n", mqttClient.state());
            delay(5000);
        }
    }
}

// ── Setup ─────────────────────────────────────────────────────────────────────
void setup() {
    Serial.begin(115200);
    Serial1.begin(9600, SERIAL_8N1, MB_RX_PIN, MB_TX_PIN);

    Serial.print("[wifi] connecting");
    WiFi.begin(WIFI_SSID, WIFI_PASS);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.printf(" connected, IP=%s\n", WiFi.localIP().toString().c_str());

    mqttClient.setServer(MQTT_HOST, MQTT_PORT);
    mqttClient.setCallback(mqtt_callback);
    connect_mqtt();
}

// ── Loop ──────────────────────────────────────────────────────────────────────
void loop() {
    if (!mqttClient.connected()) connect_mqtt();
    mqttClient.loop();
}
