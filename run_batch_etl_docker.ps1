# Run PySpark ETL inside Spark Docker Container
# This avoids all Windows winutils issues!

param(
    [string]$Date = ""
)

Write-Host "===========================================================" -ForegroundColor Cyan
Write-Host "  Running PySpark ETL in Docker (HDFS -> Cassandra)" -ForegroundColor Cyan
Write-Host "===========================================================" -ForegroundColor Cyan

# Use today's date if not specified
if ($Date -eq "") {
    $Date = Get-Date -Format "yyyy/MM/dd"
}

Write-Host ""
Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "  Date: $Date"
Write-Host "  Running in: Spark Docker Container"
Write-Host ""

# Check if pyspark-worker is running
Write-Host "Checking PySpark container..." -ForegroundColor Yellow
$sparkCheck = docker ps --filter "name=pyspark-worker" --format "{{.Names}}" 2>$null

if ($LASTEXITCODE -ne 0 -or $sparkCheck -ne "pyspark-worker") {
    Write-Host "  PySpark container not running!" -ForegroundColor Red
    Write-Host "  Starting container..." -ForegroundColor Yellow
    docker-compose up -d pyspark-worker
    Start-Sleep -Seconds 5
}
Write-Host "  PySpark container is running" -ForegroundColor Green

Write-Host ""
Write-Host "Starting PySpark ETL in Docker..." -ForegroundColor Yellow
Write-Host ""

# Run Python script inside PySpark container
docker exec pyspark-worker python /opt/batch-layer/src/pyspark_etl.py --date $Date

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "===========================================================" -ForegroundColor Cyan
    Write-Host "  PySpark ETL Completed!" -ForegroundColor Green
    Write-Host "===========================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Verify data in Cassandra:" -ForegroundColor Yellow
    Write-Host "  docker exec -it cassandra cqlsh" -ForegroundColor Cyan
    Write-Host "  USE lol_data;" -ForegroundColor Cyan
    Write-Host '  SELECT COUNT(*) FROM match_stats;' -ForegroundColor Cyan
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "===========================================================" -ForegroundColor Red
    Write-Host "  PySpark ETL Failed!" -ForegroundColor Red
    Write-Host "===========================================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Check Spark logs:" -ForegroundColor Yellow
    Write-Host "  docker logs spark-master" -ForegroundColor Cyan
    Write-Host ""
}
