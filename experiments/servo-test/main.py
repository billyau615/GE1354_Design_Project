from microbit import pin0, button_a, button_b, display, sleep

# ── Servo calibration experiment ───────────────────────────────────────────────
# 8-slot rotary dispenser: each pill = 45 degrees of rotation
#
# Controls:
#   Button A       → step forward one slot (45 deg)
#   Button B       → step backward one slot (45 deg)
#   A + B (hold)   → reset to slot 0 (home position)
#
# Tune these two values until one button press drops exactly one pill:
#   US_PER_DEG  — microseconds per degree (start at 1000/180 ≈ 5.56)
#   HOME_US     — pulse width for the home/starting position
#
# Typical servo range: 1000 µs = 0°, 2000 µs = 180°
# so US_PER_DEG = 1000 / 180 ≈ 5.56  (adjust if your servo differs)

HOME_US    = 1000     # pulse width (µs) for slot 0 — tune this
US_PER_DEG = 5.56     # µs per degree — tune if steps feel too big/small
STEP_DEG   = 45       # degrees per slot (360 / 8 slots)
PERIOD_US  = 20000    # 50 Hz servo signal — do not change
SETTLE_MS  = 400      # ms to wait after moving before releasing PWM

STEP_US = int(STEP_DEG * US_PER_DEG)   # µs per one slot step

slot = 0   # current slot index (0 = home)


def set_servo(us):
    duty = int(us / PERIOD_US * 1023)
    pin0.set_analog_period_microseconds(PERIOD_US)
    pin0.write_analog(duty)


def release():
    pin0.write_digital(0)


def go_to_slot(n):
    us = HOME_US + n * STEP_US
    set_servo(us)
    sleep(SETTLE_MS)
    release()


# Home on startup
go_to_slot(0)
display.show("0")

while True:
    a = button_a.is_pressed()
    b = button_b.is_pressed()

    if a and b:
        # Reset to home
        slot = 0
        go_to_slot(slot)
        display.show("0")
        sleep(600)

    elif button_a.was_pressed():
        slot += 1
        go_to_slot(slot)
        display.show(str(slot) if slot < 10 else "+")

    elif button_b.was_pressed():
        if slot > 0:
            slot -= 1
        go_to_slot(slot)
        display.show(str(slot) if slot < 10 else "+")

    sleep(50)
