# main.py
# 1-d: CO2 threshold の結果で MCU の LED を点滅させる

import network
import time
from machine import Pin
from umqtt.simple import MQTTClient

SSID = "JAISTALL"

MQTT_BROKER = "150.65.230.59"
MQTT_PORT = 1883

STUDENT = "s2510063"

TOPIC_CO2_THRESHOLD = "i483/actuators/{}/co2_threshold/crossed".format(STUDENT)
CLIENT_ID = "{}-led-mcu".format(STUDENT)

LED_PIN = 2
LED_ACTIVE_LOW = False

led = Pin(LED_PIN, Pin.OUT)

blink_enabled = False
led_state = False
last_blink_time = time.ticks_ms()
BLINK_INTERVAL_MS = 500


def set_led(on):
    if LED_ACTIVE_LOW:
        led.value(0 if on else 1)
    else:
        led.value(1 if on else 0)


def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if not wlan.isconnected():
        print("Connecting Wi-Fi...")
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)

        while not wlan.isconnected():
            time.sleep(0.5)

    print("Wi-Fi connected")
    print(wlan.ifconfig())


def mqtt_callback(topic, msg):
    global blink_enabled, led_state

    topic = topic.decode()
    msg = msg.decode().strip()

    print("receive:", topic, msg)

    if topic == TOPIC_CO2_THRESHOLD:
        if msg == "yes":
            blink_enabled = True
            print("LED blink start")

        elif msg == "no":
            blink_enabled = False
            led_state = False
            set_led(False)
            print("LED off")


def connect_mqtt():
    client = MQTTClient(
        client_id=CLIENT_ID,
        server=MQTT_BROKER,
        port=MQTT_PORT
    )

    client.set_callback(mqtt_callback)
    client.connect()
    client.subscribe(TOPIC_CO2_THRESHOLD)

    print("MQTT connected")
    print("Subscribe:", TOPIC_CO2_THRESHOLD)

    return client


connect_wifi()
client = connect_mqtt()

set_led(False)

while True:
    client.check_msg()

    if blink_enabled:
        now = time.ticks_ms()

        if time.ticks_diff(now, last_blink_time) >= BLINK_INTERVAL_MS:
            led_state = not led_state
            set_led(led_state)
            last_blink_time = now

    time.sleep(0.05)