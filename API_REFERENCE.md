# API REFERENCE - Big Data LoL System

## 🌐 Overview

Tài liệu này mô tả các API và interfaces chính của hệ thống.

---

## 📦 1. Data Generator API

### Script: `lol_match_generator.py` (Current Implementation)

#### Current Usage (Standalone Script)

```python
# Run directly (no class instantiation needed)
python lol_match_generator.py

# Or import functions:
from lol_match_generator import generate_match, generate_participant

# Generate a single match
match_data = generate_match()
print(match_data)
```

#### Configuration (In-file constants)

```python
# Edit these in lol_match_generator.py:
BOOTSTRAP_SERVERS = 'localhost:9092'  # Kafka server
TOPIC_NAME = 'lol_matches'            # Kafka topic
INTERVAL_SECONDS = 0.5                 # 2 matches/second
```

#### Future Class-based API (Planned)

```python
# After refactoring:
from data_generator.lol_match_generator import LoLMatchGenerator

generator = LoLMatchGenerator(
    kafka_bootstrap_servers='localhost:9092',
    topic='lol_matches',
    match_rate=120  # matches per minute (2/second)
)
```

#### Methods

##### `generate_match() -> dict`

Generate a single match with all participants.

**Returns:**

```json
{
  "match_id": "uuid-string",
  "timestamp": "2026-01-12T10:30:00Z",
  "duration": 1800,
  "game_mode": "ranked",
  "participants": [
    {
      "player_id": 12345,
      "champion": "Ahri",
      "role": "mid",
      "team": 100,
      "stats": {
        "kills": 10,
        "deaths": 2,
        "assists": 15,
        "gold_earned": 15000,
        "damage_dealt": 25000,
        "cs": 180,
        "vision_score": 25
      },
      "win": true
    }
  ]
}
```

##### `start() -> None`

Start continuous match generation.

##### `stop() -> None`

Stop match generation gracefully.

---

## ⚡ 2. Streaming Layer API

### Class: `SparkStreamingProcessor`

#### Initialization

```python
from streaming_layer.spark_streaming_app import SparkStreamingProcessor

processor = SparkStreamingProcessor(
    kafka_servers='kafka:9092',
    kafka_topic='lol_matches',
    es_host='elasticsearch',
    es_port=9200,
    es_index='lol_stream',
    batch_interval=30,  # seconds
    window_duration=300  # 5 minutes
)
```

#### Methods

##### `process_stream() -> None`

Start processing Kafka stream with windowing and aggregations.

**Processing Steps:**

1. Read from Kafka
2. Parse JSON
3. Apply 5-minute tumbling window
4. Calculate aggregations per champion
5. Write to Elasticsearch

##### `calculate_win_rate(df: DataFrame) -> DataFrame`

Calculate win rate statistics.

**Input Schema:**

```python
{
  "champion": StringType(),
  "win": BooleanType(),
  "kills": IntegerType(),
  "deaths": IntegerType(),
  "assists": IntegerType()
}
```

**Output Schema:**

```python
{
  "champion": StringType(),
  "window_start": TimestampType(),
  "window_end": TimestampType(),
  "total_matches": IntegerType(),
  "total_wins": IntegerType(),
  "win_rate": FloatType(),
  "avg_kills": FloatType(),
  "avg_deaths": FloatType(),
  "avg_assists": FloatType()
}
```

---

## 💾 3. Batch Layer API

### Class: `BatchConsumer`

#### Initialization

```python
from batch_layer.batch_consumer import BatchConsumer

consumer = BatchConsumer(
    kafka_servers='kafka:9092',
    kafka_topic='lol_matches',
    hdfs_path='/data/lol_matches',
    batch_size=50
)
```

#### Methods

##### `consume_batch() -> List[dict]`

Consume batch of messages from Kafka.

##### `write_to_hdfs(data: List[dict]) -> str`

Write batch to HDFS with date partitioning.

**File Path Pattern:**

```
/data/lol_matches/YYYY/MM/DD/batch_XXXXXX.parquet
```

---

### Class: `PySparkProcessor`

#### Initialization

```python
from batch_layer.pyspark_processor import PySparkProcessor

processor = PySparkProcessor(
    hdfs_input='/data/lol_matches',
    cassandra_host='cassandra',
    cassandra_keyspace='lol_data',
    cassandra_table='match_participants'
)
```

#### Methods

##### `process_batch(date: str) -> None`

Process batch data for a specific date.

**Steps:**

1. Read Parquet from HDFS
2. Flatten nested JSON
3. Feature engineering
4. Data quality checks
5. Write to Cassandra

##### `flatten_participants(df: DataFrame) -> DataFrame`

Flatten match data to participant level.

---

## 🤖 4. Machine Learning API

### Class: `FeatureEngineer`

#### Methods

##### `extract_features(date_range: tuple) -> DataFrame`

Extract features from Cassandra for ML training.

**Features:**

```python
[
  'champion_id',
  'role_encoded',
  'avg_kills_last_10',
  'avg_deaths_last_10',
  'avg_assists_last_10',
  'win_rate_last_20',
  'gold_per_min',
  'damage_per_min',
  'cs_per_min',
  'vision_score',
  'kda_ratio'
]
```

##### `create_training_dataset() -> tuple`

Create X_train, X_test, y_train, y_test.

---

### Class: `RandomForestModel`

#### Initialization

```python
from ml_layer.model_training import RandomForestModel

model = RandomForestModel(
    n_estimators=100,
    max_depth=10,
    random_state=42
)
```

#### Methods

##### `train(X_train, y_train) -> None`

Train the Random Forest model.

##### `predict(X_test) -> np.array`

Make predictions.

##### `evaluate(X_test, y_test) -> dict`

Evaluate model performance.

**Returns:**

```json
{
  "accuracy": 0.78,
  "precision": 0.76,
  "recall": 0.8,
  "f1_score": 0.78,
  "roc_auc": 0.82
}
```

##### `get_feature_importance() -> dict`

Get feature importance scores.

##### `save_model(path: str) -> None`

Save model to disk.

##### `load_model(path: str) -> None`

Load model from disk.

---

## 🔍 5. Query APIs

### Elasticsearch Queries

#### Get Recent Matches

```python
from elasticsearch import Elasticsearch

es = Elasticsearch(['http://localhost:9200'])

# Query last 1 hour of data
query = {
  "query": {
    "range": {
      "timestamp": {
        "gte": "now-1h"
      }
    }
  },
  "sort": [
    {"timestamp": {"order": "desc"}}
  ],
  "size": 100
}

results = es.search(index='lol_stream', body=query)
```

#### Champion Win Rate Aggregation

```python
query = {
  "size": 0,
  "aggs": {
    "champions": {
      "terms": {
        "field": "champion",
        "size": 50
      },
      "aggs": {
        "avg_win_rate": {
          "avg": {
            "field": "win_rate"
          }
        }
      }
    }
  }
}

results = es.search(index='lol_stream', body=query)
```

---

### Cassandra Queries

#### Get Player Match History

```python
from cassandra.cluster import Cluster

cluster = Cluster(['localhost'])
session = cluster.connect('lol_data')

query = """
SELECT * FROM match_participants
WHERE match_id = ?
"""

prepared = session.prepare(query)
results = session.execute(prepared, [match_id])
```

#### Champion Statistics

```python
query = """
SELECT champion, AVG(kills) as avg_kills, AVG(deaths) as avg_deaths
FROM match_participants
WHERE timestamp > ? AND timestamp < ?
ALLOW FILTERING
"""

results = session.execute(query, [start_date, end_date])
```

---

## 📊 6. Monitoring API

### Prometheus Metrics

#### Custom Metrics

```python
from prometheus_client import Counter, Histogram, Gauge

# Kafka metrics
kafka_messages_produced = Counter(
    'kafka_messages_produced_total',
    'Total messages produced to Kafka'
)

# Processing metrics
processing_latency = Histogram(
    'processing_latency_seconds',
    'Processing latency in seconds'
)

# System metrics
active_consumers = Gauge(
    'active_consumers',
    'Number of active Kafka consumers'
)
```

#### Export Metrics

```python
from prometheus_client import start_http_server

# Start metrics server
start_http_server(8000)

# Increment counter
kafka_messages_produced.inc()

# Record histogram
with processing_latency.time():
    process_data()

# Set gauge
active_consumers.set(5)
```

---

## 🔒 7. Configuration API

### Environment Variables

```bash
# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9093
KAFKA_TOPIC_MATCHES=lol_matches

# HDFS
HDFS_NAMENODE=hdfs://namenode:9000
HDFS_DATA_PATH=/data/lol_matches

# Elasticsearch
ES_HOST=localhost
ES_PORT=9200
ES_INDEX=lol_stream

# Cassandra
CASSANDRA_HOST=localhost
CASSANDRA_PORT=9042
CASSANDRA_KEYSPACE=lol_data

# Spark
SPARK_MASTER=spark://spark-master:7077
SPARK_APP_NAME=LoLProcessor

# ML
ML_MODEL_PATH=/data/models
ML_BATCH_SIZE=1000
```

### Config File (YAML)

```yaml
# config/app_config.yaml
kafka:
  bootstrap_servers: "localhost:9093"
  topics:
    matches: "lol_matches"
    events: "lol_events"
  consumer_group: "lol_consumers"

spark:
  app_name: "LoLStreamProcessor"
  master: "spark://spark-master:7077"
  streaming:
    batch_interval: 30
    checkpoint_dir: "/checkpoints"

elasticsearch:
  hosts: ["http://localhost:9200"]
  index: "lol_stream"
  batch_size: 1000

cassandra:
  contact_points: ["localhost"]
  keyspace: "lol_data"
  table: "match_participants"

ml:
  model_path: "/data/models"
  feature_columns:
    - "champion_id"
    - "avg_kills"
    - "avg_deaths"
  target_column: "win"
```

---

## 🧪 8. Testing Utilities

### Mock Data Generator

```python
from tests.utils import MockDataGenerator

# Generate mock match
mock_gen = MockDataGenerator()
match = mock_gen.generate_match(
    num_participants=10,
    win_team=100
)
```

### Test Fixtures

```python
import pytest
from kafka import KafkaProducer

@pytest.fixture
def kafka_producer():
    producer = KafkaProducer(
        bootstrap_servers=['localhost:9093']
    )
    yield producer
    producer.close()

@pytest.fixture
def sample_match():
    return {
        'match_id': 'test-123',
        'champion': 'Ahri',
        'win': True
    }
```

---

## 📝 Usage Examples

### End-to-End Example

```python
# 1. Start Data Generator
from data_generator.lol_match_generator import LoLMatchGenerator

generator = LoLMatchGenerator(
    kafka_bootstrap_servers='localhost:9093',
    topic='lol_matches',
    match_rate=10
)
generator.start()

# 2. Start Streaming Processor
from streaming_layer.spark_streaming_app import SparkStreamingProcessor

stream_processor = SparkStreamingProcessor(
    kafka_servers='kafka:9092',
    kafka_topic='lol_matches',
    es_host='elasticsearch',
    es_port=9200
)
stream_processor.process_stream()

# 3. Start Batch Consumer
from batch_layer.batch_consumer import BatchConsumer

batch_consumer = BatchConsumer(
    kafka_servers='kafka:9092',
    kafka_topic='lol_matches',
    hdfs_path='/data/lol_matches'
)
batch_consumer.start()

# 4. Query Results
from elasticsearch import Elasticsearch

es = Elasticsearch(['http://localhost:9200'])
results = es.search(
    index='lol_stream',
    body={
        "query": {"match_all": {}},
        "size": 10
    }
)
print(results['hits']['hits'])
```

---

## 🔗 API Endpoints (Future FastAPI Implementation)

### Planned REST API

```python
# GET /health
# Health check endpoint
{
  "status": "healthy",
  "timestamp": "2026-01-12T10:30:00Z",
  "services": {
    "kafka": "up",
    "elasticsearch": "up",
    "cassandra": "up"
  }
}

# GET /api/v1/champions/{champion_name}/stats
# Get champion statistics
{
  "champion": "Ahri",
  "total_matches": 1000,
  "win_rate": 0.52,
  "avg_kills": 8.5,
  "avg_deaths": 5.2,
  "avg_assists": 12.3
}

# POST /api/v1/predict
# Predict match outcome
# Request:
{
  "champion": "Ahri",
  "role": "mid",
  "features": {
    "avg_kills": 8,
    "avg_deaths": 5,
    "gold_per_min": 400
  }
}
# Response:
{
  "win_probability": 0.68,
  "confidence": 0.85
}

# GET /api/v1/matches/recent
# Get recent matches
{
  "matches": [...],
  "total": 100,
  "page": 1
}
```

---

## 📚 Additional Resources

- Kafka Python Docs: https://kafka-python.readthedocs.io/
- PySpark API: https://spark.apache.org/docs/latest/api/python/
- Elasticsearch Python: https://elasticsearch-py.readthedocs.io/
- Cassandra Driver: https://docs.datastax.com/en/developer/python-driver/

---

_Last updated: January 12, 2026_
_Version: 1.0_
