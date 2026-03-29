from microbit import i2c, sleep

DHT20_ADDR = 0x38

def read_dht20():
    """Read temperature and humidity from DHT20"""
    try:
        i2c.write(DHT20_ADDR, b'\xac\x33\x00')
        sleep(80)
        data = i2c.read(DHT20_ADDR, 6)
        humidity = ((data[1] << 8) | data[2]) >> 4
        temperature = ((data[3] & 0x0f) << 8) | data[4]
        humidity = (humidity / 1048576) * 100
        temperature = ((temperature / 1048576) * 200) - 50
        return round(humidity, 1), round(temperature, 1)
    except:
        return None, None
