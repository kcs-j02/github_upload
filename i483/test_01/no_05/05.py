from machine import Pin, I2C
import time

i2c = I2C(0, scl=Pin(0), sda=Pin(1), freq=100000)

SCD41 = 0x62
BH1750 = 0x23
RPR = 0x38
DPS = 0x76 

print("I2C devices:", i2c.scan())


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


def init_sensors():
    dev = i2c.scan()

    if SCD41 in dev:
        write_cmd(SCD41, 0x3F86)  # stop
        time.sleep(0.5)
        write_cmd(SCD41, 0x21B1)  # start
        time.sleep(5)

    if RPR in dev:
        write_reg(RPR, 0x41, 0xC6)
        time.sleep(0.2)

    if DPS in dev:
        write_reg(DPS, 0x06, 0x00)
        write_reg(DPS, 0x07, 0x80)
        write_reg(DPS, 0x08, 0x07)
        time.sleep(0.2)


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


def read_dps310_raw():
    d = read_reg(DPS, 0x00, 6)

    pressure_raw = signed24(d[0], d[1], d[2])
    temp_raw = signed24(d[3], d[4], d[5])

    return pressure_raw, temp_raw


init_sensors()

print("Start measurement")

while True:
    print("==========")

    co2, temp, hum = read_scd41()
    print("SCD41 CO2:", co2, "ppm")
    print("SCD41 Temp:", temp, "C")
    print("SCD41 Humidity:", hum, "%")

    bh_lux = read_bh1750()
    print("BH1750 Light:", bh_lux, "lux")

    als0, als1, rpr_lux = read_rpr()
    print("RPR-0521RS ALS0:", als0)
    print("RPR-0521RS ALS1:", als1)
    print("RPR-0521RS Light:", rpr_lux, "lux")

    p_raw, t_raw = read_dps310_raw()
    print("DPS310 Pressure raw:", p_raw)
    print("DPS310 Temp raw:", t_raw)

    time.sleep(15)

# DPS310の値が間違っていた原因は、センサーから読み取った値をそのまま表示していたためである。
# DPS310から取得できる値は、最初は気圧や温度として使える値ではなく、補正前のraw値である。
# そのため、Pressure raw: -247826 や Temp raw: 135828 のように、気圧や温度として見ると不自然な値になっていた。

# 正しい値を出すためには、DPS310内部に保存されている補正係数を読み取り、その係数を使ってraw値を計算し直す必要がある。
# 具体的には、圧力と温度のraw値をスケーリングし、補正式に代入することで、気圧をhPa、温度を℃として意味のある値に変換する。

# そのため、05-2に変更コードを書き、出力値を示す。
# コードでは、DPS310のraw値をそのまま返す read_dps310_raw() を使うのをやめ、補正係数を読み取る処理と、補正式を使って気圧・温度に変換する read_dps310() を追加した。
# また、表示部分も DPS310 Pressure raw や DPS310 Temp raw ではなく、DPS310 Pressure: ○○ hPa、DPS310 Temp: ○○ C のように、補正後の値を表示する形に変更した。

# つまり、変更内容は「raw値をそのまま表示するコード」から、「DPS310の補正係数を使って、raw値を正しい気圧と温度に変換して表示するコード」に変えたということである。