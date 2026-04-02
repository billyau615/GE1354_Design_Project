from microbit import uart, pin8, pin16, display, sleep
import radio

uart.init(baudrate=9600, tx=pin16, rx=pin8)
radio.on()
radio.config(group=43)

uart_buf = b''
display.show("1")

while True:
    while uart.any():
        chunk = uart.read(1)
        if chunk:
            uart_buf += chunk
            if b"\n" in uart_buf:
                idx = uart_buf.find(b"\n")
                line = uart_buf[:idx].decode("utf-8", "replace").strip()
                uart_buf = uart_buf[idx + 1:]
                if line.startswith("CAL:"):
                    radio.send(line)
    sleep(50)
