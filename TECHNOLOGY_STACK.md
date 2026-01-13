# TECHNOLOGY STACK - Big Data LoL System

## 📊 Tổng quan Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    LAMBDA ARCHITECTURE                           │
│                                                                  │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐ │
│  │ Speed Layer  │      │ Serving Layer│      │ Batch Layer  │ │
│  │ (Real-time)  │─────→│  (Query)     │←─────│ (Historical) │ │
│  └──────────────┘      └──────────────┘      └──────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 CORE TECHNOLOGIES

### 1. Data Ingestion Layer

#### Apache Kafka 3.6+

**Vai trò**: Message Broker - Real-time streaming platform
**Đặc điểm**:

- Distributed, fault-tolerant
- High throughput (millions msgs/sec)
- Persistent message storage
- Horizontal scalability

**Configuration**:

```yaml
Brokers: 3 nodes
Partitions: 3 per topic
Replication Factor: 2
Retention: 7 days
```

**Python Client** (Currently Implemented):

```python
# lol_match_generator.py implementation
from kafka import KafkaProducer
import json

producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Generate và send match data
match_data = generate_match()  # Riot API format
producer.send('lol_matches', match_data)
producer.flush()
```

**Data Generator Details**:

- ✅ Standalone script: `lol_match_generator.py`
- ✅ Format: Riot API v2 compatible
- ✅ Generation rate: 2 matches/second (configurable)
- ✅ Mode: Continuous (infinite loop)
- ✅ Replaces: Web crawling from op.gg
- ✅ Benefits: No rate limits, consistent format, faster testing

**Alternatives considered**:

- RabbitMQ (lower throughput)
- AWS Kinesis (cloud-only)
- Apache Pulsar (more complex)

---

### 2. Speed Layer (Real-time Processing)

#### Apache Spark Streaming 3.4+

**Vai trò**: Real-time stream processing engine
**Đặc điểm**:

- Micro-batch processing (30s intervals)
- Exactly-once semantics
- Fault-tolerant với checkpointing
- Rich API (Python, Scala, Java)

**Configuration**:

```python
# Spark Streaming setup
spark = SparkSession.builder \
    .appName("LoLStreamingProcessor") \
    .config("spark.streaming.kafka.maxRatePerPartition", "1000") \
    .config("spark.sql.streaming.checkpointLocation", "/checkpoints") \
    .getOrCreate()
```

**Processing Pattern**:

- Window operations: 5 minutes tumbling window
- Watermarking: 10 minutes late data tolerance
- State management: In-memory with periodic checkpointing

**Alternatives**:

- Apache Flink (true streaming, more complex)
- Apache Storm (older, less active)
- Kafka Streams (Java-only)

---

#### Elasticsearch 8.11+

**Vai trò**: Search engine & Real-time indexing
**Đặc điểm**:

- Full-text search
- Near real-time indexing
- Aggregations & analytics
- Horizontal scaling

**Index Mapping**:

```json
{
  "mappings": {
    "properties": {
      "match_id": { "type": "keyword" },
      "timestamp": { "type": "date" },
      "champion": { "type": "keyword" },
      "win_rate": { "type": "float" },
      "stats": {
        "properties": {
          "kills": { "type": "integer" },
          "deaths": { "type": "integer" },
          "assists": { "type": "integer" }
        }
      }
    }
  }
}
```

**Python Client**:

```python
from elasticsearch import Elasticsearch
es = Elasticsearch(['http://localhost:9200'])
```

---

#### Kibana 8.11+

**Vai trò**: Visualization & Dashboard
**Đặc điểm**:

- Pre-built visualizations
- Custom dashboards
- Real-time monitoring
- Alert integration

**Dashboard Components**:

- Line charts: Win rate over time
- Bar charts: Champion pick rates
- Heat maps: Performance by time of day
- Data tables: Recent matches

---

### 3. Batch Layer (Historical Processing)

#### Hadoop HDFS 3.3+

**Vai trò**: Distributed File System - Data Lake
**Đặc điểm**:

- Fault-tolerant storage
- High throughput
- Commodity hardware
- Petabyte-scale

**Directory Structure**:

```
/data/lol_matches/
├── 2026/
│   ├── 01/
│   │   ├── 12/
│   │   │   ├── batch_000001.parquet
│   │   │   └── batch_000002.parquet
│   │   └── 13/
│   └── 02/
```

**Configuration**:

```xml
<configuration>
  <property>
    <name>dfs.replication</name>
    <value>3</value>
  </property>
  <property>
    <name>dfs.blocksize</name>
    <value>134217728</value> <!-- 128MB -->
  </property>
</configuration>
```

---

#### Apache Spark (Batch Mode) 3.4+

**Vai trò**: Large-scale batch processing
**Đặc điểm**:

- DataFrame API
- SQL support
- In-memory computing
- Lazy evaluation

**ETL Pipeline**:

```python
# Read from HDFS
df = spark.read.parquet("/data/lol_matches/2026/01/12/")

# Transform
transformed = df \
    .select("match_id", "participants") \
    .withColumn("player", explode("participants")) \
    .select("match_id", "player.*")

# Write to Cassandra
transformed.write \
    .format("org.apache.spark.sql.cassandra") \
    .options(table="match_participants", keyspace="lol_data") \
    .save()
```

**Optimization**:

- Partitioning: By date
- File format: Parquet (columnar)
- Compression: Snappy
- Broadcast joins: For small lookup tables

---

#### Apache Cassandra 4.1+

**Vai trò**: NoSQL Database - Batch serving layer
**Đặc điểm**:

- Wide-column store
- Linear scalability
- High write throughput
- Tunable consistency

**Data Model**:

```sql
CREATE KEYSPACE lol_data WITH replication = {
  'class': 'SimpleStrategy',
  'replication_factor': 3
};

CREATE TABLE match_participants (
  match_id UUID,
  player_id INT,
  champion TEXT,
  role TEXT,
  stats MAP<TEXT, INT>,
  win BOOLEAN,
  timestamp TIMESTAMP,
  PRIMARY KEY ((match_id), player_id)
) WITH CLUSTERING ORDER BY (player_id ASC);
```

**Partition Strategy**:

- Partition key: `match_id` (even distribution)
- Clustering key: `player_id` (sorted within partition)
- Secondary index: `champion` (for queries)

**Python Driver**:

```python
from cassandra.cluster import Cluster
cluster = Cluster(['localhost'])
session = cluster.connect('lol_data')
```

---

### 4. Machine Learning Layer

#### Scikit-learn 1.3+

**Vai trò**: Machine Learning framework
**Algorithm**: Random Forest Classifier

**Feature Engineering**:

```python
features = [
    'champion_id',
    'avg_kills',
    'avg_deaths',
    'avg_assists',
    'gold_per_min',
    'damage_per_min',
    'cs_per_min',
    'vision_score',
    'role_encoded'
]

target = 'win'
```

**Model Training**:

```python
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

rf_model = RandomForestClassifier(
    n_estimators=100,
    max_depth=10,
    min_samples_split=5,
    random_state=42
)

rf_model.fit(X_train, y_train)
```

**Model Evaluation**:

- Accuracy
- Precision, Recall, F1
- ROC-AUC
- Feature importance

---

#### MLflow 2.9+ (Optional)

**Vai trò**: ML lifecycle management
**Features**:

- Experiment tracking
- Model registry
- Model versioning
- Deployment tracking

**Usage**:

```python
import mlflow
import mlflow.sklearn

with mlflow.start_run():
    mlflow.log_params(model_params)
    mlflow.log_metrics({"accuracy": accuracy})
    mlflow.sklearn.log_model(rf_model, "model")
```

---

### 5. Supporting Technologies

#### Python 3.9+

**Libraries**:

```
# Data Processing
pandas==2.0.3
numpy==1.24.3
pyarrow==13.0.0

# Kafka
kafka-python==2.0.2
confluent-kafka==2.3.0

# Spark
pyspark==3.4.1

# Elasticsearch
elasticsearch==8.11.0

# Cassandra
cassandra-driver==3.28.0

# ML
scikit-learn==1.3.2
mlflow==2.9.0

# Utilities
pyyaml==6.0.1
python-dotenv==1.0.0
faker==20.1.0
```

---

#### Docker & Docker Compose

**Vai trò**: Containerization & Orchestration

**Services Configuration**:

```yaml
version: "3.8"
services:
  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.0

  kafka:
    image: confluentinc/cp-kafka:7.5.0
    depends_on:
      - zookeeper

  namenode:
    image: bde2020/hadoop-namenode:2.0.0-hadoop3.2.1-java8

  datanode:
    image: bde2020/hadoop-datanode:2.0.0-hadoop3.2.1-java8

  spark-master:
    image: bitnami/spark:3.4.1

  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0

  kibana:
    image: docker.elastic.co/kibana/kibana:8.11.0

  cassandra:
    image: cassandra:4.1
```

---

#### Prometheus & Grafana

**Vai trò**: Monitoring & Alerting

**Metrics Collection**:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: "kafka"
    static_configs:
      - targets: ["kafka:9090"]

  - job_name: "spark"
    static_configs:
      - targets: ["spark-master:4040"]

  - job_name: "elasticsearch"
    static_configs:
      - targets: ["elasticsearch:9200"]
```

**Grafana Dashboards**:

- Kafka: Throughput, lag, partition metrics
- Spark: Job execution, memory usage
- Elasticsearch: Indexing rate, query latency
- Cassandra: Write throughput, read latency

---

## 📊 TECHNOLOGY COMPARISON

### Why Lambda Architecture?

| Architecture | Pros                   | Cons                       | Use Case            |
| ------------ | ---------------------- | -------------------------- | ------------------- |
| **Lambda**   | Both real-time + batch | Complex, dual pipeline     | Our choice          |
| Kappa        | Simpler, stream-only   | No historical reprocessing | Real-time only apps |
| Batch-only   | Simple, reliable       | High latency               | Legacy systems      |

---

### Kafka vs Others

| Feature     | Kafka      | RabbitMQ | AWS Kinesis |
| ----------- | ---------- | -------- | ----------- |
| Throughput  | ⭐⭐⭐⭐⭐ | ⭐⭐⭐   | ⭐⭐⭐⭐    |
| Persistence | ⭐⭐⭐⭐⭐ | ⭐⭐     | ⭐⭐⭐⭐    |
| Scalability | ⭐⭐⭐⭐⭐ | ⭐⭐⭐   | ⭐⭐⭐⭐⭐  |
| Complexity  | ⭐⭐⭐     | ⭐⭐     | ⭐          |
| Cost        | Free       | Free     | $$          |

---

### Spark vs Flink

| Aspect         | Spark Streaming | Apache Flink   |
| -------------- | --------------- | -------------- |
| Processing     | Micro-batch     | True streaming |
| Latency        | Seconds         | Milliseconds   |
| State          | Limited         | Rich state     |
| Maturity       | ⭐⭐⭐⭐⭐      | ⭐⭐⭐⭐       |
| Learning Curve | Easier          | Steeper        |
| Our Choice     | ✅              | -              |

---

## 🚀 SCALABILITY CONSIDERATIONS

### Horizontal Scaling

#### Kafka

- Add brokers: Linear throughput increase
- Add partitions: More parallelism
- Consumer groups: Scale consumers

#### Spark

- Add worker nodes: More processing power
- Increase executors: More tasks in parallel
- Dynamic allocation: Auto-scaling

#### Elasticsearch

- Add data nodes: More storage & indexing
- Sharding: Distribute data
- Replicas: Fault tolerance

#### Cassandra

- Add nodes: Linear capacity increase
- Virtual nodes: Even distribution
- Multi-datacenter: Geographic distribution

---

### Performance Benchmarks (Expected)

| Component       | Metric     | Target         | Notes                   |
| --------------- | ---------- | -------------- | ----------------------- |
| Kafka           | Throughput | 10k msgs/sec   | 3 brokers, 3 partitions |
| Spark Streaming | Latency    | < 60s          | 30s micro-batch         |
| Elasticsearch   | Indexing   | 5k docs/sec    | 3 nodes, 2 replicas     |
| Cassandra       | Writes     | 10k writes/sec | 3 nodes, RF=3           |
| ML Prediction   | Latency    | < 100ms        | Single prediction       |

---

## 🔒 SECURITY CONSIDERATIONS

### Kafka

- SASL authentication
- SSL/TLS encryption
- ACLs for topics

### Elasticsearch

- Basic authentication
- HTTPS
- Role-based access

### Cassandra

- Authentication enabled
- Encryption at rest
- Network encryption

---

## 📚 LEARNING RESOURCES

### Official Docs

- Kafka: https://kafka.apache.org/documentation/
- Spark: https://spark.apache.org/docs/latest/
- Elasticsearch: https://www.elastic.co/guide/
- Cassandra: https://cassandra.apache.org/doc/

### Tutorials

- Kafka Python: https://kafka-python.readthedocs.io/
- PySpark Tutorial: https://sparkbyexamples.com/
- ES Python Client: https://elasticsearch-py.readthedocs.io/

### Books

- "Designing Data-Intensive Applications" - Martin Kleppmann
- "Learning Spark" - O'Reilly
- "Kafka: The Definitive Guide" - O'Reilly

---

## 🎯 DECISION RATIONALE

### Why This Stack?

1. **Industry Standard**: All technologies widely adopted
2. **Open Source**: No licensing costs
3. **Python-First**: Unified language across layers
4. **Scalable**: Proven at scale (LinkedIn, Netflix, Uber)
5. **Community**: Large community support
6. **Learning Value**: Highly marketable skills

### Trade-offs Made

✅ **Accepted**:

- Complexity: Lambda architecture có 2 pipelines
- Resource-heavy: Cần nhiều RAM/CPU
- Learning curve: Nhiều technologies

❌ **Avoided**:

- Vendor lock-in: No cloud-specific services
- Cost: All open-source
- Over-engineering: Start simple, scale as needed

---

_Last updated: January 12, 2026_
_Version: 1.0_
