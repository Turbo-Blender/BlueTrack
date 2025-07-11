$env:JAVA_HOME = "C:\Program Files\Eclipse Adoptium\jdk-11.0.27.6-hotspot"
$env:PATH = "$env:JAVA_HOME\bin;" + $env:PATH
Write-Host "JAVA_HOME set to: $env:JAVA_HOME"

$env:HADOOP_HOME = "C:\hadoop"
$env:PATH = "$env:PATH;$env:HADOOP_HOME\bin"


$env:SPARK_HOME = "C:\spark\spark-3.4.4-bin-hadoop3"
$env:PATH = "$env:SPARK_HOME\bin;" + $env:PATH
$env:PYTHONPATH="$env:SPARK_HOME\python;$env:SPARK_HOME\python\lib\py4j-0.10.9.7-src.zip"
$env:PYSPARK_PYTHON = ".\venv\Scripts\python.exe"
$env:PYSPARK_DRIVER_PYTHON = ".\venv\Scripts\python.exe"

Write-Host "SPARK_HOME set to: $env:SPARK_HOME"

Write-Host "`nTesting Java version..."
java -version

Write-Host "`nTesting Spark version..."
spark-submit --version