import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.types import *
from pyspark.sql.functions import from_json, col

# -------------------------------
# Funkcja do aktualizacji stanu
# -------------------------------
def update_active_tracks(user_id, events_iter, state):
    # Pobranie aktualnego stanu
    if state.exists:
        active_tracks = state.get()
    else:
        active_tracks = pd.DataFrame(columns=["track_id"])

    # Złączenie nowych eventów
    new_events = pd.concat(list(events_iter), ignore_index=True)

    # Dodajemy tracki z operation_type="start"
    start_events = new_events[new_events["operation_type"] == "start"]
    if not start_events.empty:
        active_tracks = pd.concat([active_tracks, start_events[["track_id"]]], ignore_index=True)

    # Usuwamy tracki z operation_type="stop"
    stop_events = new_events[new_events["operation_type"] == "stop"]
    if not stop_events.empty:
        active_tracks = active_tracks[~active_tracks["track_id"].isin(stop_events["track_id"])]

    # Aktualizacja stanu
    if not active_tracks.empty:
        state.update(active_tracks)
        yield new_events  # zamiast return
    else:
        state.remove()
        yield pd.DataFrame(columns=new_events.columns)  # pusty generator, ale zachowujemy schemat



# -------------------------------
# Spark init
# -------------------------------
spark = SparkSession.builder \
    .appName("TestState") \
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.6") \
    .getOrCreate()

# -------------------------------
# Schemat eventów
# -------------------------------
schema = StructType([
    StructField("user_id", StringType()),
    StructField("track_id", StringType()),
    StructField("operation_type", StringType())
])

state_schema = StructType([StructField("track_id", StringType())])

# -------------------------------
# Kafka input
# -------------------------------
df_raw = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "127.0.0.1:9092") \
    .option("subscribe", "songs_tracker") \
    .option("startingOffsets", "latest") \
    .load()

df = df_raw.selectExpr("CAST(value AS STRING) as json_string") \
    .withColumn("data", from_json(col("json_string"), schema)) \
    .select("data.*")

# -------------------------------
# ApplyInPandasWithState
# -------------------------------
active_tracks = df.groupBy("user_id").applyInPandasWithState(
    update_active_tracks,
    outputStructType=schema,
    stateStructType=state_schema,
    outputMode="update",
    timeoutConf="NoTimeout"
)

# -------------------------------
# ForeachBatch do podglądu
# -------------------------------
def process_batch(batch_df, epoch_id):
    print(f"\n[Batch {epoch_id}] Active tracks:")
    batch_df.show(truncate=False)

# -------------------------------
# Start streamingu
# -------------------------------
query = active_tracks.writeStream \
    .foreachBatch(process_batch) \
    .outputMode("update") \
    .option("checkpointLocation", "C:/Users/mspyc/Desktop/BlueTrack/checkpoints/spark_test_console") \
    .trigger(processingTime="5 seconds") \
    .start()

print("[SPARK] Streaming started. Send JSON messages to Kafka topic 'songs_tracker'.")
query.awaitTermination()
