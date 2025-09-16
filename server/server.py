from kafka import KafkaConsumer, KafkaProducer
from pymongo import MongoClient, errors
import json
import bcrypt
import base64
import uuid
import os
import csv
import random
from dotenv import load_dotenv
# https://www.kaggle.com/datasets/maharshipandya/-spotify-tracks-dataset?resource=download - spotify dataset
load_dotenv()
try:
    mongo_client = MongoClient(os.getenv("MONGODB_URI"), serverSelectionTimeoutMS=5000)
    user_db = mongo_client["database"]
    users = user_db["users"]
    songs = user_db["songs"]
except errors.ConnectionFailure as e:
    print("Problem z połączeniem z bazą MongoDB:", e)
    exit(1)

BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # Path to the main directory

if not songs.find_one():
    with open(os.path.join(BASE_PATH, "data", "spotify_dataset.csv"), newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        tracks_id = []
        track_names = []
        artists = []
        genres = []
        track_duration = []
        for row in reader:
            tracks_id.append(row["track_id"])
            track_names.append(row["track_name"])
            artists.append(row["artists"])
            genres.append(row["track_genre"])
            track_duration.append(row["duration_ms"])

    tracks = []
    for i in range(len(tracks_id)):
        tracks.append({
            "track_id": tracks_id[i],
            "track_name": track_names[i],
            "artist": artists[i],
            "genre": genres[i],
            "duration_ms": track_duration[i]
        })

    songs.insert_many(tracks)

try:
    users.create_index([("username", 1)], unique=True)
    users.create_index([("email", 1)], unique=True)
except errors.DuplicateKeyError:
    print("[SERVER] Warning: nie można utworzyć unikalnych indeksów z powodu istniejących duplikatów.")

try:
    producer = KafkaProducer(
        bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS"),
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
except Exception as e:
    print("Problem z połączeniem z brokerem Kafka:", e)

consumer = KafkaConsumer(
    'register_user', 'login_user', 'session_auth','songs_update','songs_tracker',
    bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS"),
    group_id='user-service',
    auto_offset_reset='latest',
    enable_auto_commit=True,
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

print("[SERVER] Waiting for registration and login data...")


unique_genres = songs.distinct("genre")

for msg in consumer:
    topic = msg.topic
    data = msg.value

    if topic == 'register_user':
        username = data.get("username")
        email = data.get("email")
        password = data.get("password")
        print(f"[SERVER] Register attempt: {username} / {email}")
        
        response = {"success": False, "message": "", "session_id": None, "user_id": None}
        
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
                salt = bcrypt.gensalt()
                hash_bytes = bcrypt.hashpw(password.encode('utf-8'), salt)
                hashed_password = base64.b64encode(hash_bytes).decode('utf-8')
                users.insert_one({"username": username, "email": email, "password": hashed_password})
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
        
        response = {"success": False, "message": "", "session_id": None, "user_id": None}
       
        user = users.find_one({"$or": [{"username": identifier}, {"email": identifier}]})
        if user and bcrypt.checkpw(password.encode('utf-8'), base64.b64decode(user.get("password").encode('utf-8'))):
            session_id = str(uuid.uuid4())
            users.update_one({"_id": user["_id"]}, {"$set": {"session_id": session_id}})

            response["success"] = True
            response["message"] = "Zalogowano pomyślnie!"
            response["session_id"] = session_id
            response["user_id"] = str(user.get("_id"))
            print(f"[SERVER] User '{user.get('username')}' login successful.")
        else:
            response["message"] = "Nieprawidłowa nazwa użytkownika/email lub hasło!"
            print(f"[SERVER] Login failed for '{identifier}'.")

        producer.send('login_user_response', response)
        producer.flush()
    
            
    elif topic == 'session_auth':
        session_id = data.get("session_id")
        user = users.find_one({"session_id": session_id})
        response = {"success": False, "message": "", "session_id": session_id}
        print(f"[SERVER] Session auth attempt for session ID: {session_id}")
        if user:
            response["success"] = True
            response["message"] = "Sesja jest ważna."
            response["session_id"] = session_id
        else:
            response["message"] = "Sesja wygasła lub jest nieprawidłowa."
        producer.send('session_auth_response', response)
        producer.flush()

    elif topic == 'songs_update':

        sampled_20_genres = random.sample(unique_genres, min(len(unique_genres), 20))

        login_random_tracks = {}

        for genre in sampled_20_genres:

            tracks = list(songs.find({"genre": genre}))
            random_tracks = random.sample(tracks, min(len(tracks), 20))
            login_random_tracks[genre] = {"track_names": [track["track_name"] for track in random_tracks],
                                          "artists": [track["artist"] for track in random_tracks],
                                          "tracks_id": [track["track_id"] for track in random_tracks],
                                          "duration_ms":[track["duration_ms"] for track in random_tracks]}

        response = [login_random_tracks,sampled_20_genres]
        
        producer.send("songs_response", response)
        producer.flush()
