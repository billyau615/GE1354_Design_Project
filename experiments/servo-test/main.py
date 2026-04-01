from microbit import pin0, button_a, button_b, display, sleep

HOME_US   = 1000          # 0 degrees — home position
STEP_US   = 200           # (2000-1000) / 5 slots = 200us per slot
MAX_SLOTS = 5
PERIOD_US = 20000
SETTLE_MS = 400


def set_servo(us):
    pin0.set_analog_period_microseconds(PERIOD_US)
    pin0.write_analog(int(us / PERIOD_US * 1023))


def go(slot):
    set_servo(HOME_US + slot * STEP_US)
    sleep(SETTLE_MS)


slot = 0
go(0)
display.show("0")

while True:
    if button_a.is_pressed() and button_b.is_pressed():
        slot = 0
        go(0)
        display.show("0")
        sleep(800)
    elif button_a.was_pressed():
        if slot < MAX_SLOTS:
            slot += 1
            go(slot)
            display.show(str(slot))
    sleep(50)
