from microbit import pin0, button_a, button_b, display, sleep

# ── Servo calibration experiment ───────────────────────────────────────────────
# 8-slot rotary dispenser: each pill = 45 degrees of rotation
#
# Controls:
#   Button A            → step forward one slot
#   Button B            → step backward one slot
#   A + B (hold 1s)     → reset to slot 0 (home)
#
# HOME_US is set to 1500 (servo midpoint) to avoid the non-linear zone
# near the 1000 µs extreme where the same µs = more physical degrees.
# Adjust STEP_US if one step doesn't equal exactly one slot.

HOME_US   = 1500    # midpoint of servo range — adjust to align slot 0
STEP_US   = 250     # µs per slot (45 deg). increase = bigger step
PERIOD_US = 20000   # 50 Hz — do not change
SETTLE_MS = 500     # ms to wait for servo to reach position

slot = 0


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


go_to_slot(0)
display.show("0")

ab_timer = 0

while True:
    a = button_a.is_pressed()
    b = button_b.is_pressed()

    if a and b:
        ab_timer += 1
        if ab_timer >= 20:  # held for ~1 second
            slot = 0
            go_to_slot(slot)
            display.show("0")
            ab_timer = 0
            sleep(600)
    else:
        ab_timer = 0
        if button_a.was_pressed():
            slot += 1
            go_to_slot(slot)
            display.show(str(slot) if slot < 10 else "+")
        elif button_b.was_pressed():
            if slot > 0:
                slot -= 1
            go_to_slot(slot)
            display.show(str(slot) if slot < 10 else "+")

    sleep(50)
