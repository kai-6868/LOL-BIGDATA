# Build Custom Spark Image with Pre-installed Dependencies
# Run this script ONCE to create optimized Spark image

Write-Host "===========================================================" -ForegroundColor Cyan
Write-Host "  Building Custom Spark Image (One-time setup)" -ForegroundColor Cyan
Write-Host "===========================================================" -ForegroundColor Cyan

Write-Host ""
Write-Host "This will:" -ForegroundColor Yellow
Write-Host "   1. Build custom Spark image with Python packages"
Write-Host "   2. Pre-download Kafka connector JARs"
Write-Host "   3. Setup Ivy cache directory"
Write-Host ""
Write-Host "Estimated time: 5-10 minutes (one-time only)" -ForegroundColor Yellow
Write-Host "After this, Spark jobs will start instantly (<5s)" -ForegroundColor Green
Write-Host ""

$confirm = Read-Host "Continue? (Y/N)"
if ($confirm -ne "Y" -and $confirm -ne "y") {
    Write-Host "Build cancelled." -ForegroundColor Yellow
    exit
}

Write-Host ""
Write-Host "Building image..." -ForegroundColor Yellow

# Build custom Spark image
docker build -t spark-custom:3.5.0 -f docker/Dockerfile.spark-custom .

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "Image built successfully!" -ForegroundColor Green
    
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "   1. Update docker-compose.yml:"
    Write-Host "      Change image from apache/spark:3.5.0 to spark-custom:3.5.0"
    Write-Host "      (for both spark-master and spark-worker)"
    Write-Host ""
    Write-Host "   2. Restart Spark containers:"
    Write-Host "      docker-compose down"
    Write-Host "      docker-compose up -d spark-master spark-worker"
    Write-Host ""
    Write-Host "   3. Use optimized submit script:"
    Write-Host "      .\submit_spark_job_optimized.ps1"
    Write-Host ""
    Write-Host "===========================================================" -ForegroundColor Cyan
    Write-Host "Setup complete! Spark jobs will now start instantly." -ForegroundColor Green
    Write-Host "===========================================================" -ForegroundColor Cyan
} else {
    Write-Host ""
    Write-Host "Build failed!" -ForegroundColor Red
    Write-Host "Check error messages above" -ForegroundColor Yellow
}
