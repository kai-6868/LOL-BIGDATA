# Setup HDFS for Batch Layer
# Creates directories and sets permissions

Write-Host "===========================================================" -ForegroundColor Cyan
Write-Host "  Setting up HDFS for Batch Layer" -ForegroundColor Cyan
Write-Host "===========================================================" -ForegroundColor Cyan

Write-Host ""
Write-Host "[1/5] Checking HDFS NameNode..." -ForegroundColor Yellow
# Try to execute a simple command to check if namenode is accessible
$testResult = docker exec namenode echo "OK" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "  NameNode not running!" -ForegroundColor Red
    Write-Host "  Start containers: docker-compose up -d" -ForegroundColor Yellow
    exit 1
}
Write-Host "  NameNode is running" -ForegroundColor Green

Write-Host ""
Write-Host "[2/5] Creating base directory..." -ForegroundColor Yellow
docker exec namenode hadoop fs -mkdir -p /data/lol_matches 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "  Created /data/lol_matches" -ForegroundColor Green
} else {
    Write-Host "  Directory may already exist" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "[3/5] Setting permissions..." -ForegroundColor Yellow
docker exec namenode hadoop fs -chmod -R 777 /data/lol_matches
if ($LASTEXITCODE -eq 0) {
    Write-Host "  Permissions set to 777" -ForegroundColor Green
} else {
    Write-Host "  Warning: Could not set permissions" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[4/5] Creating today partition..." -ForegroundColor Yellow
$today = Get-Date -Format "yyyy/MM/dd"
docker exec namenode hadoop fs -mkdir -p "/data/lol_matches/$today" 2>$null
docker exec namenode hadoop fs -chmod 777 "/data/lol_matches/$today" 2>$null
Write-Host "  Created partition: $today" -ForegroundColor Green

Write-Host ""
Write-Host "[5/5] Verifying setup..." -ForegroundColor Yellow
docker exec namenode hadoop fs -ls -R /data/lol_matches

Write-Host ""
Write-Host "===========================================================" -ForegroundColor Cyan
Write-Host "  HDFS Setup Complete!" -ForegroundColor Green
Write-Host "===========================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "HDFS Structure:" -ForegroundColor Yellow
Write-Host "  /data/lol_matches/" -ForegroundColor Cyan
Write-Host "    - $today/" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next step:" -ForegroundColor Yellow
Write-Host "  Run: .\setup_cassandra.ps1" -ForegroundColor Cyan
Write-Host ""
