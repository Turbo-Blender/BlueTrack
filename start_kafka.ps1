Start-Process powershell -ArgumentList '-NoExit', '-Command', ".\bin\windows\zookeeper-server-start.bat .\config\zookeeper.properties"
Start-Sleep -Seconds 5
Start-Process powershell -ArgumentList '-NoExit', '-Command', ".\bin\windows\kafka-server-start.bat .\config\server.properties"
