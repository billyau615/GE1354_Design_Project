from microbit import pin0, button_a, button_b, display, sleep

# ── Continuous rotation servo — slot calibration ───────────────────────────────
# PWM for continuous rotation servo:
#   NEUTRAL_US  → servo stopped
#   NEUTRAL_US + offset → rotates (larger offset = faster)
#   NEUTRAL_US - offset → rotates opposite direction
#
# Phase 1 — find neutral (display "n"):
#   B short press  → NEUTRAL_US + 10 (tune until servo fully stops)
#   B long press   → NEUTRAL_US - 10
#   A              → confirm neutral, move to phase 2
#
# Phase 2 — find slot duration (display count):
#   A              → run one slot (DRIVE_US for SLOT_MS, then neutral)
#   B short press  → SLOT_MS + 50ms (more rotation)
#   B long press   → SLOT_MS - 50ms (less rotation)
#   A + B hold     → scroll current SLOT_MS value

NEUTRAL_US = 1500   # tune in phase 1 until servo stops completely
DRIVE_US   = 1600   # rotation speed — increase for faster (1550=slow, 1700=fast)
SLOT_MS    = 500    # duration (ms) for one slot — tune in phase 2
PERIOD_US  = 20000


def set_servo(us):
    duty = int(us / PERIOD_US * 1023)
    pin0.set_analog_period_microseconds(PERIOD_US)
    pin0.write_analog(duty)


def stop():
    set_servo(NEUTRAL_US)


def dispense_one():
    set_servo(DRIVE_US)
    sleep(SLOT_MS)
    stop()


# ── Phase 1: find neutral ──────────────────────────────────────────────────────
stop()
display.show("n")

b_counter = 0
phase = 1

while phase == 1:
    if button_a.was_pressed():
        phase = 2
        break

    if button_b.is_pressed():
        b_counter += 1
    else:
        if b_counter > 0:
            if b_counter < 15:
                NEUTRAL_US += 10
            else:
                NEUTRAL_US -= 10
            stop()  # re-apply updated neutral
            display.scroll(str(NEUTRAL_US), delay=80)
            display.show("n")
        b_counter = 0

    sleep(50)

# ── Phase 2: find slot duration ────────────────────────────────────────────────
# Manually position the wheel to home before pressing A.
stop()
count = 0
display.show("0")
b_counter = 0

while True:
    a = button_a.is_pressed()
    b = button_b.is_pressed()

    if a and b:
        b_counter += 1
        if b_counter >= 20:
            display.scroll(str(SLOT_MS), delay=80)
            display.show(str(count) if count < 10 else "F")
            b_counter = 0
            sleep(400)
    else:
        b_counter = 0

        if button_a.was_pressed() and not button_b.is_pressed():
            count += 1
            display.show(">")
            dispense_one()
            display.show(str(count) if count < 10 else "F")

        if button_b.is_pressed():
            b_counter += 1
        else:
            if b_counter > 0:
                if b_counter < 15:
                    SLOT_MS += 50
                else:
                    SLOT_MS -= 50
                display.scroll(str(SLOT_MS), delay=80)
                display.show(str(count) if count < 10 else "F")
            b_counter = 0

    sleep(50)
