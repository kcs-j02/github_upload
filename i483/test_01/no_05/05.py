from machine import Pin, I2C
import time

# 配線に合わせる
# SCL=GP0, SDA=GP1 の場合
i2c = I2C(0, scl=Pin(0), sda=Pin(1), freq=50000)

SCD41 = 0x62
BH1750 = 0x23
RPR = 0x38

DPS_ADDRS = [0x76, 0x77]
DPS = None

# DPS310 oversampling x1 のスケール係数
K_PRESSURE = 524288
K_TEMP = 524288

dps_coef = None


def scan_i2c():
    dev = i2c.scan()
    print("I2C devices:", [hex(x) for x in dev])
    return dev


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
    v = (b0 << 16) | (b1 << 8) | b2
    return to_signed(v, 24)


def detect_dps(dev):
    for addr in DPS_ADDRS:
        if addr in dev:
            return addr
    return None


def wait_dps310_ready(timeout_ms=1000):
    start = time.ticks_ms()

    while time.ticks_diff(time.ticks_ms(), start) < timeout_ms:
        status = read_reg(DPS, 0x08, 1)[0]

        # bit5 = TMP_RDY, bit4 = PRS_RDY
        if (status & 0x30) == 0x30:
            return True

        time.sleep(0.02)

    return False


def wait_dps310_coef_ready(timeout_ms=1000):
    start = time.ticks_ms()

    while time.ticks_diff(time.ticks_ms(), start) < timeout_ms:
        status = read_reg(DPS, 0x08, 1)[0]

        # bit7 = COEF_RDY
        if status & 0x80:
            return True

        time.sleep(0.02)

    return False


def read_dps310_coeffs():
    if not wait_dps310_coef_ready():
        raise OSError("DPS310 coefficient not ready")

    d = read_reg(DPS, 0x10, 18)

    c0 = (d[0] << 4) | (d[1] >> 4)
    c0 = to_signed(c0, 12)

    c1 = ((d[1] & 0x0F) << 8) | d[2]
    c1 = to_signed(c1, 12)

    c00 = (d[3] << 12) | (d[4] << 4) | (d[5] >> 4)
    c00 = to_signed(c00, 20)

    c10 = ((d[5] & 0x0F) << 16) | (d[6] << 8) | d[7]
    c10 = to_signed(c10, 20)

    c01 = (d[8] << 8) | d[9]
    c01 = to_signed(c01, 16)

    c11 = (d[10] << 8) | d[11]
    c11 = to_signed(c11, 16)

    c20 = (d[12] << 8) | d[13]
    c20 = to_signed(c20, 16)

    c21 = (d[14] << 8) | d[15]
    c21 = to_signed(c21, 16)

    c30 = (d[16] << 8) | d[17]
    c30 = to_signed(c30, 16)

    return {
        "c0": c0,
        "c1": c1,
        "c00": c00,
        "c10": c10,
        "c01": c01,
        "c11": c11,
        "c20": c20,
        "c21": c21,
        "c30": c30,
    }


def init_sensors():
    global DPS, dps_coef

    dev = scan_i2c()

    DPS = detect_dps(dev)

    if DPS is not None:
        print("DPS310 address:", hex(DPS))
    else:
        print("DPS310 not found")

    # SCD41
    if SCD41 in dev:
        try:
            write_cmd(SCD41, 0x3F86)  # stop periodic measurement
            time.sleep(1.0)
        except OSError as e:
            print("SCD41 stop skipped:", e)

        try:
            write_cmd(SCD41, 0x21B1)  # start periodic measurement
            time.sleep(6)
            print("SCD41 started")
        except OSError as e:
            print("SCD41 start failed:", e)

    # RPR-0521RS
    if RPR in dev:
        try:
            write_reg(RPR, 0x41, 0xC6)
            time.sleep(0.2)
            print("RPR-0521RS initialized")
        except OSError as e:
            print("RPR init failed:", e)

    # DPS310
    if DPS is not None:
        try:
            time.sleep(0.2)

            # 測定停止
            write_reg(DPS, 0x08, 0x00)
            time.sleep(0.1)

            # 補正係数を先に読む
            dps_coef = read_dps310_coeffs()

            # pressure config: rate x1, oversampling x1
            write_reg(DPS, 0x06, 0x00)

            # temperature config: 外部温度センサ, rate x1, oversampling x1
            write_reg(DPS, 0x07, 0x80)

            # continuous pressure and temperature
            write_reg(DPS, 0x08, 0x07)

            time.sleep(1.0)

            print("DPS310 initialized")
        except OSError as e:
            print("DPS310 init failed:", e)


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

    if lux < 0:
        lux = 0

    return als0, als1, lux


def read_dps310():
    global dps_coef

    if DPS is None:
        raise OSError("DPS310 not found")

    if dps_coef is None:
        dps_coef = read_dps310_coeffs()

    if not wait_dps310_ready():
        raise OSError("DPS310 data not ready")

    d = read_reg(DPS, 0x00, 6)

    p_raw = signed24(d[0], d[1], d[2])
    t_raw = signed24(d[3], d[4], d[5])

    # raw が両方0なら異常値として捨てる
    if p_raw == 0 and t_raw == 0:
        raise OSError("DPS310 invalid raw data")

    p_sc = p_raw / K_PRESSURE
    t_sc = t_raw / K_TEMP

    c0 = dps_coef["c0"]
    c1 = dps_coef["c1"]
    c00 = dps_coef["c00"]
    c10 = dps_coef["c10"]
    c01 = dps_coef["c01"]
    c11 = dps_coef["c11"]
    c20 = dps_coef["c20"]
    c21 = dps_coef["c21"]
    c30 = dps_coef["c30"]

    temp_c = c0 * 0.5 + c1 * t_sc

    pressure_pa = (
        c00
        + p_sc * (c10 + p_sc * (c20 + p_sc * c30))
        + t_sc * c01
        + t_sc * p_sc * (c11 + p_sc * c21)
    )

    pressure_hpa = pressure_pa / 100

    return pressure_hpa, temp_c, p_raw, t_raw


init_sensors()

print("Start measurement")

while True:
    print("==========")

    try:
        co2, temp, hum = read_scd41()
        print("SCD41 CO2:", co2, "ppm")
        print("SCD41 Temp:", temp, "C")
        print("SCD41 Humidity:", hum, "%")
    except OSError as e:
        print("SCD41 read failed:", e)

    try:
        bh_lux = read_bh1750()
        print("BH1750 Light:", bh_lux, "lux")
    except OSError as e:
        print("BH1750 read failed:", e)

    try:
        als0, als1, rpr_lux = read_rpr()
        print("RPR-0521RS ALS0:", als0)
        print("RPR-0521RS ALS1:", als1)
        print("RPR-0521RS Light:", rpr_lux, "lux")
    except OSError as e:
        print("RPR-0521RS read failed:", e)

    try:
        pressure, dps_temp, p_raw, t_raw = read_dps310()
        print("DPS310 Pressure:", pressure, "hPa")
        print("DPS310 Temp:", dps_temp, "C")
        print("DPS310 Pressure raw:", p_raw)
        print("DPS310 Temp raw:", t_raw)
    except OSError as e:
        print("DPS310 read failed:", e)

    time.sleep(15)