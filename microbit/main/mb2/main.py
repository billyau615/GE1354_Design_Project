from microbit import display, Image, sleep
import radio

# Micro:bit #2 — Dispenser actuator
# Receives commands from Micro:bit #1 via radio (group 42)
# Servo control is stubbed until hardware arrives.
# Received commands are shown on the LED matrix for testing.

radio.on()
radio.config(group=42)
display.show("2")


while True:
    msg = radio.receive()
    if msg:
        if msg == "DISPENSE:A":
            display.scroll("A", delay=80)
            radio.send("DONE:A")
        elif msg == "DISPENSE:B":
            display.scroll("B", delay=80)
            radio.send("DONE:B")
        elif msg == "DISPENSE:AB":
            display.scroll("AB", delay=80)
            radio.send("DONE:AB")
        elif msg == "SERVO_STEP":
            display.show(Image.ARROW_E)
            sleep(500)
        display.show("2")
    sleep(50)
