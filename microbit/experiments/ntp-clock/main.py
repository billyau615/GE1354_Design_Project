from microbit import uart, pin0, pin8, pin16, sleep
from oled import init_oled, clear_oled, write_oled
import music

# UART: Micro:bit P16 (TX) → ESP32 GPIO17, Micro:bit P8 (RX) ← ESP32 GPIO16
uart.init(baudrate=9600, tx=pin16, rx=pin8)

sleep(2000)
init_oled()
clear_oled()
write_oled("Waiting NTP...", 0)

# Wait for a single HH:MM:SS line from ESP32
line = None
while not line:
    line = uart.readline()

text = line.decode('utf-8').strip()
h = int(text[0:2])
m = int(text[3:5])
s = int(text[6:8])

clear_oled()

# Run clock independently on Micro:bit
while True:
    write_oled("{:02d}:{:02d}:{:02d}".format(h, m, s), 0)

    if s == 0:
        music.pitch(880, 200, pin=pin0)

    sleep(1000)

    s += 1
    if s >= 60:
        s = 0
        m += 1
        if m >= 60:
            m = 0
            h += 1
            if h >= 24:
                h = 0
