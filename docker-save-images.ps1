# Docker Images Backup Script
Write-Host ""
Write-Host "========================================"
Write-Host "  DOCKER IMAGES BACKUP" -ForegroundColor Yellow
Write-Host "========================================"
Write-Host ""

$images = "bigbig-kafka:snapshot", "bigbig-zookeeper:snapshot", "bigbig-spark-master:snapshot", "bigbig-spark-worker:snapshot", "bigbig-hadoop-namenode:snapshot", "bigbig-hadoop-datanode:snapshot", "bigbig-cassandra:snapshot", "bigbig-elasticsearch:snapshot", "bigbig-kibana:snapshot", "bigbig-prometheus:snapshot", "bigbig-grafana:snapshot"
$outputFile = "bigbig-stack-snapshot.tar"

Write-Host "[1/3] Checking images..." -ForegroundColor Green
foreach ($img in $images) {
    $info = docker images $img --format "{{.Size}}"
    if ($info) {
        Write-Host "  Found: $img ($info)" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "WARNING: File size will be ~10-12 GB" -ForegroundColor Yellow
Write-Host "This may take 10-30 minutes" -ForegroundColor Yellow
Write-Host ""

$confirm = Read-Host "Continue? (yes/no)"
if ($confirm -ne "yes") {
    Write-Host "Cancelled" -ForegroundColor Red
    exit 0
}

Write-Host ""
Write-Host "[2/3] Saving images..." -ForegroundColor Green
Write-Host "Please wait (10-30 minutes)..." -ForegroundColor Gray
Write-Host ""

$startTime = Get-Date
docker save -o $outputFile $images

if ($LASTEXITCODE -eq 0) {
    $duration = (Get-Date) - $startTime
    Write-Host ""
    Write-Host "[3/3] Complete!" -ForegroundColor Green
    if (Test-Path $outputFile) {
        $size = (Get-Item $outputFile).Length / 1GB
        Write-Host "  File: $outputFile" -ForegroundColor Cyan
        Write-Host "  Size: $([math]::Round($size, 2)) GB" -ForegroundColor Cyan
        Write-Host "  Time: $([math]::Round($duration.TotalSeconds, 0)) seconds" -ForegroundColor Cyan
    }
    Write-Host ""
    Write-Host "SUCCESS! See DOCKER_RESTORE_GUIDE.md for restore instructions" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "ERROR: Docker save failed" -ForegroundColor Red
    Write-Host ""
}
