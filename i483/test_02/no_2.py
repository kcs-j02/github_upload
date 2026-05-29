import paho.mqtt.client as mqtt
from datetime import datetime

MQTT_BROKER = "150.65.230.59"
MQTT_PORT = 1883
STUDENT = "s2510063"


# python -c "print('hello')"

TOPIC = "i483/sensors/{}/+/+".format(STUDENT)

def on_connect(client, userdata, flags, rc):
    print("MQTT connected:", rc)
    print("Subscribe topic:", TOPIC)
    client.subscribe(TOPIC)

def on_message(client, userdata, msg):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    value = msg.payload.decode()
    print(now, msg.topic, value)

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop_forever()
