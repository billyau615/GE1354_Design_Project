from microbit import uart, pin0, pin1, pin8, pin16, button_a, button_b, display, sleep, Image
import radio
import music
from oled import init_oled, write_oled, clear_oled
from dht20 import read_dht20
from ds3231 import read_ds3231, set_ds3231

# ── UART & Radio init ─────────────────────────────────────────────────────────
radio.on()
radio.config(group=42)
uart.init(baudrate=9600, tx=pin16, rx=pin8)

# ── State ─────────────────────────────────────────────────────────────────────
h = 0; m = 0; s = 0
schedules = []      # list of (hh, mm, type_str) e.g. (14, 30, "A")
storage_a = 7
storage_b = 7
dispensed_this_minute = False
sensor_timer = 0    # count down to next DHT20 read
last_humi = None
last_temp = None
uart_buf = b''
prev_m = -1

# Long-press tracking
a_pressed_since = 0
b_pressed_since = 0
LONG_PRESS_MS = 1000

# ── Helpers ───────────────────────────────────────────────────────────────────

def send_uart(msg):
    uart.write(msg + "\n")

def parse_sched_line(line):
    # "SCHED:14:30:A,15:00:B,16:00:AB"
    global schedules
    body = line[6:]  # after "SCHED:"
    schedules = []
    for part in body.split(","):
        part = part.strip()
        # part = "14:30:A" or "14:30:AB"
        # find last colon to split time from type
        idx = part.rfind(":")
        if idx < 3:
            continue
        time_str = part[:idx]   # "14:30"
        type_str = part[idx+1:] # "A", "B", or "AB"
        if len(time_str) == 5 and time_str[2] == ":":
            try:
                sh = int(time_str[0:2])
                sm = int(time_str[3:5])
                schedules.append((sh, sm, type_str))
            except ValueError:
                pass

def parse_uart_line(line):
    global h, m, s, storage_a, storage_b
    if line.startswith("TIME:"):
        body = line[5:]
        if len(body) == 8 and body[2] == ":" and body[5] == ":":
            try:
                h = int(body[0:2])
                m = int(body[3:5])
                s = int(body[6:8])
                set_ds3231(h, m, s)
                send_uart("TIME_ACK")
            except ValueError:
                pass
    elif line.startswith("SCHED:"):
        parse_sched_line(line)
    elif line.startswith("STORAGE_SET:"):
        body = line[12:]
        parts = body.split(",")
        if len(parts) == 2:
            try:
                storage_a = int(parts[0])
                storage_b = int(parts[1])
            except ValueError:
                pass
    elif line.startswith("DISPENSE:"):
        do_dispense(line[9:])

def read_uart():
    global uart_buf
    while uart.any():
        chunk = uart.read(1)
        if chunk:
            uart_buf += chunk
            if b"\n" in uart_buf:
                idx = uart_buf.find(b"\n")
                line = uart_buf[:idx].decode("utf-8", "replace").strip()
                uart_buf = uart_buf[idx+1:]
                if line:
                    parse_uart_line(line)

def do_dispense(type_str):
    global storage_a, storage_b
    type_str = type_str.strip()

    # Check stock
    if type_str == "A" or type_str == "AB":
        if storage_a == 0:
            send_uart("STORAGE:0,{}:EMPTY_A".format(storage_b))
            return
    if type_str == "B" or type_str == "AB":
        if storage_b == 0:
            send_uart("STORAGE:{},0:EMPTY_B".format(storage_a))
            return

    # Alarm
    music.pitch(880, 200, pin=pin0)
    sleep(100)
    music.pitch(1100, 200, pin=pin0)
    sleep(100)
    music.pitch(880, 200, pin=pin0)

    # Send to MB2 via radio (stubbed until MB2 is ready)
    radio.send("DISPENSE:" + type_str)
    # Wait for ACK up to 5 seconds
    # radio.receive() is non-blocking; poll for ~5s
    # TODO: uncomment when MB2 is ready
    # ack_wait = 0
    # while ack_wait < 50:
    #     msg = radio.receive()
    #     if msg and msg.startswith("DONE:"):
    #         break
    #     sleep(100)
    #     ack_wait += 1

    # Decrement storage
    empty_flag = ""
    if type_str == "A" or type_str == "AB":
        storage_a -= 1
        if storage_a == 0:
            empty_flag += ":EMPTY_A"
    if type_str == "B" or type_str == "AB":
        storage_b -= 1
        if storage_b == 0:
            empty_flag += ":EMPTY_B"

    send_uart("STORAGE:{},{}{}".format(storage_a, storage_b, empty_flag))
    send_uart("DISPENSE_DONE:" + type_str)

def check_schedules():
    global dispensed_this_minute
    if dispensed_this_minute:
        return
    for (sh, sm, type_str) in schedules:
        if sh == h and sm == m:
            dispensed_this_minute = True
            do_dispense(type_str)
            break

def compute_countdown():
    now_mins = h * 60 + m
    min_delta = None
    for (sh, sm, _) in schedules:
        sched_mins = sh * 60 + sm
        delta = (sched_mins - now_mins) % (24 * 60)
        if min_delta is None or delta < min_delta:
            min_delta = delta
    if min_delta is None:
        return "No sched"
    return "{:02d}:{:02d}".format(min_delta // 60, min_delta % 60)

def read_sensors():
    global last_humi, last_temp
    humi, temp = read_dht20()
    if humi is not None:
        last_humi = humi
        last_temp = temp
        send_uart("SENSOR:{},{}".format(temp, humi))

def update_oled():
    write_oled("{:02d}:{:02d}:{:02d}".format(h, m, s), 0)
    if last_humi is not None:
        write_oled("H:{:.1f}% T:{:.1f}C".format(last_humi, last_temp), 1)
    else:
        write_oled("Sensor...", 1)
    write_oled("Next:" + compute_countdown(), 2)

def enter_refill_mode(type_str):
    global storage_a, storage_b

    current = storage_a if type_str == "A" else storage_b

    # If pills remain, ask to confirm reset
    if current > 0:
        clear_oled()
        write_oled("{} has {} left".format(type_str, current), 0)
        write_oled("A=reset B=cancel", 1)
        # Wait for button press
        while True:
            if button_a.was_pressed():
                if type_str == "A":
                    storage_a = 0
                else:
                    storage_b = 0
                current = 0
                break
            if button_b.was_pressed():
                return  # cancel
            sleep(50)

    # Refill loop
    slot_count = 0
    clear_oled()
    write_oled("Refill " + type_str, 0)
    display.show(str(slot_count))

    while slot_count < 7:
        if type_str == "A":
            pressed = button_a.was_pressed()
            exit_pressed = button_b.was_pressed()
        else:
            pressed = button_b.was_pressed()
            exit_pressed = button_a.was_pressed()

        if pressed:
            # TODO: radio.send("SERVO_STEP") when MB2 ready
            slot_count += 1
            display.show(str(slot_count))
        if exit_pressed:
            break
        sleep(50)

    # Save count
    if type_str == "A":
        storage_a = slot_count
    else:
        storage_b = slot_count

    send_uart("STORAGE:{},{}".format(storage_a, storage_b))
    display.clear()
    clear_oled()

def check_long_press():
    global a_pressed_since, b_pressed_since
    # button.is_pressed() is continuous hold, was_pressed() is edge
    # We track how long the button stays held via loop counter
    if button_a.is_pressed():
        a_pressed_since += 1
        if a_pressed_since == LONG_PRESS_MS // 1000 + 1:
            enter_refill_mode("A")
            a_pressed_since = 0
    else:
        a_pressed_since = 0

    if button_b.is_pressed():
        b_pressed_since += 1
        if b_pressed_since == LONG_PRESS_MS // 1000 + 1:
            enter_refill_mode("B")
            b_pressed_since = 0
    else:
        b_pressed_since = 0

# ── Boot sequence ─────────────────────────────────────────────────────────────
sleep(2000)
init_oled()
clear_oled()
display.show(Image.CLOCK12)

# Always sync DS3231 from ESP32 NTP on every boot
write_oled("Waiting NTP...", 0)
while True:
    if uart.any():
        chunk = uart.read(1)
        if chunk:
            uart_buf += chunk
            if b"\n" in uart_buf:
                idx = uart_buf.find(b"\n")
                line = uart_buf[:idx].decode("utf-8", "replace").strip()
                uart_buf = uart_buf[idx+1:]
                if line.startswith("TIME:"):
                    body = line[5:]
                    if len(body) == 8 and body[2] == ":" and body[5] == ":":
                        try:
                            h = int(body[0:2])
                            m = int(body[3:5])
                            s = int(body[6:8])
                            set_ds3231(h, m, s)    # write NTP time to RTC
                            send_uart("TIME_ACK")
                            break
                        except ValueError:
                            pass

# Non-blocking poll for SCHED: (up to 3 seconds)
for _ in range(300):
    if uart.any():
        chunk = uart.read(1)
        if chunk:
            uart_buf += chunk
            if b"\n" in uart_buf:
                idx = uart_buf.find(b"\n")
                line = uart_buf[:idx].decode("utf-8", "replace").strip()
                uart_buf = uart_buf[idx+1:]
                if line.startswith("SCHED:"):
                    parse_sched_line(line)
                    break
    sleep(10)

# Non-blocking poll for STORAGE_SET: (up to 3 seconds)
for _ in range(300):
    if uart.any():
        chunk = uart.read(1)
        if chunk:
            uart_buf += chunk
            if b"\n" in uart_buf:
                idx = uart_buf.find(b"\n")
                line = uart_buf[:idx].decode("utf-8", "replace").strip()
                uart_buf = uart_buf[idx+1:]
                if line.startswith("STORAGE_SET:"):
                    parts = line[12:].split(",")
                    if len(parts) == 2:
                        try:
                            storage_a = int(parts[0])
                            storage_b = int(parts[1])
                        except ValueError:
                            pass
                    break
    sleep(10)

display.clear()
clear_oled()
read_sensors()
sensor_timer = 30

# ── Main loop ─────────────────────────────────────────────────────────────────
while True:
    read_uart()
    check_long_press()

    rh, rm, rs = read_ds3231()
    if rh is not None:
        h, m, s = rh, rm, rs
        if m != prev_m:
            dispensed_this_minute = False
            prev_m = m
            check_schedules()

    sensor_timer -= 1
    if sensor_timer <= 0:
        read_sensors()
        sensor_timer = 30

    update_oled()
    sleep(1000)
