# Submit Spark Streaming job to Docker cluster (PowerShell version)

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "Submitting Spark Streaming Job to Docker Cluster" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# Install Python dependencies in Spark container first (as root)
Write-Host "`nInstalling Python dependencies..." -ForegroundColor Yellow
docker exec -u root spark-master pip install pyyaml elasticsearch kafka-python

# Submit Spark job
Write-Host "`nSubmitting job..." -ForegroundColor Yellow
docker exec spark-master /opt/spark/bin/spark-submit `
  --master spark://spark-master:7077 `
  --deploy-mode client `
  --driver-memory 2g `
  --executor-memory 2g `
  --executor-cores 2 `
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 `
  --conf spark.driver.extraJavaOptions="-Divy.cache.dir=/tmp -Divy.home=/tmp" `
  --conf spark.executor.extraJavaOptions="-Divy.cache.dir=/tmp -Divy.home=/tmp" `
  --conf spark.streaming.backpressure.enabled=true `
  --conf spark.streaming.kafka.maxRatePerPartition=100 `
  --conf spark.pyspark.python=python3 `
  --py-files /opt/spark/work-dir/streaming-layer/src/elasticsearch_indexer.py `
  /opt/spark/work-dir/streaming-layer/src/spark_streaming_consumer.py `
  --config /opt/spark/work-dir/streaming-layer/config/spark_config_docker.yaml

Write-Host "`n==================================================" -ForegroundColor Cyan
Write-Host "Job submitted!" -ForegroundColor Green
Write-Host "Check Spark UI: http://localhost:8080" -ForegroundColor Yellow
Write-Host "Check Spark App UI: http://localhost:4040" -ForegroundColor Yellow
Write-Host "==================================================" -ForegroundColor Cyan
