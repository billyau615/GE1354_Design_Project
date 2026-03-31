from microbit import uart, pin8, pin16, display, Image, sleep

uart.init(baudrate=9600, tx=pin16, rx=pin8)
sleep(1000)

while True:
    uart.write("PING\n")
    display.show(Image.ARROW_E)

    # Wait up to 2s for PONG
    buf = b''
    for _ in range(200):
        if uart.any():
            buf += uart.read(1)
            if b"\n" in buf:
                break
        sleep(10)

    line = buf.decode("utf-8", "replace").strip()
    if line == "PONG":
        display.show(Image.YES)
    else:
        display.show(Image.NO)

    sleep(2000)
