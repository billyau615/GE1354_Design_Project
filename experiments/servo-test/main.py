from microbit import pin0, button_a, button_b, display, sleep

# Phase 1 (display "F"): find true max pulse width
#   A       → +50us
#   B       → -50us
#   A+B     → confirm, go to phase 2
#
# Phase 2 (display slot 1-5): 5-slot dispense test
#   A       → advance to next slot
#   B short → STEP_US +10 (fix if overshooting)
#   B long  → STEP_US -10 (fix if undershooting)
#   A+B     → reset to slot 1

PERIOD_US = 20000
HOME_US   = 1000
SETTLE_MS = 400
current   = 2000


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

# ── Phase 2: slots 1-5 ────────────────────────────────────────────────────────
# home=0, 5 slots, 5 intervals: slot0=HOME, slot5=MAX
STEP_US = (MAX_US - HOME_US) // 5

slot = 0
set_servo(HOME_US)
sleep(SETTLE_MS)
display.show("0")

b_counter = 0

while True:
    a = button_a.is_pressed()
    b = button_b.is_pressed()

    if a and b:
        slot = 0
        set_servo(HOME_US)
        sleep(SETTLE_MS)
        display.show("0")
        sleep(800)
    else:
        if button_a.was_pressed():
            if slot < 5:
                slot += 1
                set_servo(HOME_US + slot * STEP_US)
                sleep(SETTLE_MS)
                display.show(str(slot))

        if button_b.is_pressed():
            b_counter += 1
        else:
            if b_counter > 0:
                if b_counter < 15:
                    STEP_US += 10
                else:
                    STEP_US -= 10
                display.scroll(str(STEP_US), delay=70)
                display.show(str(slot))
            b_counter = 0

    sleep(50)
