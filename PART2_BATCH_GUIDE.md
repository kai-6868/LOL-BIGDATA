# 🚀 PHẦN 2: BATCH PROCESSING LAYER

## 📋 Tổng quan

Pipeline batch xử lý dữ liệu theo luồng:

```
Kafka → Batch Consumer → HDFS (Parquet) → PySpark ETL → Cassandra
```

### Các thành phần:
- **Batch Consumer**: Đọc data từ Kafka theo batch
- **HDFS**: Lưu trữ data dạng Parquet (columnar format)
- **PySpark ETL**: Transform và aggregate data
- **Cassandra**: NoSQL database cho historical data

---

## 🎯 Yêu cầu

### Đã hoàn thành Part 1
- ✅ Kafka đang chạy với data
- ✅ Docker containers running
- ✅ Data generator đang tạo data

### Containers cần thiết
- ✅ `namenode` (HDFS)
- ✅ `datanode` (HDFS)
- ✅ `cassandra`
- ✅ `kafka`

---

## 🚀 QUICK START (Recommended)

### Option 1: Run All Steps Automatically

```powershell
.\run_batch_complete.ps1
```

Script này sẽ tự động:
1. ✅ Setup HDFS directories
2. ✅ Setup Cassandra schema
3. ✅ Run batch consumer
4. ✅ Run PySpark ETL

**Thời gian**: ~2-3 phút

---

## 📝 MANUAL SETUP (Step by Step)

Nếu muốn chạy từng bước riêng:

### Bước 1: Setup HDFS

```powershell
.\setup_hdfs.ps1
```

**Script này sẽ**:
- Tạo `/data/lol_matches` directory
- Set permissions 777
- Tạo partition theo ngày hiện tại

### Bước 2: Setup Cassandra

```powershell
.\setup_cassandra.ps1
```

**Script này sẽ**:
- Copy `init_cassandra.cql` vào container
- Execute CQL script
- Verify schema created

### Bước 3: Run Batch Consumer

```powershell
.\run_batch_consumer.ps1 -Batches 1 -BatchSize 50
```

**Parameters**:
- `-Batches`: Số lượng batches (default: 1)
- `-BatchSize`: Messages per batch (default: 50)

**Script này sẽ**:
- Consume data từ Kafka
- Write Parquet files vào HDFS
- Partition theo date (YYYY/MM/DD)

### Bước 4: Run PySpark ETL

```powershell
.\run_batch_etl.ps1 -Date "2026/01/15"
```

**Parameters**:
- `-Date`: Date to process (default: today)

**Script này sẽ**:
- Read Parquet từ HDFS
- Transform và aggregate
- Write vào Cassandra

---

## ✅ Verification

### Check HDFS Data

```powershell
# List all files
docker exec namenode hdfs dfs -ls -R /data/lol_matches

# Check file size
docker exec namenode hdfs dfs -du -h /data/lol_matches

# View file content (first few rows)
docker exec namenode hdfs dfs -cat /data/lol_matches/2026/01/15/*.parquet | head -n 10
```

### Check Cassandra Data

```powershell
# Connect to Cassandra
docker exec -it cassandra cqlsh

# Query data
USE lol_data;
SELECT COUNT(*) FROM match_stats;
SELECT * FROM match_stats LIMIT 5;

# Exit
exit;
```

---

## 🔍 Troubleshooting

### Issue 1: HDFS Permission Denied

**Error**:
```
PermissionError: Permission denied writing to HDFS
```

**Solution**:
```powershell
docker exec namenode hdfs dfs -chmod -R 777 /data/lol_matches
```

### Issue 2: Cassandra Connection Failed

**Error**:
```
NoHostAvailable: Unable to connect to Cassandra
```

**Solution**:
```powershell
# Check Cassandra is running
docker exec cassandra nodetool status

# Restart if needed
docker-compose restart cassandra
Start-Sleep -Seconds 30

# Re-run setup
.\setup_cassandra.ps1
```

### Issue 3: No Data in Kafka

**Error**:
```
Batch timeout reached. Got 0/50 messages
```

**Solution**:
- Ensure Data Generator is running (Part 1)
- Check Kafka has data:
```powershell
docker exec kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic lol_matches --max-messages 1
```

### Issue 4: HDFS Path Not Found

**Error**:
```
FileNotFoundError: HDFS path not found
```

**Solution**:
```powershell
# Re-run HDFS setup
.\setup_hdfs.ps1

# Or manually create
docker exec namenode hdfs dfs -mkdir -p /data/lol_matches/$(Get-Date -Format "yyyy/MM/dd")
docker exec namenode hdfs dfs -chmod 777 /data/lol_matches/$(Get-Date -Format "yyyy/MM/dd")
```

### Issue 5: Python Module Not Found

**Error**:
```
ModuleNotFoundError: No module named 'hdfs'
```

**Solution**:
```powershell
# Activate venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

---

## 📊 Complete Workflow (Part 1 + Part 2)

### Terminal 1: Data Generator (Part 1)
```powershell
.\.venv\Scripts\Activate.ps1
python lol_match_generator.py
```

### Terminal 2: Spark Streaming (Part 1)
```powershell
.\submit_spark_job.ps1
```

### Terminal 3: Batch Processing (Part 2)
```powershell
# One-time setup
.\setup_hdfs.ps1
.\setup_cassandra.ps1

# Run periodically (e.g., every 5 minutes)
.\run_batch_consumer.ps1 -Batches 1
.\run_batch_etl.ps1
```

---

## 📈 Performance Metrics

| Metric | Value |
|--------|-------|
| Batch size | 50 messages |
| Batch timeout | 60 seconds |
| HDFS write time | ~1-2 seconds/batch |
| Parquet file size | ~50-100 KB/batch |
| ETL processing time | ~5-10 seconds/batch |
| Cassandra write time | ~2-3 seconds/batch |
| Total time per batch | ~10-15 seconds |

---

## 🎯 Success Criteria

Batch layer chạy thành công khi:

- ✅ HDFS directories created với permissions đúng
- ✅ Cassandra schema initialized
- ✅ Batch consumer đọc data từ Kafka
- ✅ Parquet files được lưu vào HDFS
- ✅ PySpark ETL process data thành công
- ✅ Data được ghi vào Cassandra
- ✅ Query Cassandra thấy data

---

## 💡 Tips & Best Practices

### 1. Automated Batch Processing

Tạo scheduled task để chạy batch processing tự động:

```powershell
# Windows Task Scheduler
# Run every 5 minutes:
.\run_batch_consumer.ps1 -Batches 1
.\run_batch_etl.ps1
```

### 2. Monitor HDFS Space

```powershell
# Check HDFS usage
docker exec namenode hdfs dfs -df -h

# Clean old data (older than 30 days)
docker exec namenode hdfs dfs -rm -r /data/lol_matches/2025/*
```

### 3. Partition Strategy

Data được partition theo date:
```
/data/lol_matches/
  ├── 2026/
  │   ├── 01/
  │   │   ├── 15/
  │   │   │   ├── matches_20260115_100000_batch1.parquet
  │   │   │   ├── matches_20260115_100500_batch2.parquet
```

Lợi ích:
- ✅ Dễ query historical data
- ✅ Dễ delete old data
- ✅ Optimize ETL performance

### 4. Backup Cassandra

```powershell
# Create snapshot
docker exec cassandra nodetool snapshot lol_data

# List snapshots
docker exec cassandra nodetool listsnapshots
```

### 5. Monitor Logs

```powershell
# Batch consumer logs
cat batch-layer/logs/batch_consumer_$(Get-Date -Format "yyyyMMdd").log

# Cassandra logs
docker logs cassandra --tail 100

# HDFS logs
docker logs namenode --tail 100
```

---

## 📝 Scripts Summary

| Script | Purpose | Usage |
|--------|---------|-------|
| `run_batch_complete.ps1` | **Run all steps** | `.\run_batch_complete.ps1` |
| `setup_hdfs.ps1` | Setup HDFS | `.\setup_hdfs.ps1` |
| `setup_cassandra.ps1` | Setup Cassandra | `.\setup_cassandra.ps1` |
| `run_batch_consumer.ps1` | Kafka → HDFS | `.\run_batch_consumer.ps1 -Batches 1` |
| `run_batch_etl.ps1` | HDFS → Cassandra | `.\run_batch_etl.ps1 -Date "2026/01/15"` |

---

## 🚀 Next Steps

Sau khi hoàn thành Part 2:

1. **Verify data flow**:
   - Kafka → HDFS → Cassandra
   - Check data consistency

2. **Optimize performance**:
   - Adjust batch size
   - Tune Spark configs

3. **Setup monitoring**:
   - Track batch processing metrics
   - Alert on failures

4. **Move to Part 3**: Machine Learning Layer

---

**Chúc bạn thành công! 🎉**

Nếu gặp vấn đề, check phần Troubleshooting hoặc xem logs để debug.
