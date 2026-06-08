// mvn clean package
// java -jar .\target\kadai3-flink-1.0.jar

package i483;

import org.apache.flink.api.common.eventtime.WatermarkStrategy;
import org.apache.flink.api.common.serialization.SerializationSchema;
import org.apache.flink.api.common.typeinfo.TypeInformation;
import org.apache.flink.connector.kafka.sink.KafkaRecordSerializationSchema;
import org.apache.flink.connector.kafka.sink.KafkaSink;
import org.apache.flink.connector.kafka.source.KafkaSource;
import org.apache.flink.connector.kafka.source.enumerator.initializer.OffsetsInitializer;
import org.apache.flink.connector.kafka.source.reader.deserializer.KafkaRecordDeserializationSchema;
import org.apache.flink.streaming.api.datastream.DataStream;
import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;
import org.apache.flink.streaming.api.functions.ProcessFunction;
import org.apache.flink.util.Collector;
import org.apache.kafka.clients.consumer.ConsumerRecord;

import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.LinkedList;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class Kadai3Flink {

    static final String KAFKA_BROKER = "150.65.230.59:9092";
    static final String STUDENT = "s2510063";

    static final String TOPIC_BH1750_ILLUMINATION =
            "i483-sensors-" + STUDENT + "-BH1750-illumination";

    static final String TOPIC_SCD41_CO2 =
            "i483-sensors-" + STUDENT + "-SCD41-co2";

    public static void main(String[] args) throws Exception {

        StreamExecutionEnvironment env =
                StreamExecutionEnvironment.getExecutionEnvironment();

        env.setParallelism(1);

        KafkaSource<SensorRecord> source = KafkaSource.<SensorRecord>builder()
                .setBootstrapServers(KAFKA_BROKER)
                .setTopics(Arrays.asList(
                        TOPIC_BH1750_ILLUMINATION,
                        TOPIC_SCD41_CO2
                ))
                .setGroupId("kadai3-3b-" + STUDENT)
                .setStartingOffsets(OffsetsInitializer.latest())
                .setDeserializer(new SensorDeserializer())
                .build();

        DataStream<SensorRecord> input = env.fromSource(
                source,
                WatermarkStrategy.noWatermarks(),
                "Kafka Source"
        );

        DataStream<AnalyticsRecord> result = input
                .process(new OccupancyProcessFunction());

        KafkaSink<AnalyticsRecord> sink = KafkaSink.<AnalyticsRecord>builder()
                .setBootstrapServers(KAFKA_BROKER)
                .setRecordSerializer(
                        KafkaRecordSerializationSchema.<AnalyticsRecord>builder()
                                .setTopicSelector(record -> record.outputTopic)
                                .setValueSerializationSchema(new AnalyticsValueSerializer())
                                .build()
                )
                .build();

        result.sinkTo(sink);

        System.out.println("Flink job started");
        env.execute("Kadai3 3-b Occupancy Detection");
    }

    public static class SensorRecord {
        public String student;
        public String sensor;
        public String dataType;
        public double value;

        public SensorRecord() {}

        public SensorRecord(String student, String sensor, String dataType, double value) {
            this.student = student;
            this.sensor = sensor;
            this.dataType = dataType;
            this.value = value;
        }
    }

    public static class AnalyticsRecord {
        public String outputTopic;
        public String value;

        public AnalyticsRecord() {}

        public AnalyticsRecord(String outputTopic, String value) {
            this.outputTopic = outputTopic;
            this.value = value;
        }
    }

    public static class SensorDeserializer
            implements KafkaRecordDeserializationSchema<SensorRecord> {

        private static final Pattern TOPIC_PATTERN =
                Pattern.compile("^i483-sensors-(s\\d+)-([A-Za-z0-9]+)-(.+)$");

        @Override
        public void deserialize(
                ConsumerRecord<byte[], byte[]> record,
                Collector<SensorRecord> out
        ) {
            String topic = record.topic();
            String valueStr = new String(record.value(), StandardCharsets.UTF_8).trim();

            Matcher matcher = TOPIC_PATTERN.matcher(topic);
            if (!matcher.matches()) {
                return;
            }

            try {
                String student = matcher.group(1);
                String sensor = matcher.group(2).toUpperCase();
                String dataType = matcher.group(3).toLowerCase();
                double value = Double.parseDouble(valueStr);

                System.out.println("receive: " + topic + " " + valueStr);

                out.collect(new SensorRecord(student, sensor, dataType, value));

            } catch (NumberFormatException e) {
                System.out.println("Invalid value: " + topic + " " + valueStr);
            }
        }

        @Override
        public TypeInformation<SensorRecord> getProducedType() {
            return TypeInformation.of(SensorRecord.class);
        }
    }

    public static class OccupancyProcessFunction
            extends ProcessFunction<SensorRecord, AnalyticsRecord> {

        private double latestCo2 = 0.0;
        private double latestIllumination = 0.0;

        private final LinkedList<Co2History> co2History = new LinkedList<>();

        private static final long WINDOW_MS = 5 * 60 * 1000;
        private static final double CO2_HIGH_THRESHOLD = 1000.0;
        private static final double CO2_SUB_THRESHOLD = 900.0;
        private static final double ILLUMINATION_THRESHOLD = 100.0;
        private static final double CO2_RISE_THRESHOLD = 50.0;

        @Override
        public void processElement(
                SensorRecord r,
                Context ctx,
                Collector<AnalyticsRecord> out
        ) {
            long now = System.currentTimeMillis();

            if (r.sensor.equals("SCD41") && r.dataType.equals("co2")) {
                latestCo2 = r.value;

                co2History.add(new Co2History(now, r.value));

                while (!co2History.isEmpty()
                        && now - co2History.getFirst().timestamp > WINDOW_MS) {
                    co2History.removeFirst();
                }
            }

            if (r.sensor.equals("BH1750") && r.dataType.equals("illumination")) {
                latestIllumination = r.value;
            }

            boolean co2High = latestCo2 > CO2_HIGH_THRESHOLD;
            boolean lightAndCo2 =
                    latestCo2 > CO2_SUB_THRESHOLD
                            && latestIllumination > ILLUMINATION_THRESHOLD;
            boolean co2Rising = isCo2Rising();

            String occupancy =
                    (co2High || lightAndCo2 || co2Rising)
                            ? "occupied"
                            : "vacant";

            String value = occupancy.equals("occupied") ? "1" : "0";

            String outputTopic =
                    "i483-sensors-" + r.student + "-analytics-room-occupancy";

            System.out.println(
                    "publish: " + outputTopic
                            + " occupancy=" + occupancy
                            + " value=" + value
                            + " co2=" + latestCo2
                            + " illumination=" + latestIllumination
                            + " co2Rising=" + co2Rising
            );

            out.collect(new AnalyticsRecord(outputTopic, value));
        }

        private boolean isCo2Rising() {
            if (co2History.size() < 2) {
                return false;
            }

            double first = co2History.getFirst().value;
            double last = co2History.getLast().value;

            return last - first >= CO2_RISE_THRESHOLD;
        }

        private static class Co2History {
            long timestamp;
            double value;

            Co2History(long timestamp, double value) {
                this.timestamp = timestamp;
                this.value = value;
            }
        }
    }

    public static class AnalyticsValueSerializer
            implements SerializationSchema<AnalyticsRecord> {

        @Override
        public byte[] serialize(AnalyticsRecord record) {
            return record.value.getBytes(StandardCharsets.UTF_8);
        }
    }
}