from microbit import pin0, pin1, sleep
import music

# FC-51 IR obstacle sensor on P1
# OUT = LOW (0) when obstacle detected, HIGH (1) when clear
# Passive buzzer on P0

while True:
    if pin1.read_digital() == 0:  # obstacle detected
        music.pitch(1000, 100, pin=pin0)
    sleep(50)
