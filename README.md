### UWAGA! ###

Instalacja została wykonana, aby działała na konkrentych nazwach folderów oraz na konkretnych wersjach programów.
Będzie działała tylko i wyłącznie na windowsie.
Instalator lub instrukcja instalacji dla większej ilości wersji i innych systemów operacyjnych zostanie opracowana w późniejszych etapach rozwijania aplikacji.

### Instalacja ###

1. Pobranie oraz konfiguracja kafki

    Pobrać kafkę (https://kafka.apache.org/downloads - kafka_2.13-3.4.0.tgz (Scala 2.13) z Binary downloads)

    Do folderu C:\kafka (jeżeli nie istnieje to stworzyć) skopiować zawartość kafka_2.13-3.4.0.tgz.
    Powino wyglądać to tak C:\kafka\kafka_2.13-3.4.0. 

    Następnie zmienić nazwę folderu z kafka_2.13-3.4.0 na kafka-3.4.0 (finalny wynik - C:\kafka\kafka-3.4.0)

    W pliku server.properties, który znajduje się w ścieżce ../kafka-3.4.0/config/server.properties zmienić linijkę log.dirs=/tmp/kafka-logs na log.dirs=C:/kafka/kafka-3.4.0/kafka-logs

2. Pobranie oraz konfiguracja ZooKeeper-a (potrzebny, aby kafka działała)

    Pobrać Zookeeper-a (https://zookeeper.apache.org/releases.html Latest Stable Version - wersja 3.8.4)

    Do folderu C:\zookeeper (jeżeli nie istnieje to stworzyć) skopiować zawartość apache-zookeeper-3.8.4-bin.tar.gz
    Powino wyglądać to tak C:\kafka\apache-zookeeper-3.8.4-bin

    Następnie zmienić nazwę folderu z apache-zookeeper-3.8.4-bin na zookeeper-3.8.4 (finalny wynik - C:\zookeeper\zookeeper-3.8.4)

    Do folderu zookeeper-3.8.4 przekopiować plik start_zk.ps1 (ścieżka do pliku ../BlueTrack/config/start_zk.ps1 gdzie BlueTrack to folder projektu ) 

    Do folderu zookeeper-3.8.4/conf przekopiować plik zoo.cfg (ścieżka do pliku ../BlueTrack/config/zoo.cfg gdzie BlueTrack to folder projektu )

3. Pobranie MongoDB

    https://fastdl.mongodb.org/windows/mongodb-windows-x86_64-8.0.11-signed.msi - pobrać (MongoDB compass opcjonalne)

4. Pobranie Java w odpowiedniej wersji (wersja Java 11 z link-u jest kompatybilna)

    https://adoptium.net/temurin/releases?version=11&os=any&arch=any - link do pobrania

5. Pobieranie Spark oraz konfiguracja

    https://spark.apache.org/downloads.html - wybrać wersję 3.4.4 i typ pakietu "Pre-built for Apache Hadoop 3.4 and later"
    w folderze C:\spark (jeżeli nie istnieje to stworzyć) skopiować zawartość spark-4.0.0-bin-hadoop3.tgz , powino wyglądać to tak C:\spark\spark-3.4.4-bin-hadoop3

6. Pobranie Hadoop

    https://github.com/cdarlint/winutils/tree/master/hadoop-3.2.0/bin - pobrać wszystkie pliki z tego folderu

    stworzyć folder C:\hadoop\bin i wrzucić wszystkie pliki pobrane z link-u wyżej

7. Pobranie Visual C++ Redistributable

    https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170

8. Stworzyć venv z pythonem 3.9.18

    Najlepiej pobrać podanego python-a i za pomocą ścieżki do danej wersji pythona stworzyć venv

    https://github.com/xenago/python_win_redist/releases/download/UserBuild_2023.06.07_18-50/python-3.9.18-amd64.exe - możliwy link do pobrania (nie trzeba z tego link-u, można pobrać inaczej)

    "ścieżka do pliku python.exe odpowiedniej wersji pythona" -m venv venv

    np. C:\Python3918\python.exe -m venv venv

9. Sprawdzenie ścieżek

    w set_env.ps1 są podane ścieżki do odpowiednich folderów/plików niezbędnych do uruchomienia programu, należy sprawdzić czy wszystkie ścieżki się zgadzają


10. Pobierz biblioteki z requirements.txt

    Na początku należy aktywować venv (komenda w folderze roboczym, czyli BlueTrack - ./venv/Scripts/activate )

    dla pip-a: pip install -r requirements.txt


### Komendy w powershell do uruchomienia programu (każdy krok to osobny powershell), najlepiej uruchamiać jako administrator: ###

1. Uruchomienie kafka i ZooKeeper-a

    Przejdź do folderu roboczego BlueTrack

    ./config/start_all.ps1

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
