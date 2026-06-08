// これで実行
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
import org.apache.flink.streaming.api.functions.windowing.ProcessWindowFunction;
import org.apache.flink.streaming.api.windowing.assigners.SlidingProcessingTimeWindows;
import org.apache.flink.streaming.api.windowing.time.Time;
import org.apache.flink.streaming.api.windowing.windows.TimeWindow;
import org.apache.flink.util.Collector;
import org.apache.kafka.clients.consumer.ConsumerRecord;

import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class Kadai3Flink {

    static final String KAFKA_BROKER = "150.65.230.59:9092";
    static final String STUDENT = "s2510063";

    static final String TOPIC_BH1750_ILLUMINATION =
            "i483-sensors-" + STUDENT + "-BH1750-illumination";

    static final String TOPIC_BH1750_TEMPERATURE =
            "i483-sensors-" + STUDENT + "-BH1750-temperature";

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
                        TOPIC_BH1750_TEMPERATURE,
                        TOPIC_SCD41_CO2
                ))
                .setGroupId("kadai3-1a-" + STUDENT)
                .setStartingOffsets(OffsetsInitializer.latest())
                .setDeserializer(new SensorDeserializer())
                .build();

        DataStream<SensorRecord> input = env.fromSource(
                source,
                WatermarkStrategy.noWatermarks(),
                "Kafka Source"
        );

        DataStream<AnalyticsRecord> result = input
                .keyBy(r -> r.student + "|" + r.sensor + "|" + r.dataType)
                .window(SlidingProcessingTimeWindows.of(
                        Time.minutes(5),
                        Time.seconds(30)
                ))
                .process(new AnalyticsWindowFunction());

        KafkaSink<AnalyticsRecord> sink = KafkaSink.<AnalyticsRecord>builder()
                .setBootstrapServers(KAFKA_BROKER)
                .setRecordSerializer(
                        KafkaRecordSerializationSchema.<AnalyticsRecord>builder()
                                .setTopicSelector((AnalyticsRecord record) -> record.outputTopic)
                                .setValueSerializationSchema(new AnalyticsValueSerializer())
                                .build()
                )
                .build();

        result.sinkTo(sink);

        System.out.println("Flink job started");
        env.execute("Kadai3 1-a Flink Analytics");
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

    public static class AnalyticsWindowFunction
            extends ProcessWindowFunction<SensorRecord, AnalyticsRecord, String, TimeWindow> {

        @Override
        public void process(
                String key,
                Context context,
                Iterable<SensorRecord> records,
                Collector<AnalyticsRecord> out
        ) {
            double min = Double.MAX_VALUE;
            double max = -Double.MAX_VALUE;
            double sum = 0.0;
            int count = 0;

            SensorRecord sample = null;

            for (SensorRecord r : records) {
                sample = r;
                min = Math.min(min, r.value);
                max = Math.max(max, r.value);
                sum += r.value;
                count++;
            }

            if (count == 0 || sample == null) {
                return;
            }

            double avg = sum / count;

            publish(out, sample, "min", min);
            publish(out, sample, "max", max);
            publish(out, sample, "avg", avg);
        }

        private void publish(
                Collector<AnalyticsRecord> out,
                SensorRecord r,
                String metric,
                double value
        ) {
            String outputTopic =
                    "i483-sensors-" + r.student
                            + "-analytics-"
                            + r.student + "_" + r.sensor + "_" + metric
                            + "-" + r.dataType;

            String valueStr = String.format("%.2f", value);

            System.out.println("publish: " + outputTopic + " " + valueStr);

            out.collect(new AnalyticsRecord(outputTopic, valueStr));
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