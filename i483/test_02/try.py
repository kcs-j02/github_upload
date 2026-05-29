from machine import Pin, I2C
import network
import time
from umqtt.simple import MQTTClient

SSID = "JAISTALL"

MQTT_BROKER = "150.65.230.59"
MQTT_PORT = 1883
STUDENT = "s2510063"

i2c = I2C(0, scl=Pin(0), sda=Pin(1), freq=50000)

SCD41 = 0x62
BH1750 = 0x23
RPR = 0x38
DPS = 0x77

K_PRESSURE = 524288
K_TEMP = 524288
dps_coef = None


# =====================
# Wi-Fi / MQTT
# =====================

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)

    wlan.active(False)
    time.sleep(1)
    wlan.active(True)
    time.sleep(1)

    try:
        wlan.disconnect()
    except:
        pass

    print("Connecting to WiFi:", SSID)
    wlan.connect(SSID)

    while not wlan.isconnected():
        print("WiFi connecting...", wlan.status())
        time.sleep(1)

    print("WiFi connected")
    print(wlan.ifconfig())


def make_topic(sensor, data_type):
    return "i483/sensors/{}/{}/{}".format(
        STUDENT, sensor, data_type
    ).encode()


def publish_value(client, sensor, data_type, value):
    topic = make_topic(sensor, data_type)
    message = "{:.2f}".format(value)
    client.publish(topic, message)
    print("publish:", topic, message)


# =====================
# I2C helper
# =====================

def write_cmd(addr, cmd):
    i2c.writeto(addr, bytes([(cmd >> 8) & 0xFF, cmd & 0xFF]))


def write_reg(addr, reg, val):
    i2c.writeto(addr, bytes([reg, val]))


def read_reg(addr, reg, n):
    i2c.writeto(addr, bytes([reg]))
    return i2c.readfrom(addr, n)


def to_signed(value, bits):
    if value & (1 << (bits - 1)):
        value -= 1 << bits
    return value


def signed24(b0, b1, b2):
    return to_signed((b0 << 16) | (b1 << 8) | b2, 24)


# =====================
# Sensor init
# =====================

def init_sensors():
    global dps_coef

    print("I2C devices:", [hex(x) for x in i2c.scan()])

    # SCD41 start
    try:
        write_cmd(SCD41, 0x3F86)
        time.sleep(1)
    except:
        pass

    write_cmd(SCD41, 0x21B1)
    time.sleep(6)
    print("SCD41 started")

    # RPR-0521RS
    write_reg(RPR, 0x41, 0xC6)
    time.sleep(0.2)
    print("RPR-0521RS initialized")

    # DPS310
    write_reg(DPS, 0x08, 0x00)
    time.sleep(0.1)
    dps_coef = read_dps310_coeffs()

    write_reg(DPS, 0x06, 0x00)
    write_reg(DPS, 0x07, 0x80)
    write_reg(DPS, 0x08, 0x07)
    time.sleep(1)

    print("DPS310 initialized")


# =====================
# SCD41
# =====================

def read_scd41():
    write_cmd(SCD41, 0xEC05)
    time.sleep(0.01)

    d = i2c.readfrom(SCD41, 9)

    co2 = (d[0] << 8) | d[1]
    temp_raw = (d[3] << 8) | d[4]
    hum_raw = (d[6] << 8) | d[7]

    temp = -45 + 175 * temp_raw / 65535
    hum = 100 * hum_raw / 65535

    return co2, temp, hum


# =====================
# BH1750
# =====================

def read_bh1750():
    i2c.writeto(BH1750, bytes([0x20]))
    time.sleep(0.18)

    d = i2c.readfrom(BH1750, 2)
    raw = (d[0] << 8) | d[1]

    return raw / 1.2


# =====================
# RPR-0521RS
# =====================

def read_rpr():
    d = read_reg(RPR, 0x46, 4)

    als0 = d[0] | (d[1] << 8)
    als1 = d[2] | (d[3] << 8)

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

    if lux < 0:
        lux = 0

    return als1, lux


# =====================
# DPS310
# =====================

def wait_dps310_coef_ready():
    for _ in range(50):
        status = read_reg(DPS, 0x08, 1)[0]
        if status & 0x80:
            return True
        time.sleep(0.02)
    return False


def wait_dps310_data_ready():
    for _ in range(50):
        status = read_reg(DPS, 0x08, 1)[0]
        if (status & 0x30) == 0x30:
            return True
        time.sleep(0.02)
    return False


def read_dps310_coeffs():
    if not wait_dps310_coef_ready():
        raise OSError("DPS310 coefficient not ready")

    d = read_reg(DPS, 0x10, 18)

    c0 = to_signed((d[0] << 4) | (d[1] >> 4), 12)
    c1 = to_signed(((d[1] & 0x0F) << 8) | d[2], 12)
    c00 = to_signed((d[3] << 12) | (d[4] << 4) | (d[5] >> 4), 20)
    c10 = to_signed(((d[5] & 0x0F) << 16) | (d[6] << 8) | d[7], 20)
    c01 = to_signed((d[8] << 8) | d[9], 16)
    c11 = to_signed((d[10] << 8) | d[11], 16)
    c20 = to_signed((d[12] << 8) | d[13], 16)
    c21 = to_signed((d[14] << 8) | d[15], 16)
    c30 = to_signed((d[16] << 8) | d[17], 16)

    return c0, c1, c00, c10, c01, c11, c20, c21, c30


def read_dps310():
    global dps_coef

    if not wait_dps310_data_ready():
        raise OSError("DPS310 data not ready")

    d = read_reg(DPS, 0x00, 6)

    p_raw = signed24(d[0], d[1], d[2])
    t_raw = signed24(d[3], d[4], d[5])

    p_sc = p_raw / K_PRESSURE
    t_sc = t_raw / K_TEMP

    c0, c1, c00, c10, c01, c11, c20, c21, c30 = dps_coef

    temp = c0 * 0.5 + c1 * t_sc

    pressure = (
        c00
        + p_sc * (c10 + p_sc * (c20 + p_sc * c30))
        + t_sc * c01
        + t_sc * p_sc * (c11 + p_sc * c21)
    ) / 100

    return pressure, temp


# =====================
# Main
# =====================

init_sensors()
connect_wifi()

client = MQTTClient("pico_" + STUDENT, MQTT_BROKER, port=MQTT_PORT)
client.connect()

print("MQTT connected")
print("Start measurement")

while True:
    print("==========")

    try:
        co2, temp, hum = read_scd41()
        publish_value(client, "SCD41", "co2", co2)
        publish_value(client, "SCD41", "temperature", temp)
        publish_value(client, "SCD41", "humidity", hum)
    except OSError as e:
        print("SCD41 error:", e)

    try:
        lux = read_bh1750()
        publish_value(client, "BH1750", "illumination", lux)
    except OSError as e:
        print("BH1750 error:", e)

    try:
        infrared, lux = read_rpr()
        publish_value(client, "RPR0521", "illumination", lux)
        publish_value(client, "RPR0521", "infrared_illumination", infrared)
    except OSError as e:
        print("RPR0521 error:", e)

    try:
        pressure, temp = read_dps310()
        publish_value(client, "DPS310", "air_pressure", pressure)
        publish_value(client, "DPS310", "temperature", temp)
    except OSError as e:
        print("DPS310 error:", e)

    time.sleep(15)