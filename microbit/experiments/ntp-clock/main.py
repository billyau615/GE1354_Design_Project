from microbit import uart, pin0, pin8, pin16, sleep
from oled import init_oled, clear_oled, write_oled
import music

# UART: Micro:bit P16 (TX) → ESP32 GPIO11, Micro:bit P8 (RX) ← ESP32 GPIO12
uart.init(baudrate=9600, tx=pin16, rx=pin8)

sleep(2000)
init_oled()
clear_oled()
write_oled("Waiting NTP...", 0)

last_sec = -1

while True:
    line = uart.readline()
    if line:
        try:
            text = line.decode('utf-8').strip()
            # Expected format from ESP32: "2026-03-29 14:30:05"
            if len(text) == 19:
                date_part = text[:10]   # "2026-03-29"
                time_part = text[11:]   # "14:30:05"
                sec = int(text[17:19])

                clear_oled()
                write_oled(date_part, 0)
                write_oled(time_part, 1)

                # Beep once at the start of every minute
                if sec == 0 and sec != last_sec:
                    music.pitch(880, 200, pin=pin0)

                last_sec = sec
        except:
            pass
