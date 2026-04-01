from microbit import pin0, button_a, button_b, display, sleep

# Phase 1 (display "F"): find true max pulse width
#   Button A → increase pulse by 50us and move there
#   Button B → decrease pulse by 50us
#   A + B    → confirm max, move to phase 2
#
# Phase 2 (display slot number): 5-slot dispense test
#   Button A → advance one slot
#   A + B    → reset to home

PERIOD_US = 20000
HOME_US   = 1000
current   = 2000   # start from where we left off, find true max
SETTLE_MS = 400


def set_servo(us):
    pin0.set_analog_period_microseconds(PERIOD_US)
    pin0.write_analog(int(us / PERIOD_US * 1023))


# ── Phase 1: find max ──────────────────────────────────────────────────────────
set_servo(current)
sleep(SETTLE_MS)
display.show("F")

while True:
    a = button_a.is_pressed()
    b = button_b.is_pressed()

    if a and b:
        sleep(600)
        if button_a.is_pressed() and button_b.is_pressed():
            MAX_US = current
            display.scroll(str(MAX_US), delay=80)
            break

    elif button_a.was_pressed():
        current += 50
        set_servo(current)
        sleep(SETTLE_MS)
        display.scroll(str(current), delay=60)
        display.show("F")

    elif button_b.was_pressed():
        current -= 50
        set_servo(current)
        sleep(SETTLE_MS)
        display.scroll(str(current), delay=60)
        display.show("F")

    sleep(50)

# ── Phase 2: 5-slot test ───────────────────────────────────────────────────────
STEP_US = (MAX_US - HOME_US) // 5

slot = 0
set_servo(HOME_US)
sleep(SETTLE_MS)
display.show("0")

while True:
    a = button_a.is_pressed()
    b = button_b.is_pressed()

    if a and b:
        slot = 0
        set_servo(HOME_US)
        sleep(SETTLE_MS)
        display.show("0")
        sleep(800)
    elif button_a.was_pressed():
        if slot < 5:
            slot += 1
            set_servo(HOME_US + slot * STEP_US)
            sleep(SETTLE_MS)
            display.show(str(slot))
    sleep(50)
