# python no_4.py 

import time
from collections import deque
from kafka import KafkaConsumer, KafkaProducer


KAFKA_BROKER = "150.65.230.59:9092"

STUDENT = "s2510063"

TOPIC_BH1750_ILLUMINATION = f"i483-sensors-{STUDENT}-BH1750-illumination"
TOPIC_BH1750_TEMPERATURE = f"i483-sensors-{STUDENT}-BH1750-temperature"
TOPIC_SCD41_CO2 = f"i483-sensors-{STUDENT}-SCD41-co2"

TOPIC_BH1750_AVG = f"i483-sensors-{STUDENT}-BH1750_avg-illumination"
TOPIC_CO2_THRESHOLD = f"i483-actuators-{STUDENT}-co2_threshold-crossed"

WINDOW_SECONDS = 5 * 60
PUBLISH_INTERVAL = 30

# 閾値
CO2_THRESHOLD = 700


consumer = KafkaConsumer(
    TOPIC_BH1750_ILLUMINATION,
    TOPIC_BH1750_TEMPERATURE,
    TOPIC_SCD41_CO2,
    bootstrap_servers=KAFKA_BROKER,
    auto_offset_reset="latest",
    enable_auto_commit=True,
    value_deserializer=lambda v: v.decode("utf-8")
)

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda v: v.encode("utf-8")
)

print("Kafka connected")
print("Subscribe:")
print(" ", TOPIC_BH1750_ILLUMINATION)
print(" ", TOPIC_BH1750_TEMPERATURE)
print(" ", TOPIC_SCD41_CO2)
print("---------")

bh1750_values = deque()

last_avg_publish_time = time.time()
last_co2_state = None


# main
while True:
    records = consumer.poll(timeout_ms=1000)

    now = time.time()

    for topic_partition, messages in records.items():
        for msg in messages:
            topic = msg.topic
            value_str = msg.value

            try:
                value = float(value_str)
            except ValueError:
                print("Invalid value:", topic, value_str)
                continue

            print("receive:", topic, value_str)

            # BH1750の明るさデータ
            if topic == TOPIC_BH1750_ILLUMINATION:
                bh1750_values.append((now, value))
            elif topic == TOPIC_BH1750_TEMPERATURE:
                pass

            # SCD41のCO2データ
            elif topic == TOPIC_SCD41_CO2:
                if value > CO2_THRESHOLD:
                    current_state = "yes"
                else:
                    current_state = "no"

                if current_state != last_co2_state:
                    producer.send(TOPIC_CO2_THRESHOLD, current_state)
                    producer.flush()

                    print("publish:", TOPIC_CO2_THRESHOLD, current_state)

                    # 1-cとの差分
                    # 
                    if current_state == "yes":
                        print("LED should blink")
                    else:
                        print("LED should turn off")

                    last_co2_state = current_state
                    # 

    while bh1750_values and now - bh1750_values[0][0] > WINDOW_SECONDS:
        bh1750_values.popleft()

    if now - last_avg_publish_time >= PUBLISH_INTERVAL:
        if len(bh1750_values) > 0:
            avg = sum(v for _, v in bh1750_values) / len(bh1750_values)
            avg_str = "{:.2f}".format(avg)

            producer.send(TOPIC_BH1750_AVG, avg_str)
            producer.flush()

            print("publish:", TOPIC_BH1750_AVG, avg_str)

        last_avg_publish_time = now