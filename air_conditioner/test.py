from machine import Pin, PWM
from time import sleep

servo = PWM(Pin(14), freq=50)

while True:
    servo.duty(26)
    print("0")
    sleep(2)

    servo.duty(77)
    print("90")
    sleep(2)

    servo.duty(128)
    print("180")
    sleep(2)