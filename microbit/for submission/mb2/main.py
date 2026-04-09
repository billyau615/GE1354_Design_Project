from microbit import pin0, pin1, display, Image, sleep
import radio

# Initialise radio
radio.on()
radio.config(group=42)

# set PWM servo positions 
SLOTS_A=[500, 900, 1400, 1900, 2400]
SLOTS_B=  [500, 970, 1450, 1970, 2450]
MAX_SLOTS=4
PERIOD_US=20000

#set initial slot count

slot_a = 0
slot_b = 0

# set servo position based on slot count
def set_servo(pin, servo_us):
    pin.set_analog_period_microseconds(PERIOD_US)
    pin.write_analog(int(servo_us/PERIOD_US *  1023))


display.show("2")

# Main loop
while True:
    
    received = radio.receive()
    if received is not None:

        # init
        if received.startswith("INIT:"):

            parts = received[5:].split(",")
            
            if len(parts) == 2:

                    slot_a=int(parts[0])
                    slot_b=int(parts[1])
                    set_servo(pin0, SLOTS_A[slot_a])
                    set_servo(pin1, SLOTS_B[slot_b])

        # dispense
        elif received == "DISPENSE:A":
            if slot_a> 0:
                slot_a =slot_a - 1
                set_servo(pin0, SLOTS_A[slot_a])
                display.show(Image.ARROW_E)
            # if there is no meds left shows a cross
            else:
                display.show(Image.NO)
            sleep(500)
            display.show("2")
        
        elif received == "DISPENSE:B":
            if slot_b > 0:
                slot_b=slot_b - 1
                set_servo(pin1, SLOTS_B[slot_b])
                display.show(Image.ARROW_W)
            # if there is no meds left shows a cross
            else:
                display.show(Image.NO)
            sleep(500)
            display.show("2")
        
        elif received == "DISPENSE:AB":
            successful = False
            if slot_a > 0:
                slot_a = slot_a - 1
                set_servo(pin0, SLOTS_A[slot_a])
                successful = True
            if slot_b > 0:
                slot_b = slot_b - 1
                set_servo(pin1, SLOTS_B[slot_b])
                successful = True
            if successful:
                display.show(Image.ARROW_E)
            else:
                display.show(Image.NO)
            sleep(500)
            display.show("2")
        
        # refill 
        elif received == "REFILL:A":
            slot_a = 0
            set_servo(pin0, SLOTS_A[0])

        elif received == "REFILL:B":
            slot_b = 0
            set_servo(pin1, SLOTS_B[0])

        elif received == "SERVO_STEP:A":
            if slot_a <MAX_SLOTS:
                slot_a = slot_a + 1
                set_servo(pin0, SLOTS_A[slot_a])

        elif received == "SERVO_STEP:B":
            if slot_b < MAX_SLOTS:
                slot_b = slot_b + 1
                set_servo(pin1, SLOTS_B[slot_b])

    sleep(50)
