# Setup Cassandra Schema for Batch Layer
# Executes init_cassandra.cql script

Write-Host "===========================================================" -ForegroundColor Cyan
Write-Host "  Setting up Cassandra Schema" -ForegroundColor Cyan
Write-Host "===========================================================" -ForegroundColor Cyan

Write-Host ""
Write-Host "[1/4] Checking Cassandra..." -ForegroundColor Yellow
$testResult = docker exec cassandra echo "OK" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "  Cassandra not running!" -ForegroundColor Red
    Write-Host "  Start containers: docker-compose up -d" -ForegroundColor Yellow
    exit 1
}
Write-Host "  Cassandra is running" -ForegroundColor Green

Write-Host ""
Write-Host "[2/4] Waiting for Cassandra to be ready..." -ForegroundColor Yellow
$maxWait = 30
$waited = 0
while ($waited -lt $maxWait) {
    $status = docker exec cassandra nodetool status 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  Cassandra is ready" -ForegroundColor Green
        break
    }
    Start-Sleep -Seconds 2
    $waited += 2
    Write-Host "  Waiting... ($waited/$maxWait seconds)" -ForegroundColor Cyan
}

if ($waited -ge $maxWait) {
    Write-Host "  Warning: Cassandra may not be fully ready" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[3/4] Copying init script..." -ForegroundColor Yellow
docker cp init_cassandra.cql cassandra:/tmp/
if ($LASTEXITCODE -eq 0) {
    Write-Host "  Script copied" -ForegroundColor Green
} else {
    Write-Host "  Failed to copy script" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[4/4] Executing CQL script..." -ForegroundColor Yellow
docker exec cassandra cqlsh -f /tmp/init_cassandra.cql
if ($LASTEXITCODE -eq 0) {
    Write-Host "  Schema created successfully" -ForegroundColor Green
} else {
    Write-Host "  Schema may already exist or there was an error" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "===========================================================" -ForegroundColor Cyan
Write-Host "  Verifying Schema..." -ForegroundColor Cyan
Write-Host "===========================================================" -ForegroundColor Cyan

Write-Host ""
Write-Host "Keyspaces:" -ForegroundColor Yellow
docker exec cassandra cqlsh -e "DESCRIBE KEYSPACES;"

Write-Host ""
Write-Host "Tables in lol_data:" -ForegroundColor Yellow
docker exec cassandra cqlsh -e "USE lol_data; DESCRIBE TABLES;"

Write-Host ""
Write-Host "===========================================================" -ForegroundColor Cyan
Write-Host "  Cassandra Setup Complete!" -ForegroundColor Green
Write-Host "===========================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next step:" -ForegroundColor Yellow
Write-Host "  python batch-layer/src/batch_consumer.py --batches 1" -ForegroundColor Cyan
Write-Host ""
