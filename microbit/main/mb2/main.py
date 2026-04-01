from microbit import pin0, pin1, button_a, button_b, display, Image, sleep
import radio

radio.on()
radio.config(group=42)

# ── Servo config ──────────────────────────────────────────────────────────────
# Adjust OPEN_US / CLOSED_US to match your physical mechanism.
# Standard range: 1000 µs (one end) to 2000 µs (other end).
# Run the button calibration mode to find the right values before full use.

PERIOD_US  = 20000   # 50 Hz
CLOSED_US  = 1000    # pulse width µs for closed/home position
OPEN_US    = 2000    # pulse width µs for open/dispense position
HOLD_MS    = 600     # ms to hold open before returning

SERVO_A = pin0
SERVO_B = pin1


def set_servo(pin, us):
    duty = int(us / PERIOD_US * 1023)
    pin.set_analog_period_microseconds(PERIOD_US)
    pin.write_analog(duty)


def release_servo(pin):
    pin.write_digital(0)


def dispense(pin):
    set_servo(pin, OPEN_US)
    sleep(HOLD_MS)
    set_servo(pin, CLOSED_US)
    sleep(300)
    release_servo(pin)


# ── Startup: home both servos ──────────────────────────────────────────────────
set_servo(SERVO_A, CLOSED_US)
set_servo(SERVO_B, CLOSED_US)
sleep(500)
release_servo(SERVO_A)
release_servo(SERVO_B)
display.show("2")

# ── Main loop ─────────────────────────────────────────────────────────────────
# Button A: manually cycle servo A (calibration)
# Button B: manually cycle servo B (calibration)

while True:
    msg = radio.receive()
    if msg == "DISPENSE:A":
        display.show(Image.ARROW_E)
        dispense(SERVO_A)
        display.show("2")
    elif msg == "DISPENSE:B":
        display.show(Image.ARROW_W)
        dispense(SERVO_B)
        display.show("2")
    elif msg == "DISPENSE:AB":
        display.show(Image.ARROW_E)
        set_servo(SERVO_A, OPEN_US)
        set_servo(SERVO_B, OPEN_US)
        sleep(HOLD_MS)
        set_servo(SERVO_A, CLOSED_US)
        set_servo(SERVO_B, CLOSED_US)
        sleep(300)
        release_servo(SERVO_A)
        release_servo(SERVO_B)
        display.show("2")

    if button_a.was_pressed():
        display.show(Image.ARROW_E)
        dispense(SERVO_A)
        display.show("2")

    if button_b.was_pressed():
        display.show(Image.ARROW_W)
        dispense(SERVO_B)
        display.show("2")

    sleep(50)
