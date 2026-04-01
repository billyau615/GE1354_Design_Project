from microbit import pin0, button_a, button_b, display, sleep

# Find min and max pulse width for your servo.
# A = increase pulse (move one direction)
# B = decrease pulse (move other direction)
# Scroll shows current pulse width after each press.

PERIOD_US = 20000
pos = 1500


def set_servo(us):
    pin0.set_analog_period_microseconds(PERIOD_US)
    pin0.write_analog(int(us / PERIOD_US * 1023))


set_servo(pos)
display.scroll(str(pos), delay=60)

while True:
    if button_a.was_pressed():
        pos += 50
        set_servo(pos)
        display.scroll(str(pos), delay=60)
    elif button_b.was_pressed():
        pos -= 50
        set_servo(pos)
        display.scroll(str(pos), delay=60)
    sleep(50)
