from microbit import sleep
from ds3231 import read_ds3231, set_ds3231
from oled import init_oled, clear_oled, write_oled

sleep(2000)
init_oled()
clear_oled()

# Set a known time once to verify write works.
# Comment this out after the first flash — the RTC will keep running on its battery.
set_ds3231(13, 45, 0)

write_oled("DS3231 Test", 0)
sleep(1000)
clear_oled()

while True:
    h, m, s = read_ds3231()
    write_oled("{:02d}:{:02d}:{:02d}".format(h, m, s), 0)
    sleep(1000)
