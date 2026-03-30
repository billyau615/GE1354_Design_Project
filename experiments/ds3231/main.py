from microbit import uart, pin8, pin16, sleep
from ds3231 import read_ds3231, set_ds3231
from oled import init_oled, clear_oled, write_oled

NTP_TIMEOUT_MS = 30000   # 30 seconds to wait for TIME: from ESP32

sleep(2000)
uart.init(baudrate=9600, tx=pin16, rx=pin8)
init_oled()
clear_oled()
write_oled("Waiting NTP...", 0)

# ── Wait for TIME: from ESP32 ──────────────────────────────────────────────────
uart_buf = b''
elapsed = 0
ntp_ok = False

while elapsed < NTP_TIMEOUT_MS:
    if uart.any():
        chunk = uart.read(1)
        if chunk:
            uart_buf += chunk
            if b"\n" in uart_buf:
                idx = uart_buf.find(b"\n")
                line = uart_buf[:idx].decode("utf-8", "replace").strip()
                uart_buf = uart_buf[idx + 1:]
                if line.startswith("TIME:"):
                    body = line[5:]
                    if len(body) == 8 and body[2] == ":" and body[5] == ":":
                        try:
                            h = int(body[0:2])
                            m = int(body[3:5])
                            s = int(body[6:8])
                            set_ds3231(h, m, s)
                            uart.write("TIME_ACK\n")
                            ntp_ok = True
                            break
                        except ValueError:
                            pass
    sleep(50)
    elapsed += 50

# ── Handle NTP failure ─────────────────────────────────────────────────────────
if not ntp_ok:
    clear_oled()
    write_oled("No NTP signal", 0)
    while True:
        sleep(1000)

# ── Main display loop ──────────────────────────────────────────────────────────
clear_oled()
while True:
    h, m, s = read_ds3231()
    if h is None:
        clear_oled()
        write_oled("RTC Error", 0)
    else:
        write_oled("{:02d}:{:02d}:{:02d}".format(h, m, s), 0)
    sleep(1000)
