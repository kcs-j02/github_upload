from machine import Pin, I2C
import time

i2c = I2C(0, scl=Pin(0), sda=Pin(1), freq=100000)

BH1750_ADDR = 0x23

print("I2C devices:", i2c.scan())

if BH1750_ADDR not in i2c.scan():
    print("BH1750 not found")
    raise SystemExit

while True:
    i2c.writeto(BH1750_ADDR, bytes([0x20]))
    time.sleep(0.18)

    data = i2c.readfrom(BH1750_ADDR, 2)
    raw = (data[0] << 8) | data[1]
    lux = raw / 1.2

    print("BH1750 Light:", lux, "lux")
    print("----------------")

    time.sleep(15)