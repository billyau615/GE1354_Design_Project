from microbit import i2c

DS3231_ADDR = 0x68


def _bcd_to_int(byte):
    return (byte >> 4) * 10 + (byte & 0x0F)


def _int_to_bcd(n):
    return ((n // 10) << 4) | (n % 10)


def read_ds3231():
    """Read time from DS3231. Returns (h, m, s) as ints, or (0, 0, 0) on error."""
    try:
        i2c.write(DS3231_ADDR, b'\x00')
        data = i2c.read(DS3231_ADDR, 3)
        sec  = _bcd_to_int(data[0] & 0x7F)
        mins = _bcd_to_int(data[1] & 0x7F)
        hr_byte = data[2]
        if hr_byte & 0x40:              # chip in 12h mode — convert to 24h
            am_pm = (hr_byte >> 5) & 0x01
            hrs = _bcd_to_int(hr_byte & 0x1F)
            if am_pm and hrs != 12:
                hrs += 12
            elif not am_pm and hrs == 12:
                hrs = 0
        else:
            hrs = _bcd_to_int(hr_byte & 0x3F)
        return hrs, mins, sec
    except:
        return 0, 0, 0


def set_ds3231(h, m, s):
    """Write time to DS3231. Forces 24h mode (bit 6 of hours register = 0)."""
    try:
        i2c.write(DS3231_ADDR, bytes([
            0x00,
            _int_to_bcd(s),
            _int_to_bcd(m),
            _int_to_bcd(h),
        ]))
    except:
        pass
