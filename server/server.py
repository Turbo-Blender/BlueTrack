from kafka import KafkaConsumer, KafkaProducer
import json
from pymongo import MongoClient, errors


tmongo_client = MongoClient("mongodb://localhost:27017/")
db = tmongo_client["user_db"]
users = db["users"]


try:
    users.create_index([("username", 1)], unique=True)
    users.create_index([("email", 1)], unique=True)
except errors.DuplicateKeyError:
    print("[SERVER] Warning: nie można utworzyć unikalnych indeksów z powodu istniejących duplikatów.")


producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)


consumer = KafkaConsumer(
    'register_user', 'login_user',
    bootstrap_servers='localhost:9092',
    group_id='user-service',
    auto_offset_reset='latest',
    enable_auto_commit=True,
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

print("[SERVER] Waiting for registration and login data...")

for msg in consumer:
    topic = msg.topic
    data = msg.value

    if topic == 'register_user':
        username = data.get("username")
        email = data.get("email")
        password = data.get("password")
        print(f"[SERVER] Register attempt: {username} / {email}")
        response = {"success": False, "message": ""}

        
        existing = users.find_one({"$or": [{"username": username}, {"email": email}]})
        if existing:
            if existing.get("username") == username and existing.get("email") == email:
                response["message"] = f"Nazwa użytkownika '{username}' i email '{email}' są już używane!"
            elif existing.get("username") == username:
                response["message"] = f"Nazwa użytkownika '{username}' już istnieje!"
            else:
                response["message"] = f"Email '{email}' już istnieje!"
            print(f"[SERVER] {response['message']}")
        else:
            try:
                users.insert_one({"username": username, "email": email, "password": password})
            except errors.PyMongoError as e:
                response["message"] = "Błąd bazy danych podczas rejestracji!"
                print(f"[SERVER] Insert error: {e}")
            else:
                response["success"] = True
                response["message"] = "Zarejestrowano pomyślnie!"
                print(f"[SERVER] User '{username}' registered.")

       
        producer.send('register_user_response', response)
        producer.flush()

    elif topic == 'login_user':
        identifier = data.get("username") 
        password = data.get("password")
        print(f"[SERVER] Login attempt: {identifier}")
        response = {"success": False, "message": ""}

       
        user = users.find_one({"$or": [{"username": identifier}, {"email": identifier}]})
        if user and user.get("password") == password:
            response["success"] = True
            response["message"] = "Zalogowano pomyślnie!"
            print(f"[SERVER] User '{user.get('username')}' login successful.")
        else:
            response["message"] = "Nieprawidłowa nazwa użytkownika/email lub hasło!"
            print(f"[SERVER] Login failed for '{identifier}'.")

       
        producer.send('login_user_response', response)
        producer.flush()
