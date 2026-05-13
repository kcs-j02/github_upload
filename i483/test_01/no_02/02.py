from machine import Pin, I2C
import time

i2c = I2C(0, scl=Pin(0), sda=Pin(1), freq=100000)
ADDR = 0x62

def cmd(c):
    i2c.writeto(ADDR, bytes([c >> 8, c & 0xFF]))

def read_scd41():
    cmd(0xEC05)
    time.sleep(0.01)
    d = i2c.readfrom(ADDR, 9)

    co2 = (d[0] << 8) | d[1]
    temp_raw = (d[3] << 8) | d[4]
    hum_raw = (d[6] << 8) | d[7]

    temp = -45 + 175 * temp_raw / 65535
    hum = 100 * hum_raw / 65535

    return co2, temp, hum


cmd(0x3F86)    
time.sleep(0.5)

cmd(0x21B1)      
time.sleep(5)

while True:
    co2, temp, hum = read_scd41()

    print("CO2:", co2, "ppm")
    print("Temp:", temp, "C")
    print("Humidity:", hum, "%")
    print("-----")

    time.sleep(15)