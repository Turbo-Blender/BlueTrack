Start-Process powershell -ArgumentList '-NoExit', '-Command', ".\bin\windows\zookeeper-server-start.bat .\config\zookeeper.properties"

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

Write-Host "ZooKeeper wstał, startuję Kafkę"
Start-Process powershell -ArgumentList '-NoExit', '-Command', ".\bin\windows\kafka-server-start.bat .\config\server.properties"
