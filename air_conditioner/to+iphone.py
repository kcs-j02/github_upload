import network
from time import sleep
from machine import Pin, PWM
from umqtt.simple import MQTTClient

SSID = "----"

BROKER = "---"
CLIENT_ID = "---"

TOPIC_CONTROL = b"---"
TOPIC_STATUS = b"---"

servo = PWM(Pin(4), freq=50)

def move(angle):
    duty = 1638 + (8192 - 1638) * angle // 180
    servo.duty_u16(duty)

count = 0

def callback(topic, msg):
    global count

    if msg == b"push":

        count += 1

        if count % 2 == 1:
            state = b"ON"
        else:
            state = b"OFF"

        client.publish(
            b"yukimi/sg90/status",
            state
        )

        move(90)
        sleep(1)
        move(0)

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(SSID)

while not wlan.isconnected():
    print("connecting...")
    sleep(1)

print("WiFi OK")

client = MQTTClient(CLIENT_ID, BROKER, port=1883)
client.set_callback(callback)
client.connect()
client.subscribe(TOPIC_CONTROL)

client.publish(TOPIC_STATUS, b"OFF")

print("MQTT ready")

move(0)

while True:
    client.check_msg()
    sleep(0.1)