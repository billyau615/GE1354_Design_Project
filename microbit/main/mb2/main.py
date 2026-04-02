from microbit import pin0, pin1, display, Image, sleep
import radio

radio.on()
radio.config(group=42)

HOME_US   = 500
STEP_US   = 500
MAX_SLOTS = 4
PERIOD_US = 20000

SERVO_A = pin0
SERVO_B = pin1

slot_a = 0
slot_b = 0


def set_servo(pin, us):
    pin.set_analog_period_microseconds(PERIOD_US)
    pin.write_analog(int(us / PERIOD_US * 1023))


display.show("2")

while True:
    msg = radio.receive()
    if msg is not None:
        if msg.startswith("INIT:"):
            parts = msg[5:].split(",")
            if len(parts) == 2:
                try:
                    a = int(parts[0])
                    b = int(parts[1])
                    slot_a = a
                    slot_b = b
                    set_servo(SERVO_A, HOME_US + slot_a * STEP_US)
                    set_servo(SERVO_B, HOME_US + slot_b * STEP_US)
                except ValueError:
                    pass
        elif msg == "DISPENSE:A":
            if slot_a > 0:
                slot_a -= 1
                set_servo(SERVO_A, HOME_US + slot_a * STEP_US)
                display.show(Image.ARROW_E)
            else:
                display.show(Image.NO)
            sleep(500)
            display.show("2")
        elif msg == "DISPENSE:B":
            if slot_b > 0:
                slot_b -= 1
                set_servo(SERVO_B, HOME_US + slot_b * STEP_US)
                display.show(Image.ARROW_W)
            else:
                display.show(Image.NO)
            sleep(500)
            display.show("2")
        elif msg == "DISPENSE:AB":
            moved = False
            if slot_a > 0:
                slot_a -= 1
                set_servo(SERVO_A, HOME_US + slot_a * STEP_US)
                moved = True
            if slot_b > 0:
                slot_b -= 1
                set_servo(SERVO_B, HOME_US + slot_b * STEP_US)
                moved = True
            display.show(Image.ARROW_E if moved else Image.NO)
            sleep(500)
            display.show("2")
        elif msg == "REFILL:A":
            slot_a = 0
            set_servo(SERVO_A, HOME_US)
        elif msg == "REFILL:B":
            slot_b = 0
            set_servo(SERVO_B, HOME_US)
        elif msg == "SERVO_STEP:A":
            if slot_a < MAX_SLOTS:
                slot_a += 1
                set_servo(SERVO_A, HOME_US + slot_a * STEP_US)
        elif msg == "SERVO_STEP:B":
            if slot_b < MAX_SLOTS:
                slot_b += 1
                set_servo(SERVO_B, HOME_US + slot_b * STEP_US)

    sleep(50)
