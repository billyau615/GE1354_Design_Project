from microbit import i2c

OLED_ADDR = 0x3c

def init_oled():
    """Initialize OLED display"""
    i2c.write(OLED_ADDR, b'\xae\xd5\x80\xa8\x3f\xd3\x00\x40\x8d\x14\x20\x00\xa1\xc8\xda\x12\x81\xcf\xd9\xf1\xdb\x40\x2e\xaf')

def clear_oled():
    """Clear OLED display"""
    for page in range(8):
        i2c.write(OLED_ADDR, bytes([0xb0 + page, 0x00, 0x10]))
        i2c.write(OLED_ADDR, b'\x00' * 128)

def write_oled(text, line):
    """Write text to OLED at specified line"""
    i2c.write(OLED_ADDR, bytes([0xb0 + line, 0x00, 0x10]))
    i2c.write(OLED_ADDR, text.encode() + b'\x00' * (128 - len(text)))
