from microbit import uart, pin8, pin16, display, sleep

uart.init(baudrate=9600, tx=pin16, rx=pin8)
sleep(1000)

display.show('W')  # Waiting

buf = b''
while True:
    if uart.any():
        chunk = uart.read(1)
        if chunk:
            buf += chunk
        display.show('R')  # Receiving data
        if b'\n' in buf:
            display.scroll(buf.decode('utf-8', 'replace').strip()[:8])
            buf = b''
    else:
        sleep(50)
