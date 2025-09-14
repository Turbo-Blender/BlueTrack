FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    default-jre \
    wget \
    curl \
    procps \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*
ENV JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
ENV PATH="$JAVA_HOME/bin:$PATH"

# Copy requirements first for better caching
COPY requirements.txt ./
RUN python3 -m pip install --no-cache-dir -r requirements.txt

# Now copy only the source code
COPY . .

EXPOSE 8000 5000

COPY wait-for-it.sh /wait-for-it.sh
RUN chmod +x /wait-for-it.sh

CMD bash -c "\
/wait-for-it.sh kafka:29092 --timeout=60 --strict -- \
&& /wait-for-it.sh mongodb:27017 --timeout=60 --strict -- \
&& /wait-for-it.sh spark:7077 --timeout=60 --strict -- \
&& if [ -f server/server.py ]; then python server/server.py & fi \
&& if [ -f analysis/spark_processor.py ]; then python analysis/spark_processor.py & fi \
&& sleep 10 \
&& echo 'All Python components started' \
&& tail -f /dev/null"