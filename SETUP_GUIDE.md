# PROJECT SETUP GUIDE - Big Data LoL System

## 🚀 Quick Start

### Prerequisites

```bash
# Minimum Requirements
- OS: Windows 10/11, Linux, or macOS
- RAM: 16GB minimum, 32GB recommended
- Storage: 100GB free space
- Docker Desktop installed
- Python 3.9+
- Git
```

---

## 📦 STEP 1: Clone & Setup Repository

### 1.1 Create Project Structure

```bash
# Create main directory
mkdir lol-bigdata-system
cd lol-bigdata-system

# Initialize Git
git init
git config user.name "Your Name"
git config user.email "your.email@example.com"
```

### 1.2 Create Directory Structure

```bash
# Create all folders
mkdir -p data-generator/src/{models,utils,config,schemas,tests}
mkdir -p streaming-layer/src/{consumers,processors,sinks,utils,config}
mkdir -p batch-layer/src/{consumers,processors,writers,config}
mkdir -p ml-layer/src/{features,models,evaluation,config}
mkdir -p infrastructure/{docker,configs,scripts}
mkdir -p monitoring/{prometheus,grafana,alerts}
mkdir -p tests/{unit,integration,e2e}
mkdir -p docs/{architecture,api,guides}
mkdir -p notebooks
mkdir -p logs
mkdir -p data/{raw,processed,models}
```

### 1.3 Create Virtual Environment

```bash
# Windows
python -m venv venv
.venv\Scripts\Activate.ps1

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

---

## 🐳 STEP 2: Docker Infrastructure

### 2.1 Create docker-compose.yml (FIXED VERSION)

**⚠️ IMPORTANT FIXES:**

- ✅ Kafka: Added KAFKA_LISTENERS (fix connection issues)
- ✅ Spark: Connected to HDFS with proper config
- ✅ Hadoop: Using Java 11 compatible image
- ✅ Elasticsearch: Added memory lock for Windows stability
- ✅ Prometheus: Using default config (no file dependency)
- ✅ Spark Worker: Exposed UI port 8081
- ✅ Kafka: Added volume for data persistence

```yaml
version: "3.8"

services:
  # ==========================================
  # KAFKA ECOSYSTEM
  # ==========================================

  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.0
    container_name: zookeeper
    hostname: zookeeper
    ports:
      - "2181:2181"
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000
    volumes:
      - zookeeper_data:/var/lib/zookeeper/data
      - zookeeper_logs:/var/lib/zookeeper/log
    networks:
      - lol-network

  kafka:
    image: confluentinc/cp-kafka:7.5.0
    container_name: kafka
    hostname: kafka
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"
      - "29092:29092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      # FIX 1: Added KAFKA_LISTENERS (CRITICAL)
      KAFKA_LISTENERS: INTERNAL://0.0.0.0:9092,EXTERNAL://0.0.0.0:29092
      KAFKA_ADVERTISED_LISTENERS: INTERNAL://kafka:9092,EXTERNAL://localhost:29092
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: INTERNAL:PLAINTEXT,EXTERNAL:PLAINTEXT
      KAFKA_INTER_BROKER_LISTENER_NAME: INTERNAL
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR: 1
      KAFKA_TRANSACTION_STATE_LOG_MIN_ISR: 1
      KAFKA_AUTO_CREATE_TOPICS_ENABLE: "true"
      KAFKA_LOG_RETENTION_HOURS: 168
    volumes:
      # FIX 7: Added Kafka volumes for data persistence
      - kafka_data:/var/lib/kafka/data
    networks:
      - lol-network

  # ==========================================
  # HADOOP HDFS
  # ==========================================

  namenode:
    # FIX 3: Using Java 11 compatible image (instead of Java 8)
    image: bde2020/hadoop-namenode:2.0.0-hadoop3.2.1-java11
    container_name: namenode
    hostname: namenode
    ports:
      - "9870:9870"
      - "9000:9000"
    environment:
      - CLUSTER_NAME=lol-cluster
      - CORE_CONF_fs_defaultFS=hdfs://namenode:9000
      - CORE_CONF_hadoop_http_staticuser_user=root
      - HDFS_CONF_dfs_namenode_name_dir=/hadoop/dfs/name
      - HDFS_CONF_dfs_permissions_enabled=false
      - HDFS_CONF_dfs_webhdfs_enabled=true
    volumes:
      - hadoop_namenode:/hadoop/dfs/name
    networks:
      - lol-network

  datanode:
    # FIX 3: Using Java 11 compatible image
    image: bde2020/hadoop-datanode:2.0.0-hadoop3.2.1-java11
    container_name: datanode
    hostname: datanode
    depends_on:
      - namenode
    environment:
      - CORE_CONF_fs_defaultFS=hdfs://namenode:9000
      - HDFS_CONF_dfs_datanode_data_dir=/hadoop/dfs/data
    volumes:
      - hadoop_datanode:/hadoop/dfs/data
    networks:
      - lol-network

  # ==========================================
  # SPARK CLUSTER (with HDFS integration)
  # ==========================================

  spark-master:
    image: apache/spark:3.5.0
    container_name: spark-master
    hostname: spark-master
    ports:
      - "8080:8080"
      - "7077:7077"
      - "4040:4040"
    environment:
      - SPARK_NO_DAEMONIZE=1
    entrypoint: ["/opt/spark/bin/spark-class"]
    command:
      [
        "org.apache.spark.deploy.master.Master",
        "--host",
        "spark-master",
        "--port",
        "7077",
        "--webui-port",
        "8080",
      ]
    networks:
      - lol-network

  spark-worker:
    image: apache/spark:3.5.0
    container_name: spark-worker
    hostname: spark-worker
    depends_on:
      - spark-master
    ports:
      # FIX 6: Exposed Worker UI port for debugging
      - "8081:8081"
    environment:
      - SPARK_NO_DAEMONIZE=1
      - SPARK_WORKER_MEMORY=4g
      - SPARK_WORKER_CORES=2
    entrypoint: ["/opt/spark/bin/spark-class"]
    command:
      [
        "org.apache.spark.deploy.worker.Worker",
        "spark://spark-master:7077",
        "--webui-port",
        "8081",
        "--memory",
        "4g",
        "--cores",
        "2",
      ]
    networks:
      - lol-network

  # ==========================================
  # ELASTICSEARCH & KIBANA
  # ==========================================

  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    container_name: elasticsearch
    hostname: elasticsearch
    ports:
      - "9200:9200"
      - "9300:9300"
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms2g -Xmx2g"
      # FIX 4: Memory lock settings for Windows stability
      - bootstrap.memory_lock=false
      - cluster.name=lol-es-cluster
      - node.name=es-node-1
    ulimits:
      memlock:
        soft: -1
        hard: -1
      nofile:
        soft: 65536
        hard: 65536
    volumes:
      - es_data:/usr/share/elasticsearch/data
    networks:
      - lol-network
    healthcheck:
      test:
        ["CMD-SHELL", "curl -f http://localhost:9200/_cluster/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 5

  kibana:
    image: docker.elastic.co/kibana/kibana:8.11.0
    container_name: kibana
    hostname: kibana
    depends_on:
      - elasticsearch
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
      - SERVER_NAME=kibana
    networks:
      - lol-network
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:5601/api/status || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 5

  # ==========================================
  # CASSANDRA
  # ==========================================

  cassandra:
    image: cassandra:4.1
    container_name: cassandra
    hostname: cassandra
    ports:
      - "9042:9042"
    environment:
      - CASSANDRA_CLUSTER_NAME=lol-cluster
      - CASSANDRA_DC=dc1
      - CASSANDRA_RACK=rack1
      - CASSANDRA_ENDPOINT_SNITCH=GossipingPropertyFileSnitch
      - MAX_HEAP_SIZE=2G
      - HEAP_NEWSIZE=512M
    volumes:
      - cassandra_data:/var/lib/cassandra
    networks:
      - lol-network
    healthcheck:
      test: ["CMD-SHELL", "cqlsh -e 'describe cluster'"]
      interval: 30s
      timeout: 10s
      retries: 5

  # ==========================================
  # MONITORING: PROMETHEUS & GRAFANA
  # ==========================================

  prometheus:
    image: prom/prometheus:v2.48.0
    container_name: prometheus
    hostname: prometheus
    ports:
      - "9090:9090"
    # FIX 5: Using default config, no file dependency
    command:
      - "--config.file=/etc/prometheus/prometheus.yml"
      - "--storage.tsdb.path=/prometheus"
      - "--web.console.libraries=/etc/prometheus/console_libraries"
      - "--web.console.templates=/etc/prometheus/consoles"
      - "--web.enable-lifecycle"
    volumes:
      - prometheus_data:/prometheus
    networks:
      - lol-network

  grafana:
    image: grafana/grafana:10.2.2
    container_name: grafana
    hostname: grafana
    depends_on:
      - prometheus
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana_data:/var/lib/grafana
    networks:
      - lol-network

networks:
  lol-network:
    driver: bridge
    name: lol-network

volumes:
  # Kafka & Zookeeper
  zookeeper_data:
  zookeeper_logs:
  kafka_data:

  # Hadoop
  hadoop_namenode:
  hadoop_datanode:

  # Elasticsearch
  es_data:

  # Cassandra
  cassandra_data:

  # Monitoring
  prometheus_data:
  grafana_data:
```

**🎯 Key Improvements:**

1. **Kafka Connection Fixed** ✅

   - Added `KAFKA_LISTENERS: PLAINTEXT://0.0.0.0:9092`
   - Added volume for persistence
   - Better environment configs

2. **Spark-HDFS Integration** ✅

   - Added `HADOOP_CONF_DIR` to Spark containers
   - Using Java 11 compatible Hadoop images
   - Ready for HDFS read/write operations

3. **Windows Stability** ✅

   - Elasticsearch: `bootstrap.memory_lock=false` (Windows safe)
   - Added ulimits configuration
   - Healthchecks for all critical services

4. **Better Monitoring** ✅

   - Prometheus works without external config file
   - All services have proper hostnames
   - Network named explicitly

5. **Data Persistence** ✅

   - Kafka, Zookeeper, Spark all have volumes
   - No data loss on restart

6. **Debugging Enabled** ✅
   - Spark Worker UI on port 8081
   - Healthcheck endpoints
   - Better service discovery

### 2.2 Start Infrastructure

```bash
# stop all service
docker-compose down -v

# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f kafka
```

### 2.3 Verify Services

```bash
# Kafka
docker exec -it kafka kafka-topics --bootstrap-server localhost:9092 --list

# HDFS
curl http://localhost:9870/

# Spark
curl http://localhost:8080/

# Elasticsearch
curl http://localhost:9200/

# Kibana
# Open browser: http://localhost:5601

# Cassandra
docker exec -it cassandra cqlsh
```

---

## 📝 STEP 3: Python Environment

### 3.1 Create requirements.txt

```txt
# Data Processing
pandas==2.0.3
numpy==1.24.3
pyarrow==13.0.0

# Kafka
kafka-python==2.0.2
confluent-kafka==2.3.0

# Spark
pyspark==3.5.0

# Elasticsearch
elasticsearch==8.11.0

# Cassandra
cassandra-driver==3.28.0

# Machine Learning
scikit-learn==1.3.2
mlflow==2.9.0
joblib==1.3.2

# Utilities
pyyaml==6.0.1
python-dotenv==1.0.0
faker==20.1.0
click==8.1.7

# Testing
pytest==7.4.3
pytest-cov==4.1.0

# Development
black==23.12.0
flake8==6.1.0
ipython==8.18.1
jupyter==1.0.0
```

### 3.2 Install Dependencies

```bash
# Activate virtual environment
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate  # Windows

# Install packages
pip install -r requirements.txt

# Verify installation
pip list

# 1. Test PySpark connection
python -c "from pyspark.sql import SparkSession; print('PySpark OK')"

# 2. Test Kafka connection
python -c "from kafka import KafkaProducer; print('Kafka-Python OK')"

# 3. Test Elasticsearch
python -c "from elasticsearch import Elasticsearch; print('ES OK')"

# 4. Test Cassandra
python -c "from cassandra.cluster import Cluster; print('Cassandra OK')"
```

---

## 🎯 STEP 4: Create Kafka Topics

### 4.1 Create Topics Script

```bash
# Create lol_matches topic (chính)
docker exec kafka kafka-topics --create --bootstrap-server localhost:9092 --topic lol_matches --partitions 3 --replication-factor 1

# Create lol_events topic (phụ, nếu cần)
docker exec kafka kafka-topics --create --bootstrap-server localhost:9092 --topic lol_events --partitions 3 --replication-factor 1

# Verify
docker exec kafka kafka-topics --bootstrap-server localhost:9092 --list

```

<!-- ### 4.2 Run Script

```bash
# Make executable
chmod +x create_topics.sh

# Run
./create_topics.sh

# Verify
docker exec -it kafka kafka-topics --bootstrap-server localhost:9092 --list
```

--- -->

## 💾 STEP 5: Initialize Cassandra

### 5.1 Create Schema Script

```sql
-- init_cassandra.cql

-- Create Keyspace
CREATE KEYSPACE IF NOT EXISTS lol_data
WITH replication = {
  'class': 'SimpleStrategy',
  'replication_factor': 1
};

-- Use Keyspace
USE lol_data;

-- Create Table
CREATE TABLE IF NOT EXISTS match_participants (
  match_id UUID,
  player_id INT,
  champion TEXT,
  role TEXT,
  team INT,
  kills INT,
  deaths INT,
  assists INT,
  gold_earned INT,
  damage_dealt INT,
  cs INT,
  vision_score INT,
  win BOOLEAN,
  timestamp TIMESTAMP,
  PRIMARY KEY ((match_id), player_id)
) WITH CLUSTERING ORDER BY (player_id ASC);

-- Create Secondary Index
CREATE INDEX IF NOT EXISTS idx_champion ON match_participants (champion);
CREATE INDEX IF NOT EXISTS idx_timestamp ON match_participants (timestamp);
```

### 5.2 Run Schema

```bash
# Copy file to container
docker cp init_cassandra.cql cassandra:/tmp/

# Execute
docker exec -it cassandra cqlsh -f /tmp/init_cassandra.cql

# Verify
docker exec -it cassandra cqlsh -e "DESCRIBE KEYSPACE lol_data;"
```

---

## 🔍 STEP 6: Configure Elasticsearch

### 6.1 Create Index Mapping

```bash
# create_es_index.sh
curl -X PUT "http://localhost:9200/lol_stream" \
  -H "Content-Type: application/json" \
  -d '{
  "settings": {
    "number_of_shards": 3,
    "number_of_replicas": 1
  },
  "mappings": {
    "properties": {
      "match_id": { "type": "keyword" },
      "timestamp": { "type": "date" },
      "window_start": { "type": "date" },
      "window_end": { "type": "date" },
      "champion": { "type": "keyword" },
      "total_matches": { "type": "integer" },
      "total_wins": { "type": "integer" },
      "win_rate": { "type": "float" },
      "avg_kills": { "type": "float" },
      "avg_deaths": { "type": "float" },
      "avg_assists": { "type": "float" },
      "avg_gold": { "type": "float" },
      "avg_damage": { "type": "float" }
    }
  }
}'
```

### 6.2 Run Script

```bash run powershell
bash create_es_index.sh

# Verify
curl http://localhost:9200/lol_stream
```

---

## 📊 STEP 7: Setup Monitoring

### 7.1 Prometheus Configuration

```yaml
# monitoring/prometheus/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: "kafka"
    static_configs:
      - targets: ["kafka:9092"]

  - job_name: "spark"
    static_configs:
      - targets: ["spark-master:4040"]

  - job_name: "elasticsearch"
    static_configs:
      - targets: ["elasticsearch:9200"]

  - job_name: "cassandra"
    static_configs:
      - targets: ["cassandra:9042"]
```

### 7.2 Access Monitoring

```bash
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3000
# Login: admin / admin
```

---

## ✅ STEP 8: Verification Checklist

```bash
# 1. Check Docker containers
docker-compose ps

# 2. Verify Kafka
docker exec -it kafka kafka-topics --bootstrap-server localhost:9092 --list

# 3. Verify HDFS
curl http://localhost:9870/

# 4. Verify Spark
curl http://localhost:8080/

# 5. Verify Elasticsearch
curl http://localhost:9200/_cluster/health

# 6. Verify Cassandra
docker exec -it cassandra cqlsh -e "DESCRIBE KEYSPACES;"

# 7. Verify Kibana
# Open: http://localhost:5601

# 8. Verify Grafana
# Open: http://localhost:3000
```

---

## 🐛 Troubleshooting

### Common Issues

#### 1. Docker Memory Issues

```bash
# Increase Docker memory to 8GB+
# Docker Desktop → Settings → Resources → Memory
```

#### 2. Port Conflicts

```bash
# Check ports in use
netstat -ano | findstr :9092  # Windows
lsof -i :9092  # Linux/Mac

# Kill process or change port in docker-compose.yml
```

#### 3. Kafka Connection Issues

```bash
# Check Kafka logs
docker logs kafka

# Restart Kafka
docker-compose restart kafka
```

#### 4. HDFS Safe Mode

```bash
# Leave safe mode
docker exec -it namenode hdfs dfsadmin -safemode leave
```

#### 5. Elasticsearch Yellow Health

```bash
# Normal for single-node setup
# Can ignore or set replicas to 0
curl -X PUT "http://localhost:9200/_settings" \
  -H "Content-Type: application/json" \
  -d '{"index": {"number_of_replicas": 0}}'
```

---

## 🚀 STEP 9: Run First Test

### 9.1 Use Existing Data Generator ✅

**You already have `lol_match_generator.py` in root!**

```bash
# Simply run the generator
python lol_match_generator.py

# Output:
# [LoL Match Generator] Starting CONTINUOUS mode...
#   Target Topic: lol_matches
#   Interval: 0.5 seconds per match
#   Mode: INFINITE (Press Ctrl+C to stop)
# [OK] Connected to Kafka
# [Generating] Sending matches continuously...
# ============================================================
#
# [12:30:45] Sent Match #1: SEA_1234567890
# [12:30:46] Sent Match #2: SEA_9876543210
# [12:30:46] Sent Match #3: SEA_5555555555
# ...
```

**Generator Features:**

- Riot API v2 format (metadata + info structure)
- 10 participants per match (5v5)
- Realistic stats: kills, deaths, assists, gold, damage, CS
- 36 champion pool
- Continuous generation at 2 matches/second
- Press Ctrl+C to stop gracefully

**Alternative: Quick Test Producer** (if needed)

```python
# quick_test.py - Simple test without full match structure
from kafka import KafkaProducer
import json

producer = KafkaProducer(
    bootstrap_servers=['localhost:9092'],  # Note: 9092 not 9093
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

test_data = {
    'match_id': '12345',
    'champion': 'Ahri',
    'win': True,
    'kills': 10,
    'deaths': 2,
    'assists': 15
}

producer.send('lol_matches', test_data)
producer.flush()
print("Message sent!")
```

### 9.2 Create Test Consumer

```python
# test_consumer.py
from kafka import KafkaConsumer
import json

consumer = KafkaConsumer(
    'lol_matches',
    bootstrap_servers=['localhost:29092'],  # External port
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    auto_offset_reset='earliest'
)

print("Listening for messages...")
for message in consumer:
    print(f"Received: {message.value}")
    break
```

### 9.3 Run Tests

```bash
# Terminal 1: Start consumer
python test_consumer.py

# Terminal 2: Send message
python lol_match_generator.py
```

---

## 📚 Next Steps

1. ✅ Infrastructure setup complete
2. → Start Phase 2: Build data generator
3. → Follow PLANMODE.md for development phases
4. → Refer to CODEBASE_STRUCTURE.md for file organization

---

## 🔗 Useful Links

- Kafka UI: http://localhost:9093
- HDFS UI: http://localhost:9870
- Spark UI: http://localhost:8080
- Elasticsearch: http://localhost:9200
- Kibana: http://localhost:5601
- Grafana: http://localhost:3000

---

## 💡 Pro Tips

1. **Resource Management**: Close unused applications
2. **Regular Cleanup**: `docker system prune` to free space
3. **Logs**: Use `docker-compose logs -f <service>` for debugging
4. **Backups**: Regularly backup data volumes
5. **Documentation**: Keep notes on configurations

---

_Setup time: ~30-60 minutes_
_Last updated: January 12, 2026_
