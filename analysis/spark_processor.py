import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.types import *
from pyspark.sql.functions import from_json, col, to_timestamp, expr
from pyspark.sql.streaming.state import GroupState
import json

# -------------------------------
# Funkcja do aktualizacji aktywnych tracków
# -------------------------------
def update_active_tracks(key, events_iter, state: GroupState):
    now = pd.Timestamp.now(tz="UTC")
    print(f"[DEBUG] Processing user_id={key} at {now}")

    # stan istniejący
    if state.exists:
        state_df = state.get()
        print(f"[DEBUG] Existing state rows: {len(state_df)}")
    else:
        state_df = pd.DataFrame(
            columns=["user_id", "track_id", "operation_type", "end_ts", "duration_ms", "genre"]
        )
        print("[DEBUG] No existing state, creating empty DataFrame")

    # konwersja iteratora na DF
    try:
        new_events = pd.DataFrame(list(events_iter))
        print(f"[DEBUG] New events rows: {len(new_events)}")
    except Exception as e:
        print(f"[ERROR] Failed to convert events_iter to DataFrame: {e}")
        return []

    if new_events.empty:
        print("[DEBUG] No new events, returning existing state")
        return [state_df] if state.exists else []

    # łączymy stare + nowe
    all_events = pd.concat([state_df, new_events], ignore_index=True)

    # jeśli jest STOP -> usuń ten track
    stop_events = all_events[all_events["operation_type"] == "stop"]
    if not stop_events.empty:
        all_events = all_events[~all_events["track_id"].isin(stop_events["track_id"])]
        print(f"[DEBUG] Removed stopped tracks: {len(stop_events)}")

    # filtrujemy tylko aktywne (jeszcze nie skończone)
    all_events["end_ts"] = pd.to_datetime(all_events["end_ts"])
    active = all_events[all_events["end_ts"] > now]
    print(f"[DEBUG] Active tracks after filtering: {len(active)}")

    # update state
    if not active.empty:
        state.update(active)
        print("[DEBUG] State updated")
        return [active]  # <- UWAGA: applyInPandasWithState wymaga iterable of DataFrame
    else:
        state.remove()
        print("[DEBUG] State removed (no active tracks)")
        return []

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
    .appName("KafkaSparkStreaming") \
    .config("spark.jars.packages",
            "org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.0") \
    .getOrCreate()

print("[SPARK] Connected to Kafka.")

# -------------------------------
# Kafka input stream
# -------------------------------
df_raw = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("subscribe", "songs_tracker") \
    .option("startingOffsets", "latest") \
    .option("kafka.group.id", "my_unique_group_id_123") \
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
    stateStructType=schema_IO,
    outputMode="update",
    timeoutConf="NoTimeout"
)

# -------------------------------
# ForeachBatch -> wyślij TOP5 do Kafka
# -------------------------------
def process_batch(batch_df, epoch_id):
    row_count = batch_df.count()
    print(f"[DEBUG] Processing batch_id={epoch_id}, rows={row_count}")
    if batch_df.rdd.isEmpty():
        print("[DEBUG] Batch is empty, skipping")
        return

    # policz gatunki
    top5 = (batch_df.groupBy("genre").count()
            .orderBy(col("count").desc())
            .limit(5))

    print(f"[DEBUG] Top genres:")
    top5.show(truncate=False)

    # zamiana na JSON (Kafka value musi być string)
    result_df = top5.selectExpr(
        "CAST(genre AS STRING) as key",
        "to_json(struct(*)) as value"
    )

    (result_df.write
        .format("kafka")
        .option("kafka.bootstrap.servers", "localhost:9092")
        .option("topic", "top_genres")
        .save())

# -------------------------------
# Stream start
# -------------------------------
query = active_tracks.writeStream \
    .foreachBatch(process_batch) \
    .outputMode("update") \
    .trigger(processingTime="5 seconds") \
    .start()

query.awaitTermination()
