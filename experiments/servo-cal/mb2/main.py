from microbit import pin0, pin1, display, sleep
import radio

radio.on()
radio.config(group=43)

PERIOD_US = 20000
SERVO_A = pin0
SERVO_B = pin1


def set_servo(pin, us):
    pin.set_analog_period_microseconds(PERIOD_US)
    pin.write_analog(int(us / PERIOD_US * 1023))


display.show("C")

while True:
    msg = radio.receive()
    if msg is not None:
        if msg.startswith("CAL:"):
            parts = msg[4:].split(",")
            if len(parts) == 2:
                try:
                    wheel = parts[0]
                    us = int(parts[1])
                    if wheel == "A":
                        set_servo(SERVO_A, us)
                        display.show("A")
                    elif wheel == "B":
                        set_servo(SERVO_B, us)
                        display.show("B")
                    sleep(300)
                    display.show("C")
                except ValueError:
                    pass
    sleep(50)
