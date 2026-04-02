from microbit import uart, pin0, pin1, pin8, pin16, button_a, button_b, display, sleep, Image
import radio
import music
from oled import init_oled, write_oled, write_oled_large, clear_oled
from dht20 import read_dht20
from ds3231 import read_ds3231, set_ds3231

radio.on()
radio.config(group=42)
uart.init(baudrate=9600, tx=pin16, rx=pin8)
music.set_tempo(bpm=114, ticks=16)

RICKROLL = [
    "G4:4","A4:4","C5:4","A4:4",
    "E5:10","R:2","E5:10","R:2","D5:20","R:4",
    "G4:4","A4:4","C5:4","A4:4",
    "D5:10","R:2","D5:10","R:2","C5:4","B4:4","A4:12","R:4",
    "G4:4","A4:4","C5:4","A4:4",
    "C5:12","D5:4","B4:6","R:2","A4:4","G4:8","R:4",
    "G4:8","D5:16","C5:24",
]

h = 0; m = 0; s = 0
schedules = []
storage_a = 4
storage_b = 4
dispensed_this_minute = False
sensor_timer = 0
last_humi = None
last_temp = None
uart_buf = b''
prev_m = -1
a_pressed_since = 0
b_pressed_since = 0

def send_uart(msg):
    uart.write(msg + "\n")

def parse_sched_line(line):
    global schedules
    body = line[6:]
    schedules = []
    for part in body.split(","):
        part = part.strip()
        idx = part.rfind(":")
        if idx < 3:
            continue
        time_str = part[:idx]
        type_str = part[idx+1:]
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
                radio.send("INIT:{},{}".format(storage_a, storage_b))
            except ValueError:
                pass
    elif line.startswith("DISPENSE:"):
        do_dispense(line[9:])
    elif line.startswith("MANUAL:"):
        do_dispense_manual(line[7:])

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
    if type_str == "A" or type_str == "AB":
        if storage_a == 0:
            send_uart("STORAGE:0,{}:EMPTY_A".format(storage_b))
            return
    if type_str == "B" or type_str == "AB":
        if storage_b == 0:
            send_uart("STORAGE:{},0:EMPTY_B".format(storage_a))
            return

    radio.send("DISPENSE:" + type_str)

    label = "A+B" if type_str == "AB" else type_str
    write_oled_large("Take meds", 0)
    write_oled_large(label, 2)
    write_oled_large(fmt_12h(), 4)
    write_oled_large("", 6)

    music.play(RICKROLL, pin=pin0, wait=False, loop=True)
    while pin1.read_digital() != 0:
        sleep(50)
    music.stop(pin0)

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
    update_oled()

def do_dispense_manual(type_str):
    global storage_a, storage_b
    type_str = type_str.strip()
    if type_str == "A":
        if storage_a == 0:
            send_uart("STORAGE:0,{}:EMPTY_A".format(storage_b))
            return
        radio.send("DISPENSE:A")
        storage_a -= 1
        empty_flag = ":EMPTY_A" if storage_a == 0 else ""
        send_uart("STORAGE:{},{}{}".format(storage_a, storage_b, empty_flag))
        send_uart("DISPENSE_DONE:A")
    elif type_str == "B":
        if storage_b == 0:
            send_uart("STORAGE:{},0:EMPTY_B".format(storage_a))
            return
        radio.send("DISPENSE:B")
        storage_b -= 1
        empty_flag = ":EMPTY_B" if storage_b == 0 else ""
        send_uart("STORAGE:{},{}{}".format(storage_a, storage_b, empty_flag))
        send_uart("DISPENSE_DONE:B")

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
        delta = (sh * 60 + sm - now_mins) % (24 * 60)
        if delta == 0:
            continue
        if min_delta is None or delta < min_delta:
            min_delta = delta
    if min_delta is None:
        return "No sched"
    return "Nx:{}H {:02d}M".format(min_delta // 60, min_delta % 60)

def fmt_12h():
    hh = h % 12
    if hh == 0:
        hh = 12
    suffix = "PM" if h >= 12 else "AM"
    return "{}:{:02d} {}".format(hh, m, suffix)

def read_sensors():
    global last_humi, last_temp
    humi, temp = read_dht20()
    if humi is not None:
        last_humi = humi
        last_temp = temp
        send_uart("SENSOR:{},{}".format(temp, humi))

def update_oled():
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
    current = storage_a if type_str == "A" else storage_b
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
    radio.send("REFILL:" + type_str)
    slot_count = 0
    clear_oled()
    write_oled("Refill " + type_str, 0)
    display.show(str(slot_count))
    while slot_count < 4:
        if type_str == "A":
            pressed = button_a.was_pressed()
            exit_pressed = button_b.was_pressed()
        else:
            pressed = button_b.was_pressed()
            exit_pressed = button_a.was_pressed()
        if pressed:
            slot_count += 1
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
    display.clear()
    clear_oled()

def check_long_press():
    global a_pressed_since, b_pressed_since
    if button_a.is_pressed():
        a_pressed_since += 1
        if a_pressed_since == 2:
            enter_refill_mode("A")
            a_pressed_since = 0
    else:
        a_pressed_since = 0
    if button_b.is_pressed():
        b_pressed_since += 1
        if b_pressed_since == 2:
            enter_refill_mode("B")
            b_pressed_since = 0
    else:
        b_pressed_since = 0

sleep(2000)
init_oled()
clear_oled()
display.show(Image.CLOCK12)
write_oled("Waiting NTP...", 0)
req_timer = 200
while True:
    req_timer += 1
    if req_timer >= 200:
        send_uart("TIME_REQ")
        req_timer = 0
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
                            set_ds3231(h, m, s)
                            send_uart("TIME_ACK")
                            break
                        except ValueError:
                            pass
    sleep(10)

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

radio.send("INIT:{},{}".format(storage_a, storage_b))
display.clear()
clear_oled()
read_sensors()
sensor_timer = 15

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
        sensor_timer = 15
    update_oled()
    sleep(1000)
