from microbit import uart, pin0, pin1, pin8, pin16, button_a, button_b, display, sleep, Image
import radio
import music
from oled import init_oled, write_oled, write_oled_large, clear_oled
from dht20 import read_dht20
from ds3231 import read_ds3231, set_ds3231

# Init
radio.on()
radio.config(group=42)
uart.init(baudrate=9600, tx=pin16, rx=pin8)
music.set_tempo(bpm=114, ticks=16)

# NGGYU == Never Gonna Give You Up ;) Gotcha!
RICKROLL = [
    "G4:4","A4:4","C5:4","A4:4",
    "E5:10","R:2","E5:10","R:2","D5:20","R:4",
    "G4:4","A4:4","C5:4","A4:4",
    "D5:10","R:2","D5:10","R:2","C5:4","B4:4","A4:12","R:4",
    "G4:4","A4:4","C5:4","A4:4",
    "C5:12","D5:4","B4:6","R:2","A4:4","G4:8","R:4",
    "G4:8","D5:16","C5:24",
]

# set up variables
h = 0; m = 0; s = 0  # h = hour; m = minute; s = second
schedules = []
storage_a = 4
storage_b = 4
drop_meds_soon = False
sensor_timer = 0
last_humi = None
last_temp = None
uart_buf = b''
prev_m = -1
a_pressed_count = 0
b_pressed_count = 0


def send_uart(msg):
    uart.write(msg + "\n")


def parse_uart_line(line):
    global h, m, s, storage_a, storage_b, schedules
    # time sync from ESP32
    if line.startswith("TIME:"):    # find out the line start with 
        time = line[5:] #extract the string 
        if len(time) == 8 and time[2] == ":" and time[5] == ":": #check whether the format is correct 
            try:    #if correct, extract corresponding values, and configure the rtc module
                h = int(time[0:2])
                m = int(time[3:5])
                s = int(time[6:8])
                set_ds3231(h, m, s)
                send_uart("TIME_ACK")
            except ValueError:
                pass
    # schedule list from ESP32
    elif line.startswith("SCHED:"):
        main = line[6:]
        schedules = []
        for part in main.split(","):
            part = part.strip()
            i = part.rfind(":")
            if i < 3:
                continue
            time_str = part[:i]
            type_str = part[i + 1:]
            if len(time_str) == 5 and time_str[2] == ":":
                try:
                    sh = int(time_str[0:2])
                    sm = int(time_str[3:5])
                    schedules.append((sh, sm, type_str))
                except ValueError:
                    pass
    # storage count sync from server (via ESP32)
    elif line.startswith("STORAGE_SET:"):
        storage = line[12:]
        parts = storage.split(",")
        if len(parts) == 2:
            try:
                storage_a = int(parts[0])
                storage_b = int(parts[1])
                radio.send("INIT:{},{}".format(storage_a, storage_b))
            except ValueError:
                pass
    # dispense command (normal, with buzzer)
    elif line.startswith("DISPENSE:"):
        do_dispense(line[9:])
    # manual dispense command (silent)
    elif line.startswith("MANUAL:"):
        do_dispense_manual(line[7:])


def read_uart():
    global uart_buf
    while uart.any():
        chunk = uart.read(1)
        if chunk:
            uart_buf = uart_buf + chunk
            if b"\n" in uart_buf:
                i = uart_buf.find(b"\n")
                line = uart_buf[:i].decode("utf-8", "replace").strip()
                uart_buf = uart_buf[i + 1:]
                if line:
                    parse_uart_line(line)


def do_dispense(type_str):
    global storage_a, storage_b
    type_str = type_str.strip()
    # check storage before dispensing
    if type_str == "A" or type_str == "AB":
        if storage_a == 0:
            send_uart("STORAGE:0,{}:EMPTY_A".format(storage_b))
            return
    if type_str == "B" or type_str == "AB":
        if storage_b == 0:
            send_uart("STORAGE:{},0:EMPTY_B".format(storage_a))
            return

    radio.send("DISPENSE:" + type_str)

    # show dispense screen on OLED
    if type_str == "AB":
        label = "A+B"
    else:
        label = type_str
    write_oled_large("Take meds", 0)
    write_oled_large(label, 2)
    write_oled_large(fmt_12h(), 4)
    write_oled_large("", 6)

    # play alarm until IR sensor detects hand
    music.play(RICKROLL, pin=pin0, wait=False, loop=True)
    while pin1.read_digital() != 0:
        sleep(50)
    music.stop(pin0)

    # update storage count and notify ESP32
    empty_flag = ""
    if type_str == "A" or type_str == "AB":
        storage_a = storage_a - 1
        if storage_a == 0:
            empty_flag = empty_flag + ":EMPTY_A"
    if type_str == "B" or type_str == "AB":
        storage_b = storage_b - 1
        if storage_b == 0:
            empty_flag = empty_flag + ":EMPTY_B"

    send_uart("STORAGE:{},{}{}".format(storage_a, storage_b, empty_flag))
    send_uart("DISPENSE_DONE:" + type_str)
    update_oled()


def do_dispense_manual(type_str):
    # silent dispense — no buzzer, no OLED change
    global storage_a, storage_b
    type_str = type_str.strip()
    if type_str == "A":
        if storage_a == 0:
            send_uart("STORAGE:0,{}:EMPTY_A".format(storage_b))
            return
        radio.send("DISPENSE:A")
        storage_a = storage_a - 1
        empty_flag = ":EMPTY_A" if storage_a == 0 else ""
        send_uart("STORAGE:{},{}{}".format(storage_a, storage_b, empty_flag))
        send_uart("DISPENSE_DONE:A")
    elif type_str == "B":
        if storage_b == 0:
            send_uart("STORAGE:{},0:EMPTY_B".format(storage_a))
            return
        radio.send("DISPENSE:B")
        storage_b = storage_b - 1
        empty_flag = ":EMPTY_B" if storage_b == 0 else ""
        send_uart("STORAGE:{},{}{}".format(storage_a, storage_b, empty_flag))
        send_uart("DISPENSE_DONE:B")


def check_schedules():
    global drop_meds_soon
    if drop_meds_soon:
        return
    for (sh, sm, type_str) in schedules:
        if sh == h and sm == m:
            drop_meds_soon = True
            do_dispense(type_str)
            break


def compute_countdown():
    # find the smallest positive time delta to the next schedule
    now_mins = h * 60 + m
    min_delta = None
    for (sh, sm, _) in schedules:
        delta = (sh * 60 + sm - now_mins) % (24 * 60)
        if delta == 0:
            continue
        if min_delta is None or delta < min_delta:
            min_delta = delta
    if min_delta is None:
        return "No sched"
    return "Nx:{}H {:02d}M".format(min_delta // 60, min_delta % 60)


def fmt_12h():
    hh = h % 12             #covert to 12-hour format
    if hh == 0:
        hh = 12
    suffix = "PM" if h >= 12 else "AM"
    return "{}:{:02d} {}".format(hh, m, suffix)


def read_sensors():
    global last_humi, last_temp
    humi, temp = read_dht20()   #read temperature and humidity from sensor
    if humi is not None:
        last_humi = humi
        last_temp = temp
        send_uart("SENSOR:{},{}".format(temp, humi))


def update_oled():
    # line 0: time, line 2: humidity, line 4: temperature, line 6: countdown
    write_oled_large(fmt_12h(), 0)
    if last_humi is not None:
        write_oled_large("H:{:.1f}%".format(last_humi), 2)
        write_oled_large("T:{:.1f}C".format(last_temp), 4)
    else:
        write_oled_large("Sensor...", 2)
        write_oled_large("", 4)
    write_oled_large(compute_countdown(), 6)


def enter_refill_mode(type_str):
    global storage_a, storage_b
    if type_str == "A":
        current = storage_a
    else:
        current = storage_b
    # if there are pills left, ask user to confirm reset first
    if current > 0:
        clear_oled()
        write_oled("{} has {} left".format(type_str, current), 0)
        write_oled("A=reset B=cancel", 1)
        while button_a.is_pressed() or button_b.is_pressed():
            sleep(50)
        button_a.was_pressed()
        button_b.was_pressed()
        while True:
            if button_a.was_pressed():
                if type_str == "A":
                    storage_a = 0
                else:
                    storage_b = 0
                current = 0
                break
            if button_b.was_pressed():
                return
            sleep(50)
    # wait for button release before starting count loop (avoid spurious first step)
    while button_a.is_pressed() or button_b.is_pressed():
        sleep(50)
    button_a.was_pressed()
    button_b.was_pressed()
    radio.send("REFILL:" + type_str)
    slot_count = 0
    clear_oled()
    write_oled("Refill " + type_str, 0)
    display.show(str(slot_count))
    # each button press loads one pill and advances the wheel one slot
    while slot_count < 4:
        if type_str == "A":
            pressed = button_a.was_pressed()
            exit_pressed = button_b.was_pressed()
        else:
            pressed = button_b.was_pressed()
            exit_pressed = button_a.was_pressed()
        if pressed:
            slot_count = slot_count + 1
            display.show(str(slot_count))
            radio.send("SERVO_STEP:" + type_str)
        if exit_pressed:
            break
        sleep(50)
    if type_str == "A":
        storage_a = slot_count
    else:
        storage_b = slot_count
    send_uart("STORAGE:{},{}".format(storage_a, storage_b))
    radio.send("INIT:{},{}".format(storage_a, storage_b))
    display.clear()
    clear_oled()


def check_long_press():
    # trigger refill mode on 2-second hold of button A or B
    global a_pressed_count, b_pressed_count
    if button_a.is_pressed():
        a_pressed_count = a_pressed_count + 1
        if a_pressed_count == 2:
            enter_refill_mode("A")
            a_pressed_count = 0
    else:
        a_pressed_count = 0
    if button_b.is_pressed():
        b_pressed_count = b_pressed_count + 1
        if b_pressed_count == 2:
            enter_refill_mode("B")
            b_pressed_count = 0
    else:
        b_pressed_count = 0


# ── Boot sequence ─────────────────────────────────────────────────────────────

sleep(2000)  # wait for ESP32 to finish booting
init_oled()
clear_oled()
display.show(Image.CLOCK12)
write_oled("Waiting NTP...", 0)

# send TIME_REQ every 2s until ESP32 replies with NTP time
req_timer = 200
while True:
    req_timer = req_timer + 1
    if req_timer >= 200:
        send_uart("TIME_REQ")
        req_timer = 0
    if uart.any():
        chunk = uart.read(1)
        if chunk:
            uart_buf = uart_buf + chunk
            if b"\n" in uart_buf:
                i = uart_buf.find(b"\n")
                line = uart_buf[:i].decode("utf-8", "replace").strip()
                uart_buf = uart_buf[i + 1:]
                if line.startswith("TIME:"):
                    time = line[5:]
                    if len(time) == 8 and time[2] == ":" and time[5] == ":":
                        try:
                            h = int(time[0:2])
                            m = int(time[3:5])
                            s = int(time[6:8])
                            set_ds3231(h, m, s)
                            send_uart("TIME_ACK")
                            break
                        except ValueError:
                            pass
    sleep(10)

# wait for schedule list from ESP32
for _ in range(300):
    if uart.any():
        chunk = uart.read(1)
        if chunk:
            uart_buf = uart_buf + chunk
            if b"\n" in uart_buf:
                i = uart_buf.find(b"\n")
                line = uart_buf[:i].decode("utf-8", "replace").strip()
                uart_buf = uart_buf[i + 1:]
                if line.startswith("SCHED:"):
                    parse_uart_line(line)
                    break
    sleep(10)

# wait for storage counts from ESP32
for _ in range(300):
    if uart.any():
        chunk = uart.read(1)
        if chunk:
            uart_buf = uart_buf + chunk
            if b"\n" in uart_buf:
                i = uart_buf.find(b"\n")
                line = uart_buf[:i].decode("utf-8", "replace").strip()
                uart_buf = uart_buf[i + 1:]
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

# send servo positions to MB2 and do initial sensor read
radio.send("INIT:{},{}".format(storage_a, storage_b))
display.clear()
clear_oled()
read_sensors()
sensor_timer = 15

# ── Main loop ─────────────────────────────────────────────────────────────────

while True:
    try:
        read_uart()
        check_long_press()
        # read time from DS3231 every second
        rh, rm, rs = read_ds3231()
        if rh is not None:
            h, m, s = rh, rm, rs
            if m != prev_m:
                drop_meds_soon = False  # reset dispense flag on new minute
                prev_m = m
            check_schedules()
        # read sensors every 15 seconds
        sensor_timer = sensor_timer - 1
        if sensor_timer <= 0:
            read_sensors()
            sensor_timer = 15
        update_oled()
    except Exception:
        update_oled()
    sleep(1000)
