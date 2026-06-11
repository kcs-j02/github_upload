from machine import Pin, PWM
from time import sleep

servo = PWM(Pin(4), freq=50)

def angle(deg):
    min_us = 500
    max_us = 2500
    us = min_us + (max_us - min_us) * deg // 180
    duty = int(us * 65535 // 20000)
    servo.duty_u16(duty)

while True:
    angle(0)
    sleep(1)

    angle(90)
    sleep(1)

    angle(180)
    sleep(1)