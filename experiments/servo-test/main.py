from microbit import pin0, button_a, display, sleep

NEUTRAL_US = 1500   # stopped — adjust if servo creeps when idle
DRIVE_US   = 1600   # rotation speed/direction (try 1400 if wrong direction)
SLOT_MS    = 500    # how long to spin per slot — adjust until one slot advances
PERIOD_US  = 20000


def set_servo(us):
    pin0.set_analog_period_microseconds(PERIOD_US)
    pin0.write_analog(int(us / PERIOD_US * 1023))


set_servo(NEUTRAL_US)
display.show("G")

count = 0
while True:
    if button_a.was_pressed():
        count += 1
        display.show(">")
        set_servo(DRIVE_US)
        sleep(SLOT_MS)
        set_servo(NEUTRAL_US)
        display.show(str(count) if count < 10 else "F")
    sleep(50)
