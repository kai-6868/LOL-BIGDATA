# Spark Streaming Troubleshooting Guide

## ✅ PHASE 3 PRODUCTION DEPLOYMENT - COMPLETED

**Status**: Phase 3 Streaming Layer successfully deployed and verified on Docker cluster.

**Verification Results**:

```
✓ Spark Application UI: http://localhost:4040 ✅
✓ Spark Master UI: http://localhost:8080 ✅
✓ Elasticsearch documents: 3,855+ indexed ✅
✓ Pipeline: Generator → Kafka → Spark → Elasticsearch ✅
✓ No errors, all batches successful ✅
```

---

## 🚨 Common Issues Encountered & Solutions

### Issue 1: Kafka Container Keeps Restarting

**Symptom**:

```powershell
docker compose ps
# Kafka container missing from output or status "Restarting"
```

**Root Cause**: InconsistentClusterIdException - Cluster ID mismatch between Kafka metadata and Zookeeper

**Error in Logs**:

```
InconsistentClusterIdException: The Cluster ID Or8zQec0Sgyru-dkddFCvQ
doesn't match stored clusterId Some(6r9_qcVoTuCw7V6yvDjAqA)
```

**Solution**:

```powershell
# 1. Remove corrupted Kafka volumes
docker compose down -v kafka
docker volume rm bigbig_kafka_data

# 2. Recreate Kafka with fresh metadata
docker compose up -d kafka

# 3. Wait for Kafka to start (check logs)
docker logs kafka --tail 50
# Look for: "Kafka Server started"

# 4. Recreate topic
docker exec kafka kafka-topics --bootstrap-server localhost:9092 \
  --create --topic lol_matches --partitions 3 --replication-factor 1

# 5. Verify topic configuration
docker exec kafka kafka-topics --bootstrap-server localhost:9092 \
  --describe --topic lol_matches
```

**Expected Output**:

```
Topic: lol_matches  PartitionCount: 3  ReplicationFactor: 1
Partition: 0  Leader: 1  Replicas: 1  Isr: 1
Partition: 1  Leader: 1  Replicas: 1  Isr: 1
Partition: 2  Leader: 1  Replicas: 1  Isr: 1
```

---

### Issue 2: Spark Job Crashes with Offset Error

**Symptom**:

```
Query [id = 67f76f93...] terminated with error
IllegalStateException: Partition lol_matches-2's offset was changed
from 383 to 28, some data may have been missed. failOnDataLoss triggered
```

**Root Cause**: Checkpoint directory contains old offsets that don't match current Kafka topic state (after topic recreation)

**Why This Happens**:

- When Kafka volumes are removed, topics are recreated from scratch
- New topic starts with offset 0
- Old checkpoints still reference previous offsets (e.g., 383)
- Spark detects offset mismatch and crashes to prevent data loss

**Solution**:

```powershell
# 1. Clear old checkpoint directory
Remove-Item -Recurse -Force .\checkpoints\streaming\* -ErrorAction SilentlyContinue

# 2. Verify checkpoints cleared
Get-ChildItem .\checkpoints\streaming\
# Should be empty (or only .gitkeep file)

# 3. Restart data generator (in new window)
Start-Process powershell -ArgumentList "-NoExit", "-Command", `
  "cd 'E:\FILEMANAGEMENT_PC\_WORKSPACE\PROGRESS\bigbig'; `
  .\.venv\Scripts\Activate.ps1; `
  python data-generator/src/generator.py --mode continuous"

# 4. Wait for generator to start
Start-Sleep -Seconds 3

# 5. Resubmit Spark job with clean checkpoints
.\submit_spark_job.ps1

# 6. Monitor logs for successful start
docker logs spark-master --tail 50
```

**Expected Logs (Success)**:

```
2026-01-13 02:56:20 - INFO - ✓ Initialized Spark Structured Streaming
2026-01-13 02:56:20 - INFO - ✓ Connected to Elasticsearch
2026-01-13 02:56:23 - INFO - ✓ Starting Spark Structured Streaming Consumer
2026-01-13 02:56:35 - INFO - Batch 1: 40 participants, 40 indexed, 0 failed
2026-01-13 02:56:36 - INFO - ✓ Bulk indexed: 110 docs, 0 failed
```

**No Errors Like**:

```
✗ IllegalStateException
✗ offset was changed
✗ failOnDataLoss triggered
```

---

### Issue 3: Spark UI Not Accessible (Port 4040/4041)

**Symptom**:

```powershell
curl http://localhost:4040
# Error: Unable to connect to the remote server
```

**Root Cause**: No active Spark application running (Spark UI only starts when job is active)

**Diagnosis Steps**:

```powershell
# Check if Spark job process exists
docker exec spark-master ps aux | Select-String "spark_streaming_consumer"
# Empty output = no job running

# Check Spark Master UI for running applications
Start-Process "http://localhost:8080"
# Look for "Running Applications" section
# If empty → no active job
```

**Solution**:

```powershell
# Complete restart procedure:

# 1. Start data generator (provides data stream)
Start-Process powershell -ArgumentList "-NoExit", "-Command", `
  "cd 'E:\FILEMANAGEMENT_PC\_WORKSPACE\PROGRESS\bigbig'; `
  .\.venv\Scripts\Activate.ps1; `
  python data-generator/src/generator.py --mode continuous"

# 2. Wait for generator to start producing
Start-Sleep -Seconds 3

# 3. Submit Spark job
.\submit_spark_job.ps1

# 4. Wait for Spark UI initialization (15-20 seconds)
Start-Sleep -Seconds 15

# 5. Test UI accessibility
curl http://localhost:4040 -UseBasicParsing | Select-Object -First 3
# Expected: StatusCode 200, Content contains "Spark"

# 6. Open in browser
Start-Process "http://localhost:4040"
```

**Port Mapping (from docker-compose.yml)**:

```yaml
spark-master:
  ports:
    - "8080:8080" # Spark Master UI
    - "7077:7077" # Spark Master service
    - "4040:4040" # Spark Application UI
```

**Why Port 4040 Specifically**:

- Spark Application UI auto-assigns port 4040 by default
- If 4040 is occupied, tries 4041, 4042, etc.
- Port only becomes accessible when application is actively running
- UI shuts down when job terminates

---

### Issue 4: Elasticsearch Connection Failed

**Symptom**:

```
ConnectionError: Connection refused to http://elasticsearch:9200
ERROR: Unable to connect to Elasticsearch
```

**Solution**:

```powershell
# Check Elasticsearch container
docker compose ps elasticsearch
# Should show status "Up"

# If not running, restart
docker compose restart elasticsearch
Start-Sleep -Seconds 30

# Test connection from host
curl http://localhost:9200
# Expected: JSON with cluster info

# Test connection from Spark container
docker exec spark-master curl http://elasticsearch:9200
# Should also return cluster info

# If still failing, check logs
docker logs elasticsearch --tail 50
```

---

### Issue 5: No Documents in Elasticsearch

**Symptom**: Document count stays at 0 despite job running

**Diagnosis**:

```powershell
# Check document count
curl "http://localhost:9200/lol_matches_stream/_count?pretty"

# Check Spark logs for indexing status
docker logs spark-master --tail 100 | Select-String "indexed"

# Check for failed docs
docker logs spark-master --tail 100 | Select-String "failed"
```

**Solution**:

```powershell
# Verify full pipeline:

# 1. Check data generator producing
# Look for generator window with "Sent: ..." messages

# 2. Check Kafka receiving messages
docker exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic lol_matches \
  --from-beginning \
  --max-messages 1
# Should print JSON match data

# 3. Check Spark consuming from Kafka
docker logs spark-master --tail 50 | Select-String "Batch"
# Should show: "Batch X: Y participants, Y indexed, 0 failed"

# 4. If all above work but no ES docs, check ES index mapping
curl "http://localhost:9200/lol_matches_stream/_mapping?pretty"

# 5. Try manual document insert to verify ES works
curl -X POST "http://localhost:9200/lol_matches_stream/_doc" `
  -H "Content-Type: application/json" `
  -d '{"test":"data","timestamp":1736753780000}'
```

---

## 🎯 Prevention & Best Practices

### Before Starting Work

```powershell
# Always verify infrastructure health:
docker compose ps | Select-String "Up"
# All 11 services should be "Up"

# Check Kafka topic exists:
docker exec kafka kafka-topics --list --bootstrap-server localhost:9092
# Should include: lol_matches

# Check Elasticsearch health:
curl "http://localhost:9200/_cluster/health?pretty"
# Status should be "green" or "yellow"
```

### When Restarting Services

```powershell
# If restarting Kafka, always:
# 1. Stop dependent services first
docker compose stop spark-master spark-worker

# 2. Restart Kafka
docker compose restart kafka
Start-Sleep -Seconds 60

# 3. Clear Spark checkpoints (if topic recreated)
Remove-Item -Recurse -Force .\checkpoints\streaming\*

# 4. Restart Spark services
docker compose start spark-master spark-worker

# 5. Resubmit job
.\submit_spark_job.ps1
```

### Monitoring During Development

```powershell
# Terminal 1: Data generator
python data-generator/src/generator.py --mode continuous

# Terminal 2: Spark job submission
.\submit_spark_job.ps1

# Terminal 3: Monitor Spark logs
docker logs -f spark-master

# Terminal 4: Monitor Kafka
docker exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic lol_matches

# Browser tabs:
# - Spark Master UI: http://localhost:8080
# - Spark App UI: http://localhost:4040
# - Elasticsearch: http://localhost:9200/lol_matches_stream/_count
```

---

## 📊 Expected Logs & Outputs

### Healthy Spark Job Startup

```
26/01/13 02:56:18 INFO SparkContext: Running Spark version 3.5.0
26/01/13 02:56:18 INFO JettyUtils: Start Jetty 0.0.0.0:4040 for SparkUI
26/01/13 02:56:18 INFO Utils: Successfully started service 'SparkUI' on port 4040
26/01/13 02:56:19 INFO StandaloneSchedulerBackend: Connected to Spark cluster with app ID app-20260113025619-0002
2026-01-13 02:56:20 - INFO - ✓ Initialized Spark Structured Streaming
2026-01-13 02:56:20 - INFO - ✓ Connected to Elasticsearch: ['http://elasticsearch:9200']
2026-01-13 02:56:23 - INFO - ✓ Starting Spark Structured Streaming Consumer
```

### Healthy Batch Processing

```
2026-01-13 02:56:35 - INFO - PUT http://elasticsearch:9200/_bulk [status:200 duration:0.108s]
2026-01-13 02:56:35 - INFO - ✓ Bulk indexed: 40 docs, 0 failed
2026-01-13 02:56:35 - INFO - Batch 1: 40 participants, 40 indexed, 0 failed
2026-01-13 02:56:36 - INFO - ✓ Bulk indexed: 110 docs, 0 failed
2026-01-13 02:56:36 - INFO - Batch 2: 110 participants, 110 indexed, 0 failed
```

### Expected Warnings (Harmless)

```
WARN NativeCodeLoader: Unable to load native-hadoop library
# → Normal, using Java fallback

WARN ResolveWriteToStream: spark.sql.adaptive.enabled is not supported in streaming
# → Expected, adaptive execution disabled for streaming

WARN AdminClientConfig: These configurations ... were supplied but are not used yet
# → Normal Kafka consumer config validation
```

---

## 🔍 Debugging Commands Reference

```powershell
# Container Status
docker compose ps
docker compose logs <service> --tail 50

# Kafka
docker exec kafka kafka-topics --list --bootstrap-server localhost:9092
docker exec kafka kafka-topics --describe --topic lol_matches --bootstrap-server localhost:9092
docker exec kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic lol_matches --from-beginning --max-messages 5

# Spark
docker logs spark-master --tail 100
docker logs spark-worker --tail 100
docker exec spark-master ps aux | grep spark
curl http://localhost:8080  # Master UI
curl http://localhost:4040  # Application UI

# Elasticsearch
curl "http://localhost:9200/_cluster/health?pretty"
curl "http://localhost:9200/_cat/indices?v"
curl "http://localhost:9200/lol_matches_stream/_count?pretty"
curl "http://localhost:9200/lol_matches_stream/_search?size=1&pretty"

# Checkpoints
Get-ChildItem .\checkpoints\streaming\ -Recurse
Remove-Item -Recurse -Force .\checkpoints\streaming\*

# Network
docker network inspect bigbig_lol-network
docker exec spark-master ping elasticsearch
docker exec spark-master curl http://kafka:9092
```

---

## ❌ Known Issue: Java 17+ Incompatibility (LEGACY)

**NOTE**: This issue is resolved in production deployment using Docker with Java 11.

### Error Message (Historical Reference)

```
java.lang.UnsupportedOperationException: getSubject is not supported
```

### Root Cause

Spark 3.5.0 không tương thích với Java 17+ do API changes trong Java Security.

### Solution: Use Docker Spark Cluster (Production Approach) ✅

**Recommended Solution**: Deploy Spark job to Docker cluster with Java 11:

```powershell
# Submit Spark Streaming job to Docker cluster
.\submit_spark_job.ps1
```

**Advantages**:

- ✅ Spark 3.5.0 pre-configured with Java 11
- ✅ Distributed processing capability
- ✅ Production-ready environment
- ✅ Window operations and advanced Spark features
- ✅ Checkpoint management for exactly-once processing
- ✅ Spark UI monitoring (http://localhost:4040)

**Current Status**: ✅ **Production deployment verified** (Phase 3 completed)

---

### Alternative: Downgrade to Java 11 (Local Development)

If needed for local development outside Docker:

1. **Download Java 11**:

   - Link: https://adoptium.net/temurin/releases/?version=11
   - Choose: Windows x64 JDK 11 (LTS)

2. **Set JAVA_HOME**:

   ```powershell
   # Set environment variable
   $env:JAVA_HOME = "C:\Program Files\Eclipse Adoptium\jdk-11.0.x"
   $env:PATH = "$env:JAVA_HOME\bin;$env:PATH"

   # Verify
   java -version
   # Should show: openjdk version "11.0.x"
   ```

3. **Run Spark consumer**:
   ```bash
   python streaming-layer/src/spark_streaming_consumer.py
   ```

#### ✅ Solution 3: Use Docker Spark Cluster

Chạy Spark Streaming trong Docker container:

```bash
# Submit job to Spark cluster
docker exec -it spark-master spark-submit \
  --master spark://spark-master:7077 \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 \
  /app/streaming-layer/src/spark_streaming_consumer.py
```

**Note**: Cần mount workspace vào Spark container.

#### ✅ Solution 4: Use Local Mode (Spark 3.4.0)

Downgrade Spark để tránh Java compatibility issues:

```bash
# Uninstall current version
pip uninstall pyspark

# Install Spark 3.4.0 (better Java 17 support)
pip install pyspark==3.4.0
```

---

## 🐛 Other Common Issues

### Issue: HADOOP_HOME Warning

**Error**:

```
Did not find winutils.exe: HADOOP_HOME and hadoop.home.dir are unset
```

**Fix**: Download winutils for Windows

1. Download: https://github.com/cdarlint/winutils/tree/master/hadoop-3.3.4/bin
2. Extract to: `C:\hadoop\bin\winutils.exe`
3. Set environment variable:
   ```powershell
   $env:HADOOP_HOME = "C:\hadoop"
   ```

### Issue: Spark Connection Timeout

**Error**: `Cannot connect to Spark Master`

**Fix**: Use local mode instead

Change `spark_config.yaml`:

```yaml
spark:
  master: "local[*]" # Changed from spark://localhost:7077
```

---

## 📊 Performance Comparison

| Solution               | Throughput  | Latency | Complexity | Recommended For         |
| ---------------------- | ----------- | ------- | ---------- | ----------------------- |
| Spark Local            | ~500 msg/s  | < 5s    | Medium     | Development, Testing    |
| Spark Cluster (Docker) | ~5000 msg/s | < 10s   | High       | ✅ Production (Current) |

**Current Setup**: Spark Cluster on Docker - 190-200 docs/10sec verified ✅

---

## 🚀 Quick Start (Production Deployment)

```powershell
# Terminal 1: Start data generator
python data-generator/src/generator.py --mode continuous

# Terminal 2: Submit Spark job to Docker cluster
.\submit_spark_job.ps1

# Terminal 3: Check Spark UI
Start-Process "http://localhost:4040"

# Terminal 4: Check Elasticsearch
Invoke-WebRequest "http://localhost:9200/lol_matches_stream/_count?pretty"
```

**Expected Output**:

```
============================================================
✓ Starting Spark Structured Streaming Consumer
  Kafka: kafka:9092
  Topic: lol_matches
  Elasticsearch: ['http://elasticsearch:9200']
============================================================
Batch 1: 40 participants, 40 indexed, 0 failed
✓ Bulk indexed: 40 docs, 0 failed
Batch 2: 110 participants, 110 indexed, 0 failed
✓ Bulk indexed: 110 docs, 0 failed
...
```

---

## 📝 Verification Checklist

After running Spark Streaming job:

```powershell
# 1. Run production verification
python verify_phase3_production.py
# Expected: ✓ 5/5 tests passed

# 2. Check Spark Application UI
Start-Process "http://localhost:4040"
# Navigate to "Streaming" tab

# 3. Check document count (should increase continuously)
Invoke-WebRequest "http://localhost:9200/lol_matches_stream/_count?pretty"

# 4. Check in Kibana
# Open: http://localhost:5601
# Go to: Discover → Index Pattern: lol_matches_stream
```

**For detailed guide**: See [PHASE3_QUICKSTART.md](PHASE3_QUICKSTART.md)

---

## 📚 References

- [PySpark Java Version Compatibility](https://spark.apache.org/docs/latest/#downloading)
- [Hadoop winutils for Windows](https://github.com/cdarlint/winutils)
- [Spark Structured Streaming Guide](https://spark.apache.org/docs/latest/structured-streaming-programming-guide.html)
- [Phase 3 Completion Report](PHASE3_COMPLETION_REPORT.md)

---

**Phase 3 Status**: ✅ **Production deployment completed with Spark Cluster**  
**Last Verified**: January 13, 2026  
**Performance**: 27,155+ documents indexed, 190-200 docs/10sec
**Last Updated**: 2026-01-13
