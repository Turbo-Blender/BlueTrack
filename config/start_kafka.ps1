# start_kafka.ps1
Write-Host "==== Startuję ZooKeeper ===="
Start-Process powershell -ArgumentList '-NoExit', '-Command', ".\bin\windows\zookeeper-server-start.bat .\config\zookeeper.properties"

# Czekamy aż ZooKeeper się podniesie
$zkUp = $false
while (-not $zkUp) {
    try {
        $socket = New-Object Net.Sockets.TcpClient
        $socket.Connect("localhost", 2181)
        $zkUp = $true
        $socket.Close()
    } catch {
        Write-Host "Czekam na ZooKeepera..."
        Start-Sleep -Seconds 2
    }
}

Write-Host "`n==== ZooKeeper wstał ===="

# Usuwamy stare dane w ZooKeeper
Write-Host "Czyszczę dane w ZooKeeper..."
@"
deleteall /brokers
deleteall /admin
deleteall /config
delete /cluster/id
quit
"@ | Out-File -Encoding ASCII clear_zk.txt

Get-Content clear_zk.txt | .\bin\windows\zkCli.bat -server localhost:2181 | Out-Null
Remove-Item clear_zk.txt

Write-Host "`n==== ZooKeeper wyczyszczony ===="

# Usuwamy stare logi Kafki
$kafkaLogDir = ".\kafka-logs"
if (Test-Path $kafkaLogDir) {
    Write-Host "Usuwam stare logi Kafki w $kafkaLogDir"
    Remove-Item -Recurse -Force $kafkaLogDir
} else {
    Write-Host "Nie ma katalogu logów Kafki ($kafkaLogDir), nic do usunięcia."
}

# Startujemy Kafkę
Write-Host "`n==== Startuję Kafkę ===="
Start-Process powershell -ArgumentList '-NoExit', '-Command', ".\bin\windows\kafka-server-start.bat .\config\server.properties"
