# Docker Images Restore Guide

## 📦 Đã Backup Docker Images

File: `bigbig-stack-snapshot.tar`  
Size: ~10-12 GB  
Images: 11 containers (Kafka, Spark, Hadoop, Cassandra, ES, Kibana, etc.)

---

## 🔄 Restore trên máy mới

### Prerequisites

- Docker Desktop installed (Windows/Mac/Linux)
- ~30 GB free disk space (cho images + volumes)
- 16-32 GB RAM recommended

### Step 1: Copy file .tar

```bash
# Transfer file qua:
# - USB drive
# - Network share
# - Cloud storage (Google Drive, OneDrive)
# - SCP/FTP

# Verify file size
ls -lh bigbig-stack-snapshot.tar  # Linux/Mac
Get-Item bigbig-stack-snapshot.tar | Select-Object Length  # Windows
```

### Step 2: Load Docker images

```bash
# Load all images từ .tar file
docker load -i bigbig-stack-snapshot.tar

# Output sẽ hiển thị:
# Loaded image: bigbig-kafka:snapshot
# Loaded image: bigbig-zookeeper:snapshot
# ... (11 images total)
```

**Thời gian**: ~5-15 phút tùy tốc độ disk

### Step 3: Verify images loaded

```bash
# Check images
docker images | grep bigbig

# Expected output:
# bigbig-kafka              snapshot    ...
# bigbig-zookeeper          snapshot    ...
# bigbig-spark-master       snapshot    ...
# bigbig-spark-worker       snapshot    ...
# bigbig-hadoop-namenode    snapshot    ...
# bigbig-hadoop-datanode    snapshot    ...
# bigbig-cassandra          snapshot    ...
# bigbig-elasticsearch      snapshot    ...
# bigbig-kibana             snapshot    ...
# bigbig-prometheus         snapshot    ...
# bigbig-grafana            snapshot    ...
```

### Step 4: Clone source code

```bash
# Clone Git repository
git clone <your-repo-url>
cd bigbig

# Setup Python environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1  # Windows
source .venv/bin/activate      # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### Step 5: Update docker-compose.yml

**QUAN TRỌNG**: Cập nhật docker-compose.yml để dùng snapshot images

```yaml
services:
  kafka:
    image: bigbig-kafka:snapshot  # Thay vì confluentinc/cp-kafka:7.5.0
    # ... rest of config
  
  zookeeper:
    image: bigbig-zookeeper:snapshot
    # ... rest of config
  
  spark-master:
    image: bigbig-spark-master:snapshot
    # ... rest of config
  
  # ... tương tự cho các services khác
```

### Step 6: Start services

```bash
# Start all containers
docker compose up -d

# Wait 2-3 minutes for initialization
Start-Sleep -Seconds 120  # Windows
sleep 120                  # Linux/Mac

# Check services status
docker compose ps

# Expected: All services "Up" and healthy
```

### Step 7: Verify services

```bash
# Kafka
docker exec kafka kafka-topics --bootstrap-server localhost:9092 --list

# Cassandra
docker exec cassandra cqlsh -e "DESCRIBE KEYSPACES;"

# Elasticsearch
curl http://localhost:9200/_cluster/health

# Kibana
curl http://localhost:5601/api/status

# HDFS
curl http://localhost:9870
```

### Step 8: Recreate data (if needed)

```bash
# Cassandra schema
docker exec cassandra cqlsh < batch-layer/config/cassandra_schema.cql

# Kafka topic
docker exec kafka kafka-topics --bootstrap-server localhost:9092 \
  --create --topic lol_matches --partitions 3 --replication-factor 1

# Elasticsearch index
curl -X PUT "http://localhost:9200/lol_matches_stream" \
  -H "Content-Type: application/json" \
  -d @streaming-layer/config/es_mapping.json
```

### Step 9: Run pipeline

```bash
# Terminal 1: Data generator
python data-generator/src/generator.py --mode continuous

# Terminal 2: Spark streaming
.\submit_spark_job.ps1

# Terminal 3: Batch processing
python batch-layer/src/batch_consumer.py --batches 1
```

### Step 10: Train ML model

```bash
# Train model (500 samples)
python ml-layer/src/train_model.py

# Test predictions
python ml-layer/src/predict.py
```

---

## 🔧 Troubleshooting

### Issue 1: Images không load được

```bash
# Check file integrity
# File size phải ~10-12 GB

# Try load lại
docker load -i bigbig-stack-snapshot.tar

# Check error messages
```

### Issue 2: Docker compose không start

```bash
# Check image names trong docker-compose.yml
# Phải match với "bigbig-*:snapshot"

# Verify images exist
docker images | grep bigbig

# Check Docker Desktop memory settings
# Recommend: 16-32 GB RAM
```

### Issue 3: Services unhealthy

```bash
# Check logs
docker compose logs <service-name>

# Restart specific service
docker compose restart <service-name>

# Restart all
docker compose down
docker compose up -d
```

### Issue 4: Port conflicts

```bash
# Check ports in use
netstat -an | findstr "9092 9200 5601"  # Windows
netstat -tuln | grep -E "9092|9200|5601"  # Linux

# Stop conflicting services hoặc change ports trong docker-compose.yml
```

---

## 📊 Alternative: Export running containers

Nếu muốn export cả DATA (không chỉ images):

```bash
# Export container as image (includes data)
docker commit kafka bigbig-kafka-with-data:snapshot
docker commit cassandra bigbig-cassandra-with-data:snapshot
# ... for other containers

# Then save
docker save -o bigbig-stack-with-data.tar \
  bigbig-kafka-with-data:snapshot \
  bigbig-cassandra-with-data:snapshot \
  # ... other containers
```

**⚠️ Warning**: File này sẽ RẤT LỚN (~30-50 GB)

---

## 🎯 Quick Restore Checklist

- [ ] Copy bigbig-stack-snapshot.tar (~10-12 GB)
- [ ] `docker load -i bigbig-stack-snapshot.tar`
- [ ] Verify 11 images loaded
- [ ] Clone Git repo
- [ ] Update docker-compose.yml (use snapshot tags)
- [ ] `docker compose up -d`
- [ ] Wait 2-3 minutes
- [ ] Check `docker compose ps`
- [ ] Recreate schemas/topics
- [ ] Run pipeline
- [ ] Train ML model
- [ ] ✅ System restored!

---

## 💾 Storage Recommendations

### Local Backup
- External HDD/SSD (USB 3.0+)
- Network Attached Storage (NAS)
- Second internal drive

### Cloud Backup
- Google Drive (15 GB free - cần upgrade)
- OneDrive (5 GB free - cần upgrade)
- Dropbox (2 GB free - cần upgrade)
- AWS S3 / Azure Blob (pay per GB)

### Best Practice
- Keep 2 copies (local + cloud/external)
- Compress if uploading to cloud: `gzip bigbig-stack-snapshot.tar`
- Verify file integrity after transfer (check size)

---

## 📝 Notes

### What's included in snapshot
- ✅ Docker images (11 containers)
- ✅ Application binaries và dependencies
- ✅ Pre-configured services

### What's NOT included
- ❌ Data trong volumes (Kafka data, HDFS data, etc.)
- ❌ Checkpoints (Spark streaming)
- ❌ Logs
- ❌ ML models (.pkl files)

### Why data is not included
- Volumes are managed by Docker
- Data có thể regenerate nhanh (< 5 phút)
- File .tar sẽ quá lớn nếu include data

---

## 🚀 Performance Comparison

| Action | Time | Disk Space |
|--------|------|------------|
| Save images | 10-30 min | 10-12 GB |
| Load images | 5-15 min | 15-20 GB (after load) |
| Start containers | 2-3 min | +10 GB (volumes) |
| Regenerate data | 5-10 min | +5 GB |
| **Total restore** | **20-60 min** | **~30 GB** |

---

**Created**: 2026-01-13  
**Version**: 1.0  
**Compatible with**: Docker Desktop 4.x+, Docker Engine 20.x+
