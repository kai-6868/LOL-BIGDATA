# Run Real Match Producer
# Automatically reads API keys from api_keys.txt

Write-Host "===========================================================" -ForegroundColor Cyan
Write-Host "  Real Match Data Producer" -ForegroundColor Cyan
Write-Host "===========================================================" -ForegroundColor Cyan
Write-Host ""

# Check if api_keys.txt exists
if (-not (Test-Path "api_keys.txt")) {
    Write-Host "❌ Error: api_keys.txt not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please create api_keys.txt with your Riot API keys:" -ForegroundColor Yellow
    Write-Host "  1. Copy api_keys.txt.example to api_keys.txt" -ForegroundColor Cyan
    Write-Host "  2. Edit api_keys.txt and add your keys" -ForegroundColor Cyan
    Write-Host "  3. Get keys from: https://developer.riotgames.com/" -ForegroundColor Cyan
    Write-Host ""
    exit 1
}

# Check virtual environment
if (-not $env:VIRTUAL_ENV) {
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    & .\.venv\Scripts\Activate.ps1
}

# Check Kafka
Write-Host "Checking Kafka..." -ForegroundColor Yellow
$kafkaCheck = docker ps --filter "name=kafka" --format "{{.Names}}" 2>$null
if ($LASTEXITCODE -ne 0 -or $kafkaCheck -ne "kafka") {
    Write-Host "  Kafka not running. Starting..." -ForegroundColor Yellow
    docker-compose up -d kafka zookeeper
    Write-Host "  Waiting for Kafka to be ready..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
}
Write-Host "  ✅ Kafka is running" -ForegroundColor Green
Write-Host ""

# Run producer
Write-Host "Starting Real Match Producer..." -ForegroundColor Cyan
Write-Host ""
python real_match_producer.py api_keys.txt

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "===========================================================" -ForegroundColor Cyan
    Write-Host "  Producer Stopped" -ForegroundColor Yellow
    Write-Host "===========================================================" -ForegroundColor Cyan
} else {
    Write-Host ""
    Write-Host "===========================================================" -ForegroundColor Red
    Write-Host "  Producer Failed!" -ForegroundColor Red
    Write-Host "===========================================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Troubleshooting:" -ForegroundColor Yellow
    Write-Host "  1. Check API keys in api_keys.txt are valid" -ForegroundColor Cyan
    Write-Host "  2. Verify Kafka is running: docker ps" -ForegroundColor Cyan
    Write-Host "  3. Check logs above for errors" -ForegroundColor Cyan
}
