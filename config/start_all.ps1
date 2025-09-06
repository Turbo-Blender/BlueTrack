# --------------------------------------------------
# Konfiguracja ścieżek – dostosuj do swojego systemu
# --------------------------------------------------
$zkHome = "C:\zookeeper\zookeeper-3.8.4"
$zkDataDir = "C:\zookeeper\data"                  # dataDir w zoo.cfg
$kafkaHome = "C:\kafka\kafka-3.4.0"
$kafkaLogs = "$kafkaHome\kafka-logs"        # log.dirs w server.properties

# --------------------------------------------------
# 1) Usuń stare dane ZooKeepera
# --------------------------------------------------
if (Test-Path $zkDataDir) {
    Write-Host "Deleting old ZooKeeper data folder: $zkDataDir"
    Remove-Item -Recurse -Force $zkDataDir
} else {
    Write-Host "ZooKeeper data folder does not exist: $zkDataDir"
}

# --------------------------------------------------
# 2) Usuń stare logi Kafki / utwórz folder jeśli brak
# --------------------------------------------------
if (-not (Test-Path $kafkaLogs)) {
    Write-Host "Kafka logs folder does not exist. Creating: $kafkaLogs"
    New-Item -ItemType Directory -Path $kafkaLogs
} else {
    Write-Host "Deleting old Kafka logs: $kafkaLogs"
    Remove-Item -Recurse -Force $kafkaLogs
}

# --------------------------------------------------
# 3) Start ZooKeeper w nowym oknie PowerShell
# --------------------------------------------------
Write-Host "`n=== Starting ZooKeeper ===`n"
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location '$zkHome'; .\start_zk.ps1"
) -WorkingDirectory $zkHome

# --------------------------------------------------
# 4) Czekaj aż ZooKeeper wystartuje (port 2181)
# --------------------------------------------------
Write-Host "`nWaiting for ZooKeeper (localhost:2181)…"
while (-not (Test-NetConnection -ComputerName "localhost" -Port 2181 -WarningAction SilentlyContinue).TcpTestSucceeded) {
    Write-Host -NoNewline "."
    Start-Sleep -Seconds 1
}
Write-Host "`nZooKeeper is ready!"

# --------------------------------------------------
# 5) Start Kafka Broker w nowym oknie PowerShell
# --------------------------------------------------
Write-Host "`n=== Starting Kafka Broker ===`n"
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location '$kafkaHome'; .\bin\windows\kafka-server-start.bat .\config\server.properties"
) -WorkingDirectory $kafkaHome

Write-Host "`nAll services started!"
