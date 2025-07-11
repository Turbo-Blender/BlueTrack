from kafka import KafkaConsumer
import json
from pymongo import MongoClient

# Połączenie z MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["user_db"]
users_collection = db["users"]

# Kafka consumer
consumer = KafkaConsumer(
    'register_user',
    bootstrap_servers='localhost:9092',
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    auto_offset_reset='earliest',
    enable_auto_commit=True
)

print("[SERVER] Waiting for registration data...")

for message in consumer:
    user_data = message.value
    print(f"[SERVER] Received data: {user_data}")

    # Sprawdź czy user już istnieje
    existing_user = users_collection.find_one({"username": user_data["username"]})
    if existing_user:
        print(f"[SERVER] User {user_data['username']} already exists!")
    else:
        users_collection.insert_one(user_data)
        print(f"[SERVER] Saved {user_data['username']} to MongoDB")
