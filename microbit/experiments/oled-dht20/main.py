from microbit import sleep
from dht20 import read_dht20
from oled import init_oled, clear_oled, write_oled

sleep(2000)
init_oled()

def on_forever():
    h, t = read_dht20()
    clear_oled()
    if h is not None and t is not None:
        write_oled("Humi: " + str(h) + "%", 0)
        write_oled("Temp: " + str(t) + "C", 1)
    sleep(5000)

while True:
    on_forever()

