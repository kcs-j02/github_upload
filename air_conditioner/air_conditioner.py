import network
import time
import ntptime
from time import sleep
from machine import Pin, PWM
from umqtt.simple import MQTTClient

SSID = "----"

BROKER = "---"
CLIENT_ID = "----"

TOPIC_CONTROL = b"---"
TOPIC_STATUS = b"---"

# D1 miniのD5 = GPIO2
servo = PWM(Pin(14), freq=50)

count = 0
last_auto_hour = -1
auto_enabled = True

def move(angle):
    min_duty = 26
    max_duty = 128
    duty = min_duty + (max_duty - min_duty) * angle // 180
    servo.duty(duty)

def publish_status(auto_state="待機中"):
    power = "ON" if count % 2 == 1 else "OFF"
    auto = "ON" if auto_enabled else "OFF"

    msg = "電源:{} / 自動:{} / 状態:{}   ".format(
        power,
        auto,
        auto_state
    )

    print(msg)
    client.publish(TOPIC_STATUS, msg.encode(), retain=True)

def push_action(auto_state="待機中"):
    global count

    count += 1
    publish_status(auto_state)

    move(90)
    sleep(1)
    move(0)

def callback(topic, msg):
    global auto_enabled

    if msg == b"push":
        push_action()

    elif msg == b"auto_on":
        auto_enabled = True
        publish_status("待機中")

    elif msg == b"auto_off":
        auto_enabled = False
        publish_status("自動停止中")

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(SSID)

while not wlan.isconnected():
    print("connecting...")
    sleep(1)

print("WiFi OK")

ntptime.settime()

client = MQTTClient(CLIENT_ID, BROKER, port=1883)
client.set_callback(callback)
client.connect()
client.subscribe(TOPIC_CONTROL)

move(0)
publish_status()

print("MQTT ready")

while True:
    client.check_msg()

    now = time.time() + 9 * 60 * 60
    t = time.localtime(now)

    hour = t[3]
    minute = t[4]

    if auto_enabled and (hour >= 22 or hour < 12) and minute == 0 and hour != last_auto_hour:
        push_action("自動PUSH中")
        last_auto_hour = hour
        publish_status("待機中")

    sleep(0.1)