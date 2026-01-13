#!/bin/bash
# Submit Spark Streaming job to Docker cluster

echo "=================================================="
echo "Submitting Spark Streaming Job to Docker Cluster"
echo "=================================================="

# Install Python dependencies in Spark container first
echo "Installing Python dependencies..."
docker exec spark-master pip install pyyaml elasticsearch kafka-python

# Submit Spark job
echo "Submitting job..."
docker exec spark-master /opt/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --deploy-mode client \
  --driver-memory 2g \
  --executor-memory 2g \
  --executor-cores 2 \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 \
  --conf spark.driver.extraJavaOptions="-Divy.cache.dir=/tmp -Divy.home=/tmp" \
  --conf spark.executor.extraJavaOptions="-Divy.cache.dir=/tmp -Divy.home=/tmp" \
  --conf spark.streaming.backpressure.enabled=true \
  --conf spark.streaming.kafka.maxRatePerPartition=100 \
  /opt/spark/work-dir/streaming-layer/src/spark_streaming_consumer.py

echo "=================================================="
echo "Job submitted!"
echo "Check Spark UI: http://localhost:8080"
echo "Check Spark App UI: http://localhost:4040"
echo "=================================================="
