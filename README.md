### Instalacja ###

1. Pobranie kafki 

    https://kafka.apache.org/downloads - kafka_2.13-3.4.0.tgz z Binary downloads
    w folderze C:\kafka skopiować zawartość kafka_2.13-3.4.0.tgz , powino wyglądać to tak C:\kafka\kafka_2.13-3.4.0
    
2. Pobranie MongoDB

    https://fastdl.mongodb.org/windows/mongodb-windows-x86_64-8.0.11-signed.msi - pobrać (MongoDB compass opcjonalne)

3. Konfiguracja

    wrzuć start_kafka.ps1 do folderu C:\kafka\kafka_2.13-3.4.0

4. Pobierz biblioteki z requirements.txt

    dla pip-a: pip install -r requirements.txt


Komendy w powershell:

1. Uruchomienie kafka

    cd C:\kafka\kafka_2.13-3.4.0
    .\start_kafka.ps1

2. Uruchomienie serwera

    do folderu roboczego z plikami server.py i client.py
    py server.py

3. Uruchomienie client-a 

    do folderu roboczego z plikami server.py i client.py
    py client.py