from machine import Pin, I2C
import time

i2c = I2C(0, scl=Pin(0), sda=Pin(1), freq=100000)

ADDR = 0x38   # RPR-0521RS

print("I2C devices:", i2c.scan())

if ADDR not in i2c.scan():
    print("RPR-0521RS not found")
    raise SystemExit

def write_reg(reg, val):
    i2c.writeto(ADDR, bytes([reg, val]))

def read_reg(reg, n):
    i2c.writeto(ADDR, bytes([reg]))
    return i2c.readfrom(ADDR, n)

def read_rpr():
    data = read_reg(0x46, 4)

    als0 = data[0] | (data[1] << 8)
    als1 = data[2] | (data[3] << 8)

    if als0 == 0:
        lux = 0
    else:
        ratio = als1 / als0

        if ratio < 0.595:
            lux = 1.682 * als0 - 1.877 * als1
        elif ratio < 1.015:
            lux = 0.644 * als0 - 0.132 * als1
        elif ratio < 1.352:
            lux = 0.756 * als0 - 0.243 * als1
        elif ratio < 3.053:
            lux = 0.766 * als0 - 0.25 * als1
        else:
            lux = 0

    return als0, als1, lux


write_reg(0x41, 0xC6)
time.sleep(0.2)

while True:
    als0, als1, lux = read_rpr()

    print("ALS0:", als0)
    print("ALS1:", als1)
    print("Light:", lux, "lux")
    print("-----")

    time.sleep(15)