# Optimized Spark Job Submission Script
# No package installation or JAR downloads needed
# Requires: spark-custom:3.5.0 image

Write-Host "===========================================================" -ForegroundColor Cyan
Write-Host "  Submitting Spark Streaming Job (OPTIMIZED - Instant)" -ForegroundColor Cyan
Write-Host "===========================================================" -ForegroundColor Cyan

Write-Host ""
Write-Host "Job Configuration:" -ForegroundColor Yellow
Write-Host "   Master: spark://spark-master:7077"
Write-Host "   Driver Memory: 2g"
Write-Host "   Executor Memory: 2g"
Write-Host "   Executor Cores: 2"
Write-Host "   Mode: Structured Streaming"

Write-Host ""
Write-Host "Submitting job..." -ForegroundColor Yellow

# Submit job (instant - no downloads)
docker exec spark-master /opt/spark/bin/spark-submit `
  --master spark://spark-master:7077 `
  --deploy-mode client `
  --driver-memory 2g `
  --executor-memory 2g `
  --executor-cores 2 `
  --conf spark.streaming.backpressure.enabled=true `
  --conf spark.streaming.kafka.maxRatePerPartition=100 `
  --conf spark.pyspark.python=python3 `
  --py-files /opt/spark/work-dir/streaming-layer/src/elasticsearch_indexer.py `
  /opt/spark/work-dir/streaming-layer/src/spark_streaming_consumer.py `
  --config /opt/spark/work-dir/streaming-layer/config/spark_config_docker.yaml

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "===========================================================" -ForegroundColor Cyan
    Write-Host "Job submitted successfully! (Instant startup)" -ForegroundColor Green
    Write-Host "===========================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Monitoring URLs:" -ForegroundColor Yellow
    Write-Host "   Spark Master UI:  http://localhost:8080"
    Write-Host "   Spark App UI:     http://localhost:4040"
    Write-Host "   Elasticsearch:    http://localhost:9200"
    Write-Host "   Kibana:           http://localhost:5601"
    Write-Host ""
    Write-Host "Tip: Check Spark UI to see job status" -ForegroundColor Cyan
    Write-Host "===========================================================" -ForegroundColor Cyan
} else {
    Write-Host ""
    Write-Host "Job submission failed!" -ForegroundColor Red
    Write-Host "Check logs: docker logs spark-master" -ForegroundColor Yellow
}
