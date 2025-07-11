### Instalacja ###

1. Pobranie kafki

    https://kafka.apache.org/downloads - kafka_2.13-3.4.0.tgz z Binary downloads
    w folderze C:\kafka (jeżeli nie istnieje to stworzyć) skopiować zawartość kafka_2.13-3.4.0.tgz , powino wyglądać to tak C:\kafka\kafka_2.13-3.4.0
    
2. Pobranie MongoDB

    https://fastdl.mongodb.org/windows/mongodb-windows-x86_64-8.0.11-signed.msi - pobrać (MongoDB compass opcjonalne)

3. Pobranie Java w odpowiedniej wersji

    https://adoptium.net/temurin/releases?version=11&os=any&arch=any - link do pobrania

4. Pobieranie Spark oraz konfiguracja

    https://spark.apache.org/downloads.html - wybrać wersję 3.4.4 i typ pakietu "Pre-built for Apache Hadoop 3.4 and later"
    w folderze C:\spark (jeżeli nie istnieje to stworzyć) skopiować zawartość spark-4.0.0-bin-hadoop3.tgz , powino wyglądać to tak C:\spark\spark-3.4.4-bin-hadoop3

5. Pobranie Hadoop

    https://github.com/cdarlint/winutils/tree/master/hadoop-3.2.0/bin - pobrać wszystkie pliki z tego folderu

    stworzyć folder C:\hadoop\bin i wrzucić wszystkie pliki pobrane z link-u wyżej

6. Pobranie Visual C++ Redistributable

    https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170

7. Stworzyć venv z pythonem 3.9.18

    Najlepiej pobrać podanego python-a i za pomocą ścieżki do danej wersji pythona stworzyć venv

    https://github.com/xenago/python_win_redist/releases/download/UserBuild_2023.06.07_18-50/python-3.9.18-amd64.exe - możliwy link do pobrania (nie trzeba z tego link-u, można pobrać inaczej)

    "ścieżka do pliku python.exe odpowiedniej wersji pythona" -m venv venv

    np. C:\Python311\python.exe -m venv venv

8. Sprawdzenie ścieżek

    w set_env.ps1 są podane ścieżki do odpowiednich folderów/plików niezbędnych do uruchomienia programu, należy sprawdzić czy wszystkie ścieżki się zgadzają

9. Konfiguracja

    wrzuć start_kafka.ps1 z folderu config do folderu C:\kafka\kafka_2.13-3.4.0

10. Pobierz biblioteki z requirements.txt

    dla pip-a: pip install -r requirements.txt


### Komendy w powershell do uruchomienia programu (każdy krok to osobny powershell), najlepiej uruchamiać jako administrator: ###

1. Uruchomienie kafka

    cd C:\kafka\kafka_2.13-3.4.0
    .\start_kafka.ps1

2. Uruchomienie serwera

    Przejdź do folderu roboczego BlueTrack

    ./venv/Scripts/activate
    py server/server.py

3. Uruchomienie client-a 

    Przejdź do folderu roboczego BlueTrack

    ./venv/Scripts/activate
    py client/client.py

4. Uruchomienie Spark-a

    Przejdź do folderu roboczego BlueTrack

    ./config/set_env.ps1
    ./venv/Scripts/activate
    py analysis/spark_processor.py
