# Phase 3 - Quick Start Guide

## ✅ Phase 3 Status: COMPLETED WITH KIBANA DASHBOARD

**Last Verified**: January 13, 2026  
**Pipeline Status**: ✅ Fully Operational  
**Documents Indexed**: 30,000+ (continuously increasing)  
**Kibana Dashboard**: ✅ Live visualizations active  
**Next Phase**: Phase 4 - Batch Layer

---

## 🚀 Quick Start (5 Minutes)

### Step 1: Verify Prerequisites

```powershell
# Check all Docker services running
docker compose ps

# Expected: 11 services with status "Up"
# - zookeeper, kafka
# - spark-master, spark-worker
# - elasticsearch, kibana
# - cassandra, prometheus, grafana
# - namenode, datanode
```

### Step 2: Run Automated Verification

```powershell
# Verify configuration (22 tests)
python verify_phase3.py

# Expected output:
# ✓ 22/22 tests passed
# ✓ Streaming Layer properly configured
```

### Step 3: Start Data Generator

```powershell
# Open new PowerShell window and run:
cd E:\FILEMANAGEMENT_PC\_WORKSPACE\PROGRESS\bigbig
.\.venv\Scripts\Activate.ps1
python data-generator/src/generator.py --mode continuous

# Expected output:
# 2026-01-13 10:13:54 - INFO - Sent: SEA_win vs. PHX_lose | Duration: 1845s
# 2026-01-13 10:13:55 - INFO - Sent: CLG_win vs. FNC_lose | Duration: 1792s
# (Continues at ~2 matches/second)
```

### Step 4: Submit Spark Streaming Job

```powershell
# In main PowerShell window:
.\submit_spark_job.ps1

# Wait 15-20 seconds for initialization

# Expected output:
# ✓ Installing Python dependencies
# ✓ Submitting job...
# ✓ Spark version 3.5.0
# ✓ Successfully started service 'SparkUI' on port 4040
# ✓ Connected to Spark cluster with app ID app-20260113025619-XXXX
# ✓ Initialized Spark Structured Streaming
# ✓ Connected to Elasticsearch
# ✓ Starting Spark Structured Streaming Consumer
# Batch 1: 40 participants, 40 indexed, 0 failed
# Batch 2: 110 participants, 110 indexed, 0 failed
```

### Step 5: Verify Production Deployment

```powershell
# Run production verification (5 tests)
python verify_phase3_production.py

# Expected output:
# ✓ 5/5 tests passed
# ✓ Phase 3 production deployment verified successfully!
```

### Step 6: Setup Kibana Dashboard (5 Minutes)

```powershell
# Open Kibana
Start-Process "http://localhost:5601"
```

**Quick Setup**:

1. Create index pattern: `lol_matches_stream*`
2. Time field: `timestamp`
3. Create 5 visualizations:
   - Document count over time (line chart)
   - Win rate by champion (pie chart)
   - KDA by position (bar chart)
   - Gold per minute distribution (histogram)
   - Damage by champion (horizontal bar)
4. Build dashboard "LoL Match Analytics - Real-Time"
5. Enable auto-refresh: 5 seconds
6. Verify live data updates

**Detailed guide**: See [KIBANA_SETUP_GUIDE.md](KIBANA_SETUP_GUIDE.md)

### Step 7: Access Monitoring UIs

Open in browser:

- **Spark Application UI**: http://localhost:4040 (streaming query metrics)
- **Spark Master UI**: http://localhost:8080 (cluster status)
- **Elasticsearch**: http://localhost:9200/lol_matches_stream/\_count (document count)
- **Kibana Dashboard**: http://localhost:5601/app/dashboards (real-time visualizations)

---

## 📊 Verification Commands

### Check Document Count

```powershell
# PowerShell
Invoke-WebRequest "http://localhost:9200/lol_matches_stream/_count?pretty"

# Expected output:
# {
#   "count": 21025,  # Increases by ~190-200 per 10 seconds
#   "_shards": {
#     "total": 3,
#     "successful": 3
#   }
# }
```

### Check Spark Job Status

```powershell
# Check process running
docker exec spark-master ps aux | Select-String "spark_streaming_consumer"

# Expected: Non-empty output showing Java/Python processes
```

### Check Recent Batches

```powershell
# View Spark logs
docker logs spark-master --tail 50

# Expected patterns:
# Batch X: Y participants, Y indexed, 0 failed
# ✓ Bulk indexed: Z docs, 0 failed
```

---

## 🎯 Performance Metrics (Actual)

### Data Generation

- **Rate**: 2 matches/second (10-20 participants/second)
- **Kafka Topic**: `lol_matches` (3 partitions)
- **Message Size**: ~2-3 KB per match

### Spark Streaming

- **Batch Interval**: 5 seconds
- **Processing Time**: 1-3 seconds/batch
- **Throughput**: 40-200 participants/batch
- **Latency**: < 5 seconds end-to-end

### Elasticsearch

- **Indexing Rate**: 190-200 documents per 10 seconds
- **Index**: `lol_matches_stream` (3 primary shards, 1 replica)
- **Failed Documents**: 0 (100% success rate)
- **Current Count**: 21,025+ documents

---

## 🚨 Troubleshooting Quick Reference

### Issue: Spark UI Not Accessible

```powershell
# Check if job running
docker exec spark-master ps aux | Select-String "spark"

# If empty, restart:
.\submit_spark_job.ps1
Start-Sleep -Seconds 15
Start-Process "http://localhost:4040"
```

### Issue: No Documents in Elasticsearch

```powershell
# Check Spark logs for errors
docker logs spark-master --tail 50 | Select-String "ERROR"

# Check data generator running
# Look for separate PowerShell window with generator output

# Verify Kafka has messages
docker exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic lol_matches --max-messages 1
```

### Issue: Offset Error

```powershell
# Clear checkpoints and restart
Remove-Item -Recurse -Force .\checkpoints\streaming\*
.\submit_spark_job.ps1
```

### Issue: Kafka Container Down

```powershell
# Remove volumes and recreate
docker compose down -v kafka
docker volume rm bigbig_kafka_data
docker compose up -d kafka
Start-Sleep -Seconds 60

# Recreate topic
docker exec kafka kafka-topics --bootstrap-server localhost:9092 \
  --create --topic lol_matches --partitions 3 --replication-factor 1

# Clear checkpoints
Remove-Item -Recurse -Force .\checkpoints\streaming\*

# Restart job
.\submit_spark_job.ps1
```

**Full troubleshooting guide**: See [SPARK_TROUBLESHOOTING.md](SPARK_TROUBLESHOOTING.md)

---

## 📁 Project Files

### Main Scripts

- `verify_phase3.py` - Configuration verification (22 tests)
- `verify_phase3_production.py` - Production deployment verification (5 tests)
- `submit_spark_job.ps1` - Spark job submission script

### Source Code

- `streaming-layer/src/spark_streaming_consumer.py` - Main Spark Streaming application
- `streaming-layer/src/elasticsearch_indexer.py` - Elasticsearch client with bulk indexing
- `streaming-layer/src/processors.py` - Data processing functions
- `data-generator/src/generator.py` - Match data generator

### Configuration

- `streaming-layer/config/spark_config.yaml` - Spark and Kafka settings
- `streaming-layer/config/es_mapping.json` - Elasticsearch index mapping
- `docker-compose.yml` - Infrastructure definition

### Checkpoints

- `checkpoints/streaming/` - Spark checkpoint directory (auto-managed)

---

## 🎓 What We Learned

### Issues Encountered & Solved

1. **Kafka Cluster ID Mismatch**

   - Problem: Container kept restarting with InconsistentClusterIdException
   - Solution: Remove volumes and recreate with fresh metadata
   - Prevention: Always use named volumes, backup important data

2. **Spark Checkpoint Offset Error**

   - Problem: Job crashed with "offset was changed from 383 to 28"
   - Solution: Clear checkpoint directory when Kafka topic is recreated
   - Prevention: Document checkpoint management in deployment procedures

3. **Spark UI Not Accessible**
   - Problem: Port 4040 unreachable despite port mapping
   - Root Cause: No active Spark application running
   - Solution: Ensure data generator provides stream before submitting job
   - Learning: Spark Application UI only exists when job is active

### Key Learnings

- **Docker Volume Management**: Persistent volumes can contain corrupted metadata, requiring manual cleanup
- **Checkpoint Management**: Critical for exactly-once processing, must be managed carefully during infrastructure changes
- **Distributed System Debugging**: Requires checking multiple components (Kafka, Spark, Elasticsearch) systematically
- **Production Readiness**: Always verify full pipeline before declaring success

---

## ✅ Completion Checklist

- [x] All Docker services running (11 containers)
- [x] Kafka topic `lol_matches` configured (3 partitions)
- [x] Elasticsearch index `lol_matches_stream` created
- [x] Data generator producing matches (2/second)
- [x] Spark Streaming job processing batches
- [x] Elasticsearch receiving documents (30,000+)
- [x] Spark UI accessible (localhost:4040)
- [x] End-to-end pipeline verified (5/5 tests passed)
- [x] Troubleshooting documentation complete
- [x] Production deployment guide created
- [x] **Kibana dashboard showing live data updates** ✅ COMPLETED

**✅ PHASE 3 FULLY COMPLETED**

---

## 🎯 Next Steps

### Phase 4: Batch Layer

- Kafka → HDFS batch ingestion
- PySpark ETL pipeline
- Cassandra storage
- Historical data analysis

### Immediate Actions

1. **Complete Kibana dashboard setup** (see KIBANA_SETUP_GUIDE.md)
2. Monitor Elasticsearch disk usage (set alerts at 80%)
3. Configure log rotation for Spark logs
4. Document backup and recovery procedures

---

## 📞 Support

If you encounter issues:

1. Check [SPARK_TROUBLESHOOTING.md](SPARK_TROUBLESHOOTING.md)
2. Run `python verify_phase3_production.py`
3. Check logs: `docker logs spark-master --tail 100`
4. Verify services: `docker compose ps`

**Last Updated**: January 13, 2026  
**Phase 3 Status**: ✅ **COMPLETED** (Including Kibana Dashboard)  
**Next Phase**: Phase 4 - Batch Layer (Kafka → HDFS → Cassandra)
