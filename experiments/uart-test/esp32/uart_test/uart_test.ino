// UART Test — ESP32 side
//
// Receives PING from Micro:bit and replies PONG.
// Open Serial Monitor (115200 baud) to see activity.
//
// Wiring:
//   ESP32 GPIO16 (TX) → Micro:bit P8  (RX)
//   ESP32 GPIO17 (RX) ← Micro:bit P16 (TX)
//   ESP32 GND         — Micro:bit GND

#define MB_RX_PIN 17
#define MB_TX_PIN 16

char buf[32];
int  pos = 0;

void setup() {
    Serial.begin(115200);
    Serial1.begin(9600, SERIAL_8N1, MB_RX_PIN, MB_TX_PIN);
    Serial.println("[ready] Waiting for PING...");
}

void loop() {
    while (Serial1.available()) {
        char c = Serial1.read();
        if (c == '\n' || c == '\r') {
            if (pos > 0) {
                buf[pos] = '\0';
                Serial.printf("[uart] recv: %s\n", buf);
                if (strcmp(buf, "PING") == 0) {
                    Serial1.println("PONG");
                    Serial.println("[uart] sent: PONG");
                }
                pos = 0;
            }
        } else if (pos < (int)sizeof(buf) - 1) {
            buf[pos++] = c;
        }
    }
}
