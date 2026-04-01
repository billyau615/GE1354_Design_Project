from microbit import pin0, button_a, button_b, display, sleep

# Phase 1 (display "H"): find home position (slot 0)
#   A       → +50us (move right)
#   B       → -50us (move left)
#   A+B     → confirm home, go to phase 2
#
# Phase 2 (display "F"): find max position (slot 5)
#   A       → +50us
#   B       → -50us
#   A+B     → confirm max, go to phase 3
#
# Phase 3 (display slot 0-5): test dispensing
#   A       → next slot
#   A+B     → reset to home

PERIOD_US = 20000
SETTLE_MS = 400
current   = 1500   # start at midpoint so we can go either direction


def set_servo(us):
    pin0.set_analog_period_microseconds(PERIOD_US)
    pin0.write_analog(int(us / PERIOD_US * 1023))


def nudge(direction):
    global current
    current += direction * 50
    set_servo(current)
    sleep(SETTLE_MS)
    display.scroll(str(current), delay=60)


# ── Phase 1: find home ────────────────────────────────────────────────────────
set_servo(current)
sleep(SETTLE_MS)
display.show("H")

while True:
    a = button_a.is_pressed()
    b = button_b.is_pressed()
    if a and b:
        sleep(600)
        if button_a.is_pressed() and button_b.is_pressed():
            HOME_US = current
            display.scroll("ok", delay=80)
            break
    elif button_a.was_pressed():
        nudge(+1)
        display.show("H")
    elif button_b.was_pressed():
        nudge(-1)
        display.show("H")
    sleep(50)

# ── Phase 2: find max ─────────────────────────────────────────────────────────
display.show("F")

while True:
    a = button_a.is_pressed()
    b = button_b.is_pressed()
    if a and b:
        sleep(600)
        if button_a.is_pressed() and button_b.is_pressed():
            MAX_US = current
            display.scroll("ok", delay=80)
            break
    elif button_a.was_pressed():
        nudge(+1)
        display.show("F")
    elif button_b.was_pressed():
        nudge(-1)
        display.show("F")
    sleep(50)

# ── Phase 3: test slots 0-5 ───────────────────────────────────────────────────
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
