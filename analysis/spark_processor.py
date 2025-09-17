import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, TimestampType, IntegerType   
from pyspark.sql.functions import from_json, col, to_timestamp, expr
from dotenv import load_dotenv
import os
load_dotenv()
# -------------------------------
# Funkcja do aktualizacji aktywnych tracków
# -------------------------------
# -------------------------------
# Funkcja do aktualizacji aktywnych tracków
# -------------------------------
def update_active_tracks(key, events_iter, state):
    now = pd.Timestamp.utcnow()
    
    # stan istniejący
    if state.exists:
        active_tracks = state.get()
    else:
        active_tracks = pd.DataFrame(columns=["track_id", "end_ts"])

    # events_iter to iterator po Pandas DataFrames
    try:
        new_events = pd.concat(list(events_iter), ignore_index=True)
        print(f"[DEBUG] New events rows: {len(new_events)}")
    except Exception as e:
        print(f"[ERROR] Failed to convert events_iter to DataFrame: {e}")
        return

    if new_events.empty and not state.exists:
        return

    # Łączymy stare + nowe
    all_events = pd.concat([active_tracks, new_events[["track_id", "end_ts"]]], ignore_index=True)

    # STOP events - usuwamy tracki z operation_type=stop
    stop_events = new_events[new_events["operation_type"] == "stop"]
    if not stop_events.empty:
        all_events = all_events[~all_events["track_id"].isin(stop_events["track_id"])]

    # Filtrowanie aktywnych
    all_events["end_ts"] = pd.to_datetime(all_events["end_ts"])
    active = all_events[all_events["end_ts"] > now]

    # Aktualizacja stanu
    if not active.empty:
        state.update(active)
        yield new_events  # <- tutaj używamy yield
    else:
        state.remove()
        return  # pusty generator


# -------------------------------
# Schemat wejściowy
# -------------------------------
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

# -------------------------------
# Spark init
# -------------------------------
spark = SparkSession.builder \
    .appName("KafkaSparkStreamingTest") \
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1") \
    .config("spark.driver.extraJavaOptions", "--add-opens=java.base/sun.misc=ALL-UNNAMED --add-opens=java.base/java.nio=ALL-UNNAMED") \
    .config("spark.executor.extraJavaOptions", "--add-opens=java.base/sun.misc=ALL-UNNAMED --add-opens=java.base/java.nio=ALL-UNNAMED") \
    .getOrCreate()

print("[SPARK] Connected to Kafka.")

# -------------------------------
# Kafka input stream
# -------------------------------
df_raw = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", os.getenv("KAFKA_BOOTSTRAP_SERVERS")) \
    .option("subscribe", "songs_tracker") \
    .option("startingOffsets", "latest") \
    .option("failOnDataLoss", "false") \
    .load()

df = df_raw.selectExpr("CAST(value AS STRING) as json_string") \
    .withColumn("data", from_json(col("json_string"), schema)) \
    .select("data.*")

df = df.withColumn("start_time", to_timestamp(col("start_time")))
df = df.withColumn("duration_s", col("duration_ms") / 1000.0)
df = df.withColumn(
    "end_ts",
    expr("CAST((CAST(start_time AS DOUBLE) + duration_s) AS TIMESTAMP)")
)

# -------------------------------
# Active tracks with state
# -------------------------------
active_tracks = df.groupBy("user_id").applyInPandasWithState(
    update_active_tracks,
    outputStructType=schema_IO,
    stateStructType=StructType([
        StructField("track_id", StringType()),
        StructField("end_ts", TimestampType())
    ]),
    outputMode="update",
    timeoutConf="NoTimeout"
)

# -------------------------------
# ForeachBatch -> wyświetl TOP5 w konsoli
# -------------------------------
def process_batch(batch_df, epoch_id):
    if batch_df.rdd.isEmpty():  # poprawny warunek dla pustego batcha
        print(f"[DEBUG] Batch {epoch_id} is empty")
        return

    top5 = batch_df.groupBy("genre").count().orderBy(col("count").desc()).limit(5)
    print(f"\n[DEBUG] Batch {epoch_id} TOP5 genres:")
    top5.show(truncate=False)

# -------------------------------
# Stream start
# -------------------------------
query = active_tracks.writeStream \
    .foreachBatch(process_batch) \
    .outputMode("update") \
    .trigger(processingTime="5 seconds") \
    .start()

print("[SPARK] Streaming started. Send messages to Kafka topic 'songs_tracker' now...")

query.awaitTermination()
