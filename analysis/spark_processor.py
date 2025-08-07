from pyspark.sql import SparkSession
from pyspark.sql.types import *
from pyspark.sql.functions import from_json, col, to_timestamp, expr
from pyspark.sql.streaming import GroupState, GroupStateTimeout
from datetime import datetime, timezone


def update_user_state(user_id, events_iterator, state: GroupState):
    now = datetime.now(timezone.utc)

    current_state = state.get() if state.exists else None

    for event in events_iterator:
        new_end = event.end_ts
        if new_end > now:
            state.update(event)
            return [event]
        else:
            state.remove()
            return []

    if current_state and current_state.end_ts > now:
        return [current_state]
    else:
        state.remove()
        return []
    
    
    

schema = StructType([
    StructField("user_id", StringType()),
    StructField("track_id", StringType()),
    StructField("operation_type", StringType()),
    StructField("start_time", StringType()),
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

user_grouped = df.groupByKey(lambda row: row.user_id)

stream_with_active_tracks = user_grouped \
    .mapGroupsWithState(
        update_user_state,
        outputMode="update",
        stateTimeoutConf=GroupStateTimeout.NoTimeout()
    )



active_tracks_stream = stream_with_active_tracks.flatMap(lambda tracks: tracks)


genre_counts = active_tracks_stream.groupBy("genre").count()


top5_genres = genre_counts.orderBy(col("count").desc()).limit(5)

top5_genres.writeStream \
    .format("mongo") \
    .option("checkpointLocation", "/tmp/checkpoints/mongo_genres") \
    .outputMode("complete") \
    .start() \
    .awaitTermination()