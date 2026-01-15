# Run Batch Consumer
# Consumes data from Kafka and writes to HDFS in Parquet format

param(
    [int]$Batches = 1,
    [int]$BatchSize = 50
)

Write-Host "===========================================================" -ForegroundColor Cyan
Write-Host "  Running Batch Consumer (Kafka -> HDFS)" -ForegroundColor Cyan
Write-Host "===========================================================" -ForegroundColor Cyan

Write-Host ""
Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "  Batches: $Batches"
Write-Host "  Batch Size: $BatchSize messages"
Write-Host "  Output: HDFS Parquet files"
Write-Host ""

# Check virtual environment
if (-not $env:VIRTUAL_ENV) {
    Write-Host "Virtual environment not activated!" -ForegroundColor Yellow
    Write-Host "Activating..." -ForegroundColor Cyan
    & .\.venv\Scripts\Activate.ps1
}

# Check Kafka has data
Write-Host "Checking Kafka for data..." -ForegroundColor Yellow
$kafkaCheck = docker exec kafka kafka-run-class kafka.tools.GetOffsetShell --broker-list localhost:9092 --topic lol_matches --time -1 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "  Cannot connect to Kafka" -ForegroundColor Yellow
} else {
    Write-Host "  Kafka is accessible" -ForegroundColor Green
}

Write-Host ""
Write-Host "Starting batch consumer..." -ForegroundColor Yellow
Write-Host ""

# Run batch consumer with custom batch size
python batch-layer/src/batch_consumer.py --batches $Batches --batch-size $BatchSize

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "===========================================================" -ForegroundColor Cyan
    Write-Host "  Batch Consumer Completed!" -ForegroundColor Green
    Write-Host "===========================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Verify data in HDFS:" -ForegroundColor Yellow
    Write-Host "  docker exec namenode hadoop fs -ls -R /data/lol_matches" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Next step:" -ForegroundColor Yellow
    Write-Host '  .\run_batch_etl.ps1' -ForegroundColor Cyan
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "===========================================================" -ForegroundColor Red
    Write-Host "  Batch Consumer Failed!" -ForegroundColor Red
    Write-Host "===========================================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Troubleshooting:" -ForegroundColor Yellow
    Write-Host "  1. Check Kafka has data:" -ForegroundColor Cyan
    Write-Host "     docker exec kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic lol_matches --max-messages 1"
    Write-Host "  2. Check HDFS permissions:" -ForegroundColor Cyan
    Write-Host "     docker exec namenode hadoop fs -ls /data/lol_matches"
    Write-Host "  3. Check logs in: batch-layer/logs/" -ForegroundColor Cyan
    Write-Host ""
}
