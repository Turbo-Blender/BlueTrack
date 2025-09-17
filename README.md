# BlueTrack – System strumieniowy do analizy odtwarzania muzyki

## Opis projektu
Celem projektu było stworzenie rozproszonego systemu do obsługi użytkowników aplikacji muzycznej oraz analizy trendów muzycznych w czasie rzeczywistym.  
System składa się z trzech głównych modułów:

1. **Client (GUI – `client.py`)**  
   Aplikacja desktopowa z interfejsem graficznym (PySide6), która umożliwia:
   - rejestrację i logowanie użytkowników,
   - przeglądanie losowo dobranych utworów z różnych gatunków,
   - wybór, odtwarzanie i zatrzymywanie utworów,
   - wyświetlanie statystyk najpopularniejszych gatunków muzycznych (Top 5) przetwarzanych w PySpark.

   Komunikacja z serwerem odbywa się poprzez **Apache Kafka**.

2. **Server (`server.py`)**  
   Serwer pełni rolę warstwy backendowej:
   - obsługuje rejestrację i logowanie użytkowników (zabezpieczenie haseł przy użyciu bcrypt + Base64),
   - zarządza sesjami użytkowników,
   - przechowuje informacje w **MongoDB** (kolekcje: `users`, `songs`),
   - wysyła do klienta zestawy losowych utworów w podziale na gatunki,
   - przyjmuje komunikaty o odtwarzaniu utworów (topic `songs_tracker`).

   Dane wejściowe do bazy stanowią utwory z datasetu Spotify (`spotify_dataset.csv`).

3. **Spark Processor (`spark_processor.py`)**  
   Moduł analityczny oparty na **PySpark Structured Streaming**, który:
   - pobiera dane o odtwarzaniu utworów z Kafki (topic `songs_tracker`),
   - utrzymuje stan aktywnych odtworzeń (stateful processing),
   - aktualizuje informacje o końcach odtwarzania,
   - co batch (5 sekund) wyznacza **Top 5 najczęściej odtwarzanych gatunków**,
   - wyniki są przekazywane do klienta.

---

## Architektura systemu
[Client GUI] ←→ [Kafka Topics] ←→ [Server (MongoDB)]
↑
↓
[Spark Processor]


- **Kafka topics**:
  - `register_user` / `register_user_response` – rejestracja użytkownika,
  - `login_user` / `login_user_response` – logowanie,
  - `session_auth` / `session_auth_response` – autoryzacja sesji,
  - `songs_update` / `songs_response` – wysyłanie listy utworów,
  - `songs_tracker` – śledzenie odtwarzania,
  - `top_genres` – wyniki analizy trendów.

---

## Technologie
- **Python** (PySide6, PySpark, Kafka-Python, pymongo, bcrypt)
- **Apache Kafka** – komunikacja asynchroniczna
- **MongoDB** – baza użytkowników i utworów
- **PySpark Structured Streaming** – analiza strumieniowa
- **Pandas** – zarządzanie stanem w Spark
