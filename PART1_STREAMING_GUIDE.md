# 🚀 PHẦN 1: REAL-TIME STREAMING PIPELINE

## 📋 Tổng quan

Pipeline real-time xử lý dữ liệu trận đấu League of Legends theo luồng:

```
Data Generator → Kafka → Spark Streaming → Elasticsearch → Kibana
```

### Các thành phần:
- **Data Generator**: Tạo dữ liệu trận đấu giả lập
- **Kafka**: Message queue để stream data
- **Spark Streaming**: Xử lý và transform data real-time
- **Elasticsearch**: Lưu trữ và index data
- **Kibana**: Visualization và dashboard

---

## 🎯 Yêu cầu hệ thống

### Phần cứng
- **RAM**: Tối thiểu 8GB (khuyến nghị 16GB)
- **CPU**: 4 cores trở lên
- **Disk**: 50GB trống

### Phần mềm
- **Docker Desktop**: Version 20.10+
- **Python**: 3.8+
- **PowerShell**: 5.1+ (Windows) hoặc Bash (Linux/Mac)

### Ports cần thiết
- `9092`: Kafka
- `9200`: Elasticsearch
- `5601`: Kibana
- `8080`: Spark Master UI
- `4040`: Spark Application UI
- `9870`: HDFS NameNode (optional)

---

## 📦 Bước 1: Cài đặt môi trường

### 1.1. Clone repository

```bash
git clone <repository-url>
cd LOL-BIGDATA
```

### 1.2. Tạo Python virtual environment

```powershell
# Windows
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Linux/Mac
python3 -m venv .venv
source .venv/bin/activate
```

### 1.3. Cài đặt dependencies

```powershell
pip install -r requirements.txt
```

**Lưu ý**: File `requirements.txt` đã bao gồm tất cả packages cần thiết:
- kafka-python
- elasticsearch
- pyspark
- pandas, numpy
- faker (để generate data)

---

## 🐳 Bước 2: Build Custom Spark Image

**Quan trọng**: Bước này chỉ cần chạy **1 lần duy nhất** khi setup lần đầu.

### 2.1. Build image

```powershell
.\build_spark_image.ps1
```

**Thời gian**: ~5-10 phút (tùy tốc độ mạng)

Script này sẽ:
- Build custom Spark image với Python packages pre-installed
- Install Kafka JARs
- Tối ưu để Spark job start nhanh (<5 giây)

### 2.2. Verify image

```powershell
docker images | Select-String "spark-custom"
```

Kết quả mong đợi:
```
spark-custom   3.5.0   <image-id>   <size>
```

---

## 🚀 Bước 3: Khởi động Infrastructure

### 3.1. Start Docker containers

```powershell
docker-compose up -d
```

**Đợi 60 giây** để tất cả services khởi động hoàn toàn.

### 3.2. Verify containers

```powershell
docker ps
```

Phải thấy các containers:
- ✅ `kafka`
- ✅ `zookeeper`
- ✅ `elasticsearch`
- ✅ `kibana`
- ✅ `spark-master`
- ✅ `spark-worker`

### 3.3. Check container health

```powershell
# Check Kafka
docker exec kafka kafka-broker-api-versions --bootstrap-server localhost:9092

# Check Elasticsearch
curl http://localhost:9200

# Check Kibana
curl http://localhost:5601/api/status
```

---

## 📊 Bước 4: Tạo Kafka Topic

### 4.1. Create topic

```powershell
docker exec kafka kafka-topics --create `
  --bootstrap-server localhost:9092 `
  --topic lol_matches `
  --partitions 3 `
  --replication-factor 1
```

### 4.2. Verify topic

```powershell
docker exec kafka kafka-topics --list --bootstrap-server localhost:9092
```

Kết quả mong đợi:
```
lol_matches
```

### 4.3. Describe topic (optional)

```powershell
docker exec kafka kafka-topics --describe --bootstrap-server localhost:9092 --topic lol_matches
```

---

## 🔍 Bước 5: Tạo Elasticsearch Index

### 5.1. Create index với mapping

```powershell
.\create_es_index.ps1
```

Script này sẽ:
- Tạo index `lol_matches_stream`
- Set mapping cho các fields
- Configure analyzers

### 5.2. Verify index

```powershell
curl http://localhost:9200/lol_matches_stream
```

---

## 🎲 Bước 6: Start Data Generator

### 6.1. Activate virtual environment (nếu chưa)

```powershell
.\.venv\Scripts\Activate.ps1
```

### 6.2. Start generator

```powershell
python lol_match_generator.py
```

**Output mẫu**:
```
2026-01-15 14:30:01 - INFO - Starting LoL Match Data Generator
2026-01-15 14:30:01 - INFO - Connected to Kafka: localhost:29092
2026-01-15 14:30:02 - INFO - ✓ Sent match 1/100 to Kafka
2026-01-15 14:30:03 - INFO - ✓ Sent match 2/100 to Kafka
...
```

### 6.3. Verify data trong Kafka

Mở terminal mới và chạy:

```powershell
docker exec kafka kafka-console-consumer `
  --bootstrap-server localhost:9092 `
  --topic lol_matches `
  --max-messages 1
```

Bạn sẽ thấy JSON data của 1 trận đấu.

**Lưu ý**: Để generator chạy trong background, giữ terminal này mở.

---

## ⚡ Bước 7: Start Spark Streaming Job

### 7.1. Mở terminal mới

Giữ terminal của Data Generator chạy, mở terminal mới.

### 7.2. Submit Spark job

```powershell
.\submit_spark_job.ps1
```

**Script này sẽ**:
- Submit Spark job với config tối ưu
- Không cần install packages (đã có trong custom image)
- Start streaming từ Kafka → Elasticsearch
- Instant startup (<5 giây)

### 7.3. Monitor Spark job

**Output mẫu**:
```
===========================================================
  Submitting Spark Streaming Job (OPTIMIZED - Instant)
===========================================================

Job Configuration:
   Master: spark://spark-master:7077
   Driver Memory: 2g
   Executor Memory: 2g
   Executor Cores: 2
   Mode: Structured Streaming

Submitting job...
2026-01-15 14:35:01 INFO SparkContext: Running Spark version 3.5.0
2026-01-15 14:35:02 INFO StreamExecution: Starting new streaming query
...
```

### 7.4. Verify Spark UI

Mở browser:
- **Spark Master UI**: http://localhost:8080
- **Spark Application UI**: http://localhost:4040

Tại Application UI, bạn sẽ thấy:
- Streaming tab với batch processing
- Input rate, processing time
- Number of records processed

---

## 📈 Bước 8: Verify Data trong Elasticsearch

### 8.1. Check document count

```powershell
curl http://localhost:9200/lol_matches_stream/_count
```

Kết quả:
```json
{
  "count": 150,  // Số lượng tăng dần
  "_shards": {...}
}
```

### 8.2. Query sample data

```powershell
curl http://localhost:9200/lol_matches_stream/_search?size=1
```

### 8.3. Monitor indexing rate

```powershell
# Chạy nhiều lần để thấy count tăng
while ($true) {
    $count = (curl http://localhost:9200/lol_matches_stream/_count | ConvertFrom-Json).count
    Write-Host "Documents: $count" -ForegroundColor Cyan
    Start-Sleep -Seconds 5
}
```

---

## 📊 Bước 9: Visualize với Kibana

### 9.1. Mở Kibana

Browser: http://localhost:5601

### 9.2. Create Index Pattern

1. Menu → **Stack Management** → **Index Patterns**
2. Click **Create index pattern**
3. Index pattern name: `lol_matches_stream*`
4. Click **Next step**
5. Time field: `@timestamp`
6. Click **Create index pattern**

### 9.3. Explore Data

1. Menu → **Discover**
2. Select index pattern: `lol_matches_stream*`
3. Bạn sẽ thấy data real-time

### 9.4. Create Visualizations

#### Visualization 1: Match Count Over Time

1. Menu → **Visualize** → **Create visualization**
2. Type: **Line**
3. Index: `lol_matches_stream*`
4. Metrics:
   - Y-axis: Count
5. Buckets:
   - X-axis: Date Histogram
   - Field: @timestamp
   - Interval: Auto
6. **Save**: "Match Count Over Time"

#### Visualization 2: Top Champions

1. Create visualization → **Pie**
2. Metrics: Count
3. Buckets:
   - Split slices: Terms
   - Field: champion_name.keyword
   - Size: 10
4. **Save**: "Top 10 Champions"

#### Visualization 3: Win Rate by Team

1. Create visualization → **Metric**
2. Add filters:
   - Filter 1: `win: true`
   - Filter 2: `team_id: 100`
3. **Save**: "Blue Team Win Rate"

### 9.5. Create Dashboard

1. Menu → **Dashboard** → **Create dashboard**
2. Add visualizations:
   - Match Count Over Time
   - Top 10 Champions
   - Blue Team Win Rate
3. **Save**: "LoL Real-time Dashboard"

### 9.6. Enable Auto-refresh

1. Trong Dashboard, click biểu tượng đồng hồ (top-right)
2. Set auto-refresh: **5 seconds**
3. Bạn sẽ thấy dashboard update real-time!

---

## 🔍 Monitoring & Troubleshooting

### Monitor Logs

```powershell
# Kafka logs
docker logs kafka -f --tail 100

# Spark logs
docker logs spark-master -f --tail 100

# Elasticsearch logs
docker logs elasticsearch -f --tail 100
```

### Common Issues

#### Issue 1: Kafka không nhận data

**Triệu chứng**: Generator chạy nhưng không thấy data trong Kafka

**Giải pháp**:
```powershell
# Check Kafka connectivity
docker exec kafka kafka-broker-api-versions --bootstrap-server localhost:9092

# Restart Kafka
docker-compose restart kafka
```

#### Issue 2: Spark job bị lỗi "partitions are gone"

**Triệu chứng**: 
```
ERROR: Set(lol_matches-2, lol_matches-1) are gone
```

**Giải pháp**: Script `start_spark_streaming.ps1` đã tự động fix. Nếu vẫn lỗi:
```powershell
# Manual cleanup
docker exec spark-master rm -rf /opt/spark/work-dir/checkpoints/streaming
.\start_spark_streaming.ps1
```

#### Issue 3: Elasticsearch không nhận data

**Triệu chứng**: Spark chạy OK nhưng ES count = 0

**Giải pháp**:
```powershell
# Check ES health
curl http://localhost:9200/_cluster/health

# Check index
curl http://localhost:9200/_cat/indices?v

# Recreate index
.\create_es_index.ps1
```

#### Issue 4: Kibana không hiển thị data

**Triệu chứng**: Index pattern created nhưng không thấy data

**Giải pháp**:
1. Check time range (top-right): Set to "Last 15 minutes"
2. Refresh index pattern: Stack Management → Index Patterns → Refresh
3. Check @timestamp field exists

---

## 🛑 Dừng hệ thống

### Dừng từng thành phần

```powershell
# 1. Stop Data Generator
# Ctrl+C trong terminal của generator

# 2. Stop Spark Job
# Ctrl+C trong terminal của Spark

# 3. Stop Docker containers
docker-compose down
```

### Dừng và xóa data (Clean start)

```powershell
# Stop và xóa volumes
docker-compose down -v

# Hoặc chỉ xóa Kafka data
docker-compose down
docker volume rm lol-bigdata_kafka_data
```

---

## 🔄 Restart hệ thống

### Restart giữ data cũ

```powershell
# 1. Start containers
docker-compose up -d
Start-Sleep -Seconds 60

# 2. Start generator (terminal 1)
.\.venv\Scripts\Activate.ps1
python lol_match_generator.py

# 3. Start Spark (terminal 2)
.\start_spark_streaming.ps1
```

### Restart clean (xóa data cũ)

```powershell
# 1. Stop và xóa Kafka data
docker-compose down
docker volume rm lol-bigdata_kafka_data

# 2. Start containers
docker-compose up -d
Start-Sleep -Seconds 60

# 3. Recreate topic
docker exec kafka kafka-topics --create --bootstrap-server localhost:9092 --topic lol_matches --partitions 3 --replication-factor 1

# 4. Recreate ES index
.\create_es_index.ps1

# 5. Start generator
python lol_match_generator.py

# 6. Start Spark
.\start_spark_streaming.ps1
```

---

## 📊 Performance Metrics

### Expected Performance

| Metric | Value |
|--------|-------|
| Data generation rate | ~1 match/second |
| Kafka throughput | ~100 messages/second |
| Spark processing time | <1 second/batch |
| End-to-end latency | <5 seconds |
| Elasticsearch indexing | ~50 docs/second |

### Monitor Performance

```powershell
# Kafka lag
docker exec kafka kafka-consumer-groups --bootstrap-server localhost:9092 --describe --group spark-streaming

# Spark metrics
# Check http://localhost:4040/streaming/

# Elasticsearch indexing rate
curl http://localhost:9200/_nodes/stats/indices/indexing
```

---

## 🎯 Success Criteria

Hệ thống chạy thành công khi:

- ✅ Data Generator tạo data liên tục
- ✅ Kafka nhận và lưu messages
- ✅ Spark job process data không lỗi
- ✅ Elasticsearch document count tăng dần
- ✅ Kibana dashboard hiển thị data real-time
- ✅ Auto-refresh hoạt động mượt mà

---

## 📝 Files quan trọng

| File | Mục đích |
|------|----------|
| `start_spark_streaming.ps1` | **Main script** - Start Spark với auto-clean checkpoint |
| `lol_match_generator.py` | Generate fake match data |
| `docker-compose.yml` | Infrastructure definition |
| `streaming-layer/src/spark_streaming_consumer.py` | Spark streaming logic |
| `streaming-layer/config/spark_config_docker.yaml` | Spark configuration |
| `create_es_index.ps1` | Create Elasticsearch index |

---

## 🚀 Next Steps

Sau khi hoàn thành Phần 1, bạn có thể:

1. **Tùy chỉnh data generation**:
   - Sửa `lol_match_generator.py`
   - Thay đổi rate, số lượng matches

2. **Tối ưu Spark processing**:
   - Sửa `spark_config_docker.yaml`
   - Adjust batch interval, memory

3. **Tạo thêm visualizations**:
   - Heatmaps
   - Aggregations
   - Custom metrics

4. **Chuyển sang Phần 2**: Batch Processing Layer

---

## 💡 Tips & Best Practices

1. **Luôn dùng `start_spark_streaming.ps1`** thay vì submit trực tiếp
   - Tự động clean checkpoint
   - Tránh lỗi offset

2. **Monitor logs thường xuyên**
   - Phát hiện lỗi sớm
   - Optimize performance

3. **Backup Kibana dashboards**
   - Export saved objects
   - Version control

4. **Clean restart khi có vấn đề**
   - Xóa volumes
   - Recreate từ đầu

5. **Check Docker resources**
   - Docker Desktop → Settings → Resources
   - Ensure 8GB+ RAM allocated

---

**Chúc bạn thành công! 🎉**

Nếu gặp vấn đề, check phần Troubleshooting hoặc xem logs để debug.
