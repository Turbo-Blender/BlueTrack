# filepath: e:\Other\inf\BlueTrack\dockerfile
FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    wget \
    curl \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Now copy only the source code
COPY . /app/

EXPOSE 8000 5000

CMD ["bash", "-c", "\
if [ -f server/server.py ]; then python server/server.py & fi && \
if [ -f analysis/spark_processor.py ]; then python analysis/spark_processor.py & fi && \
sleep 10 && \
echo 'All Python components started' && \
tail -f /dev/null \
"]