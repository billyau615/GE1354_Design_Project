from microbit import display, sleep
import radio

# Micro:bit #2 — Dispenser actuator
# Receives commands from Micro:bit #1 via radio (group 42)
# Servo control is stubbed until hardware is confirmed

radio.on()
radio.config(group=42)
display.show("2")


def turn_servo_one_slot():
    # TODO: write servo PWM to the assigned pin when wiring is confirmed
    # Example: pin0.write_analog(77)  # ~1ms pulse for 0 degrees
    #          sleep(500)
    #          pin0.write_analog(0)
    pass


while True:
    msg = radio.receive()
    if msg:
        if msg == "DISPENSE:A":
            turn_servo_one_slot()
            radio.send("DONE:A")
        elif msg == "DISPENSE:B":
            turn_servo_one_slot()
            radio.send("DONE:B")
        elif msg == "DISPENSE:AB":
            turn_servo_one_slot()  # type A wheel
            turn_servo_one_slot()  # type B wheel
            radio.send("DONE:AB")
        elif msg == "SERVO_STEP":
            turn_servo_one_slot()
    sleep(50)
