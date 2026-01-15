---
description: Run complete batch layer pipeline
---

# Batch Layer Workflow

This workflow runs the complete batch processing pipeline from Kafka to Cassandra.

## Prerequisites

- Docker containers running
- Cassandra schema initialized

## Steps

### 1. Start Docker Services
```powershell
docker-compose up -d
```

Wait for all services to be healthy.

### 2. Setup Cassandra Schema (First Time Only)
```powershell
.\setup_cassandra.ps1
```

This creates the `lol_data` keyspace and `match_stats` table.

### 3. Run Batch Consumer (Kafka → HDFS)
// turbo
```powershell
.\run_batch_consumer.ps1 -Batches 5
```

This consumes 5 batches of data from Kafka and writes to HDFS in Parquet format.

**Expected Output:**
```
✅ Batch 1/5: Consumed 100 messages
✅ Batch 2/5: Consumed 100 messages
...
✅ All batches written to HDFS
```

### 4. Verify HDFS Data
// turbo
```powershell
docker exec namenode hadoop fs -ls -R /data/lol_matches
```

You should see Parquet files organized by date.

### 5. Run PySpark ETL (HDFS → Cassandra)
// turbo
```powershell
.\run_batch_etl_docker.ps1
```

This processes data from HDFS and writes to Cassandra.

**Expected Output:**
```
🚀 Starting PySpark ETL Pipeline
📖 Reading from HDFS
✅ Loaded 500 records from HDFS
🧹 Cleaning data
✅ Cleaned data: 0 invalid records removed
🔧 Engineering features
✅ Features engineered
💾 Writing to Cassandra
✅ Written 500 records to Cassandra
✅ ETL Pipeline Completed Successfully!
```

### 6. Verify Cassandra Data
// turbo
```powershell
docker exec cassandra cqlsh -e "SELECT COUNT(*) FROM lol_data.match_stats;"
```

You should see the count of processed records.

### 7. Query Sample Data
```powershell
docker exec -it cassandra cqlsh
```

Then in CQL shell:
```sql
USE lol_data;
SELECT * FROM match_stats LIMIT 10;
```

## Troubleshooting

### No data in HDFS
- Check Kafka has messages: `docker exec kafka kafka-topics --list --bootstrap-server localhost:9092`
- Re-run batch consumer with more batches

### PySpark ETL fails
- Check container logs: `docker logs pyspark-worker`
- Verify HDFS has data for the specified date
- Ensure Cassandra is running: `docker exec cassandra nodetool status`

### Cassandra connection errors
- Restart Cassandra: `docker-compose restart cassandra`
- Wait 30 seconds for Cassandra to be ready
- Re-run setup script: `.\setup_cassandra.ps1`

## Notes

- Data is partitioned by date in HDFS: `/data/lol_matches/YYYY/MM/DD/`
- ETL can be re-run safely (uses append mode)
- For specific dates, use: `.\run_batch_etl_docker.ps1 -Date "2026/01/15"`
