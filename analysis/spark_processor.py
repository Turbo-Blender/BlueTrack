from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .appName("MongoSparkConnectorReadUsers") \
    .config("spark.jars.packages", "org.mongodb.spark:mongo-spark-connector_2.12:10.5.0") \
    .getOrCreate()

print("[SPARK] Connected to MongoDB.")

df = spark.read.format("mongodb") \
    .option("connection.uri", "mongodb://127.0.0.1:27017") \
    .option("database", "user_db") \
    .option("collection", "users") \
    .load()

print("[SPARK] Read data from MongoDB.")

df.show(truncate=False)

count = df.count()
print(f"[SPARK] Number of users in DB: {count}")

if count > 0:
    df.coalesce(1).write.mode("overwrite").option("header", True).csv("user_export")
    print("[SPARK] Exported data to folder 'user_export'")
else:
    print("[SPARK] No data to export.")

spark.stop()
print("[SPARK] Finished.")
