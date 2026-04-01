from microbit import pin0, button_a, button_b, display, sleep

HOME_US   = 500
MAX_US    = 2000
STEPS     = 4
STEP_US   = (MAX_US - HOME_US) // STEPS   # 375us per step
PERIOD_US = 20000
SETTLE_MS = 500

# Slot 0: 500us  Slot 1: 875us  Slot 2: 1250us
# Slot 3: 1625us  Slot 4: 2000us

def set_servo(us):
    pin0.set_analog_period_microseconds(PERIOD_US)
    pin0.write_analog(int(us / PERIOD_US * 1023))


slot = 0
set_servo(HOME_US)
sleep(SETTLE_MS)
display.show("0")

while True:
    if button_a.is_pressed() and button_b.is_pressed():
        slot = 0
        set_servo(HOME_US)
        sleep(SETTLE_MS)
        display.show("0")
        sleep(800)
    elif button_a.was_pressed():
        if slot < STEPS:
            slot += 1
            set_servo(HOME_US + slot * STEP_US)
            sleep(SETTLE_MS)
            display.show(str(slot))
    sleep(50)
