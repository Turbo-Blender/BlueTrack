
# --------------------------------------------------
# 1) Paths – adjust to your environment:
# --------------------------------------------------
$zkHome     = "C:\zookeeper\zookeeper-3.8.4"
$kafkaHome  = "C:\kafka\kafka-3.4.0"
$kafkaLogs  = "C:\kafka\kafka-3.4.0\kafka-logs"

# --------------------------------------------------
# 2) Delete old Kafka logs
# --------------------------------------------------
if (Test-Path $kafkaLogs) {
    Write-Host "Deleting old Kafka logs folder: $kafkaLogs"
    Remove-Item -Recurse -Force $kafkaLogs
} else {
    Write-Host "Kafka logs folder does not exist: $kafkaLogs"
}

# --------------------------------------------------
# 3) Start ZooKeeper in a new PS window
# --------------------------------------------------
Write-Host "`n=== Starting ZooKeeper ===`n"
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location '$zkHome'; .\start_zk.ps1"
) -WorkingDirectory $zkHome

# --------------------------------------------------
# 4) Wait for ZooKeeper (port 2181) to be ready
# --------------------------------------------------
Write-Host "`nWaiting for ZooKeeper to be ready (localhost:2181)…"
while (-not (Test-NetConnection -ComputerName "localhost" -Port 2181 -WarningAction SilentlyContinue).TcpTestSucceeded) {
    Write-Host -NoNewline "."
    Start-Sleep -Seconds 1
}
Write-Host "`nZooKeeper is ready!`n"

# --------------------------------------------------
# 5) Start Kafka Broker in a new PS window
# --------------------------------------------------
Write-Host "=== Starting Kafka Broker ==="
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location '$kafkaHome'; & .\bin\windows\kafka-server-start.bat .\config\server.properties"
) -WorkingDirectory $kafkaHome
