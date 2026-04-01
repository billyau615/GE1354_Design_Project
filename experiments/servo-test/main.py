from microbit import pin0, button_a, button_b, display, sleep

# ── Servo calibration — ratchet style ─────────────────────────────────────────
# Each dispense: servo pushes wheel one slot forward then returns home.
# The wheel must hold position on its own (friction/gravity) when servo returns.
#
# Tune:
#   HOME_US  — resting position. Adjust until wheel sits correctly between slots.
#   STEP_US  — how far to push. Increase until exactly one slot advances per press.
#
# Controls:
#   Button A            → one dispense cycle (home → push → home)
#   Button B (short)    → nudge HOME_US by +10 µs (shift resting position)
#   Button B (hold 1s)  → nudge HOME_US by -10 µs
#   A + B (hold 1s)     → print current HOME_US and STEP_US to display

HOME_US   = 1400    # resting pulse width (µs)
STEP_US   = 500     # push distance (µs) for 45 deg
HOLD_MS   = 400     # ms to hold at pushed position before returning
SETTLE_MS = 400     # ms to wait after each servo move
PERIOD_US = 20000   # 50 Hz — do not change


def set_servo(us):
    duty = int(us / PERIOD_US * 1023)
    pin0.set_analog_period_microseconds(PERIOD_US)
    pin0.write_analog(duty)


def dispense():
    set_servo(HOME_US + STEP_US)
    sleep(HOLD_MS)
    set_servo(HOME_US)
    sleep(SETTLE_MS)


# Go to home on startup
set_servo(HOME_US)
sleep(SETTLE_MS)
display.show("H")

b_counter = 0
count = 0

while True:
    if button_a.was_pressed() and not button_b.is_pressed():
        count += 1
        display.show(">")
        dispense()
        display.show(str(count) if count < 10 else "F")

    if button_b.is_pressed():
        b_counter += 1
    else:
        if b_counter > 0:
            # released — short press = forward, long press = backward
            if b_counter < 15:
                HOME_US += 50
            else:
                HOME_US -= 50
            set_servo(HOME_US)
            sleep(SETTLE_MS)
            display.scroll(str(HOME_US), delay=80)
            display.show("H")
        b_counter = 0

    sleep(50)
