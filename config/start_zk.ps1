# start_zk.ps1

# 1) Ustal katalog ZooKeepera na podstawie lokalizacji skryptu
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$env:ZOOKEEPER_HOME = $scriptDir

# 2) Upewnij się, że wskazujesz poprawne JAVA_HOME
#    (albo usuń tę linię, jeśli masz już JAVA_HOME w env)
$env:JAVA_HOME = "C:\Program Files\Eclipse Adoptium\jdk-11.0.28.6-hotspot"

Write-Host "ZOOKEEPER_HOME -> $env:ZOOKEEPER_HOME"
Write-Host "JAVA_HOME      -> $env:JAVA_HOME"

# 3) Zbuduj classpath ręcznie
#    - build/classes      : skompilowane klasy
#    - build/lib/*        : biblioteki do quorum
#    - lib/*              : wszystkie pozostałe JAR-y ZK
#    - conf               : katalog z zoo.cfg
$classpath = @(
  "$env:ZOOKEEPER_HOME\build\classes"
  "$env:ZOOKEEPER_HOME\build\lib\*"
  "$env:ZOOKEEPER_HOME\lib\*"
  "$env:ZOOKEEPER_HOME\conf"
) -join ";"

# 4) Wywołanie JVM
$javaExe = Join-Path $env:JAVA_HOME 'bin\java.exe'
Write-Host "`n-- Uruchamiam ZooKeeper (bez wrapperów) --"
Write-Host "  $javaExe -cp $classpath org.apache.zookeeper.server.quorum.QuorumPeerMain $env:ZOOKEEPER_HOME\conf\zoo.cfg`n"

# Uwaga: ten proces zostanie uruchomiony w bieżącym oknie i w foreground
& $javaExe `
  -cp $classpath `
  org.apache.zookeeper.server.quorum.QuorumPeerMain `
  "$env:ZOOKEEPER_HOME\conf\zoo.cfg"
