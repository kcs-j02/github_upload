from machine import Pin, I2C
import time

i2c = I2C(0, scl=Pin(0), sda=Pin(1), freq=100000)

SCD41 = 0x62
BH1750 = 0x23
RPR = 0x38
DPS = 0x76

devices = i2c.scan()
print("I2C devices:", devices)

def write_cmd(addr, cmd):
    i2c.writeto(addr, bytes([(cmd >> 8) & 0xFF, cmd & 0xFF]))


def write_reg(addr, reg, val):
    i2c.writeto(addr, bytes([reg, val]))


def read_reg(addr, reg, n):
    i2c.writeto(addr, bytes([reg]))
    return i2c.readfrom(addr, n)


def signed24(b0, b1, b2):
    v = (b0 << 16) | (b1 << 8) | b2
    if v & 0x800000:
        v -= 1 << 24
    return v


def sign_extend(value, bits):
    if value & (1 << (bits - 1)):
        value -= 1 << bits
    return value


DPS_COEF = None

DPS_KP = 524288
DPS_KT = 524288


def read_dps310_coefficients():
    c = read_reg(DPS, 0x10, 18)

    c0 = (c[0] << 4) | (c[1] >> 4)
    c0 = sign_extend(c0, 12)

    c1 = ((c[1] & 0x0F) << 8) | c[2]
    c1 = sign_extend(c1, 12)

    c00 = (c[3] << 12) | (c[4] << 4) | (c[5] >> 4)
    c00 = sign_extend(c00, 20)

    c10 = ((c[5] & 0x0F) << 16) | (c[6] << 8) | c[7]
    c10 = sign_extend(c10, 20)

    c01 = (c[8] << 8) | c[9]
    c01 = sign_extend(c01, 16)

    c11 = (c[10] << 8) | c[11]
    c11 = sign_extend(c11, 16)

    c20 = (c[12] << 8) | c[13]
    c20 = sign_extend(c20, 16)

    c21 = (c[14] << 8) | c[15]
    c21 = sign_extend(c21, 16)

    c30 = (c[16] << 8) | c[17]
    c30 = sign_extend(c30, 16)

    return {
        "c0": c0,
        "c1": c1,
        "c00": c00,
        "c10": c10,
        "c01": c01,
        "c11": c11,
        "c20": c20,
        "c21": c21,
        "c30": c30
    }


def init_dps310():
    global DPS_COEF

    # pressure: rate 1Hz, oversampling 1
    write_reg(DPS, 0x06, 0x00)

    # temperature: rate 1Hz, oversampling 1, external temperature sensor
    write_reg(DPS, 0x07, 0x80)

    # continuous pressure and temperature measurement
    write_reg(DPS, 0x08, 0x07)

    time.sleep(0.5)

    DPS_COEF = read_dps310_coefficients()
    print("DPS310 coefficients loaded")


def read_dps310():
    global DPS_COEF

    if DPS_COEF is None:
        DPS_COEF = read_dps310_coefficients()

    d = read_reg(DPS, 0x00, 6)

    prs_raw = signed24(d[0], d[1], d[2])
    tmp_raw = signed24(d[3], d[4], d[5])

    prs = prs_raw / DPS_KP
    tmp = tmp_raw / DPS_KT

    c0 = DPS_COEF["c0"]
    c1 = DPS_COEF["c1"]
    c00 = DPS_COEF["c00"]
    c10 = DPS_COEF["c10"]
    c01 = DPS_COEF["c01"]
    c11 = DPS_COEF["c11"]
    c20 = DPS_COEF["c20"]
    c21 = DPS_COEF["c21"]
    c30 = DPS_COEF["c30"]

    temperature = c0 * 0.5 + c1 * tmp

    pressure_pa = (
        c00
        + prs * (c10 + prs * (c20 + prs * c30))
        + tmp * c01
        + tmp * prs * (c11 + prs * c21)
    )

    pressure_hpa = pressure_pa / 100

    return pressure_hpa, temperature


def init_sensors():
    dev = i2c.scan()
    print("Detected:", dev)

    if SCD41 in dev:
        print("SCD41 found")
        try:
            write_cmd(SCD41, 0x3F86)
            time.sleep(0.5)
        except OSError:
            pass

        write_cmd(SCD41, 0x21B1)
        time.sleep(5)
    else:
        print("SCD41 not found")

    if BH1750 in dev:
        print("BH1750 found")
    else:
        print("BH1750 not found")

    if RPR in dev:
        print("RPR-0521RS found")
        write_reg(RPR, 0x41, 0xC6)
        time.sleep(0.2)
    else:
        print("RPR-0521RS not found")

    if DPS in dev:
        print("DPS310 found")
        init_dps310()
    else:
        print("DPS310 not found")


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


def read_bh1750():
    i2c.writeto(BH1750, bytes([0x20]))
    time.sleep(0.18)
    d = i2c.readfrom(BH1750, 2)

    raw = (d[0] << 8) | d[1]
    lux = raw / 1.2

    return lux


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

    return als0, als1, lux


init_sensors()

print("Start measurement")

while True:
    print("==========")

    dev = i2c.scan()
    print("I2C devices:", dev)

    if SCD41 in dev:
        co2, temp, hum = read_scd41()

        if co2 == 0:
            print("SCD41 CO2: warming up")
        else:
            print("SCD41 CO2:", co2, "ppm")

        print("SCD41 Temp:", temp, "C")
        print("SCD41 Humidity:", hum, "%")
    else:
        print("SCD41 skipped")

    if BH1750 in dev:
        bh_lux = read_bh1750()
        print("BH1750 Light:", bh_lux, "lux")
    else:
        print("BH1750 skipped")

    if RPR in dev:
        als0, als1, rpr_lux = read_rpr()
        print("RPR-0521RS ALS0:", als0)
        print("RPR-0521RS ALS1:", als1)
        print("RPR-0521RS Light:", rpr_lux, "lux")
    else:
        print("RPR-0521RS skipped")

    if DPS in dev:
        pressure, dps_temp = read_dps310()
        print("DPS310 Pressure:", pressure, "hPa")
        print("DPS310 Temp:", dps_temp, "C")
    else:
        print("DPS310 skipped")

    time.sleep(15)


# 出力値
# ==========
# I2C devices: [35, 56, 98, 118]
# SCD41 CO2: 2184 ppm
# SCD41 Temp: 25.408562 C
# SCD41 Humidity: 61.80972 %
# BH1750 Light: 7.49999936 lux
# RPR-0521RS ALS0: 3
# RPR-0521RS ALS1: 0
# RPR-0521RS Light: 5.046 lux
# DPS310 Pressure: 1008.49304 hPa
# DPS310 Temp: 26.748856 C
# ==========
# I2C devices: [35, 56, 98, 118]
# SCD41 CO2: 2181 ppm
# SCD41 Temp: 25.419242 C
# SCD41 Humidity: 61.789884 %
# BH1750 Light: 7.49999936 lux
# RPR-0521RS ALS0: 3
# RPR-0521RS ALS1: 0
# RPR-0521RS Light: 5.046 lux
# DPS310 Pressure: 1008.48948 hPa
# DPS310 Temp: 26.723236 C
# ==========
# I2C devices: [35, 56, 98, 118]
# SCD41 CO2: 2184 ppm
# SCD41 Temp: 25.443276 C
# SCD41 Humidity: 61.725796 %
# BH1750 Light: 7.49999936 lux
# RPR-0521RS ALS0: 3
# RPR-0521RS ALS1: 0
# RPR-0521RS Light: 5.046 lux
# DPS310 Pressure: 1008.503 hPa
# DPS310 Temp: 26.715438 C
# ==========
# I2C devices: [35, 56, 98, 118]
# SCD41 CO2: 2185 ppm
# SCD41 Temp: 25.48333 C
# SCD41 Humidity: 61.651028 %
# BH1750 Light: 7.49999936 lux
# RPR-0521RS ALS0: 3
# RPR-0521RS ALS1: 0
# RPR-0521RS Light: 5.046 lux
# DPS310 Pressure: 1008.5187 hPa
# DPS310 Temp: 26.654174 C
# ==========
# I2C devices: [35, 56, 98, 118]
# SCD41 CO2: 2185 ppm
# SCD41 Temp: 25.512702 C
# SCD41 Humidity: 61.609824 %
# BH1750 Light: 7.49999936 lux
# RPR-0521RS ALS0: 3
# RPR-0521RS ALS1: 0
# RPR-0521RS Light: 5.046 lux
# DPS310 Pressure: 1008.5206 hPa
# DPS310 Temp: 26.645264 C
# ==========
# I2C devices: [35, 56, 98, 118]
# SCD41 CO2: 2184 ppm
# SCD41 Temp: 25.499352 C
# SCD41 Humidity: 61.536584 %
# BH1750 Light: 7.49999936 lux
# RPR-0521RS ALS0: 3
# RPR-0521RS ALS1: 0
# RPR-0521RS Light: 5.046 lux
# DPS310 Pressure: 1008.47292 hPa
# DPS310 Temp: 26.582886 C

