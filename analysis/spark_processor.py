import os
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.types import *
from pyspark.sql.functions import from_json, col, to_timestamp, expr
from pyspark.sql.streaming.state import GroupState, GroupStateTimeout


def update_active_tracks(key, events_iterator, state: GroupState):

    now = pd.Timestamp.now(tz='UTC')

    # Jeśli jest stan, odczytaj go
    if state.exists:
        state_df = state.get()
    else:
        state_df = pd.DataFrame(columns=events_iterator.columns)

    # Złącz z nowymi eventami
    new_events = pd.concat(list(events_iterator))

    # Połącz stare + nowe eventy, zachowując tylko te z end_ts > now
    all_events = pd.concat([state_df, new_events])
    all_events["end_ts"] = pd.to_datetime(all_events["end_ts"])
    active_events = all_events[all_events["end_ts"] > now]

    # Aktualizuj stan
    if not active_events.empty:
        state.update(active_events)
    else:
        state.remove()

    return active_events

schema = StructType([
    StructField("user_id", StringType()),
    StructField("track_id", StringType()),
    StructField("operation_type", StringType()),
    StructField("start_time", TimestampType()),
    StructField("duration_ms", IntegerType()),
    StructField("genre", StringType())
    ])

schema_IO = StructType([
    StructField("user_id", StringType()),
    StructField("track_id", StringType()),
    StructField("operation_type", StringType()),
    StructField("end_ts", TimestampType()),
    StructField("duration_ms", IntegerType()),
    StructField("genre", StringType())
    ])

spark = SparkSession.builder \
    .appName("KafkaSparkStreaming") \
    .config("spark.jars.packages",
            "org.apache.spark:spark-sql-kafka-0-10_2.13:3.4.0,"
            "org.mongodb.spark:mongo-spark-connector_2.12:10.5.0") \
    .config("spark.mongodb.output.uri", "mongodb://localhost:27017/genres_count") \
    .getOrCreate()

print("[SPARK] Connected to MongoDB.")



df_raw = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("subscribe", "songs_tracker") \
    .option("startingOffsets", "latest") \
    .load()

df = df_raw.selectExpr("CAST(value AS STRING) as json_string") \
        .withColumn("data", from_json(col("json_string"), schema)) \
        .select("data.*")

df = df.withColumn("start_time", to_timestamp(col("start_time")))

# Convert duration from ms to seconds (float)
df = df.withColumn("duration_s", col("duration_ms") / 1000.0)

# Calculate end_ts with full ms accuracy
df_parsed = df.withColumn(
    "end_ts",
    expr("CAST((CAST(start_time AS DOUBLE) + duration_s) AS TIMESTAMP)")
)


stream_with_active_tracks = df_parsed.groupBy("user_id") \
    .applyInPandasWithState(
        update_active_tracks,
        outputStructType=schema_IO,
        stateStructType=schema_IO,
        outputMode="update",
        timeoutConf="NoTimeout"
    )



active_tracks_stream_with_watermark = stream_with_active_tracks.withWatermark("end_ts", "20 minutes")

# Następnie agregacja z watermarkiem
genre_counts = active_tracks_stream_with_watermark.groupBy("genre").count()

top5_genres = genre_counts.orderBy(col("count").desc()).limit(5)

top5_genres.writeStream \
    .format("mongodb") \
    .option("checkpointLocation", "/tmp/checkpoints/mongo_genres") \
    .outputMode("complete") \
    .trigger(processingTime='5 seconds') \
    .start() \
    .awaitTermination()