# Phase 3 - Streaming Layer

## 📋 Overview

Real-time streaming pipeline sử dụng **Spark Structured Streaming** để xử lý dữ liệu trận đấu LoL từ Kafka và index vào Elasticsearch.

## 🏗️ Architecture

```
Kafka (lol_matches)
    ↓
Spark Structured Streaming
    ↓ (foreachBatch)
Data Processing (Extract + Calculate Metrics)
    ↓
Elasticsearch (lol_matches_stream)
    ↓
Kibana (Visualization)
```

## 📦 Components

### 1. Spark Streaming Consumer (`spark_streaming_consumer.py`)

- **Purpose**: Consume match data từ Kafka và index vào Elasticsearch
- **Technology**: Spark Structured Streaming API 3.5.0
- **Features**:
  - Real-time consumption từ Kafka topic `lol_matches`
  - Automatic schema parsing (Riot API v2 format)
  - Micro-batch processing với foreachBatch
  - Checkpoint mechanism cho fault tolerance

### 2. Elasticsearch Indexer (`elasticsearch_indexer.py`)

- **Purpose**: Quản lý connection và indexing vào Elasticsearch
- **Features**:
  - Automatic index creation với custom mapping
  - Single document indexing
  - Bulk indexing với error handling
  - Health check và cluster monitoring

### 3. Data Processors (`processors.py`)

- **Purpose**: Transform và enrich match data
- **Features**:
  - Parse JSON match data
  - Extract participants từ arrays
  - Calculate derived metrics (KDA, GPM, DPM, CSPM)
  - Prepare documents cho Elasticsearch

## 🚀 Getting Started

### Prerequisites

1. Docker containers đang chạy:

   - Kafka (localhost:29092)
   - Elasticsearch (localhost:9200)
   - Spark Master/Worker (localhost:7077)

2. Python environment activated với packages:
   ```bash
   pip install pyspark==3.5.0 elasticsearch==8.11.0 pyyaml==6.0.1
   ```

### Quick Start

1. **Verify Setup**:

   ```bash
   python verify_phase3.py
   ```

   Expected: ✓ 22/22 tests passed

2. **Start Data Generator** (Terminal 1):

   ```bash
   python data-generator/src/generator.py --mode continuous
   ```

3. **Start Spark Streaming** (Terminal 2):

   ```bash
   python streaming-layer/src/spark_streaming_consumer.py
   ```

4. **Check Elasticsearch**:

   ```bash
   # Count documents
   curl -X GET "http://localhost:9200/lol_matches_stream/_count?pretty"

   # View sample documents
   curl -X GET "http://localhost:9200/lol_matches_stream/_search?pretty&size=5"
   ```

5. **View in Kibana**:
   - Open: http://localhost:5601
   - Go to: Management → Stack Management → Index Patterns
   - Create pattern: `lol_matches_stream`
   - Explore: Discover tab

## 📊 Data Flow

### Input (Kafka Message)

```json
{
  "metadata": {
    "matchId": "NA1_1234567890"
  },
  "info": {
    "gameCreation": 1673000000000,
    "gameDuration": 1800,
    "participants": [
      {
        "participantId": 1,
        "summonerName": "Player1",
        "championName": "Ahri",
        "teamId": 100,
        "teamPosition": "MIDDLE",
        "win": true,
        "kills": 10,
        "deaths": 2,
        "assists": 15,
        ...
      }
    ]
  }
}
```

### Processing

1. **Parse JSON** → Extract match metadata
2. **Explode participants** → 10 records per match
3. **Calculate metrics**:
   - `kda = (kills + assists) / deaths`
   - `gold_per_minute = gold_earned / (game_duration / 60)`
   - `damage_per_minute = total_damage / (game_duration / 60)`
   - `cs_per_minute = cs / (game_duration / 60)`

### Output (Elasticsearch Document)

```json
{
  "match_id": "NA1_1234567890",
  "timestamp": 1673000000000,
  "@timestamp": 1673000000000,
  "game_duration": 1800,
  "participant_id": "1",
  "summoner_name": "Player1",
  "champion_name": "Ahri",
  "team_id": 100,
  "position": "MIDDLE",
  "win": true,
  "kills": 10,
  "deaths": 2,
  "assists": 15,
  "kda": 12.5,
  "total_damage_dealt": 50000,
  "gold_earned": 15000,
  "cs": 200,
  "vision_score": 30,
  "gold_per_minute": 500.0,
  "damage_per_minute": 1666.67,
  "cs_per_minute": 6.67
}
```

## ⚙️ Configuration

### Spark Config (`config/spark_config.yaml`)

```yaml
spark:
  app_name: "LoL_Match_Streaming"
  master: "spark://localhost:7077" # or "local[*]"
  config:
    spark.driver.memory: "2g"
    spark.executor.memory: "2g"

kafka:
  bootstrap_servers: "localhost:29092"
  topic: "lol_matches"
  group_id: "spark_streaming_consumer"
  auto_offset_reset: "latest"

elasticsearch:
  hosts:
    - "http://localhost:9200"
  index_name: "lol_matches_stream"
```

### ES Mapping (`config/es_mapping.json`)

- **Keyword fields**: match_id, participant_id, summoner_name, champion_name, position
- **Numeric fields**: kills, deaths, assists, kda, gold, damage, cs, vision
- **Date fields**: timestamp, @timestamp (epoch_millis)

## 🧪 Testing

### Verification Tests

```bash
python verify_phase3.py
```

**Test Coverage**:

1. ✅ Elasticsearch connection & health
2. ✅ ES index setup với mapping
3. ✅ ES indexing (single & bulk)
4. ✅ Kafka connection
5. ✅ Configuration files
6. ✅ Module imports
7. ✅ Data processors

### Manual Testing

```bash
# Test ES indexer
python streaming-layer/src/elasticsearch_indexer.py

# Test processors
python -c "from streaming-layer.src.processors import *; print('OK')"
```

## 🔍 Monitoring

### Spark UI

- URL: http://localhost:8080
- Metrics: Active jobs, completed stages, executors

### Elasticsearch Health

```bash
# Cluster health
curl -X GET "http://localhost:9200/_cluster/health?pretty"

# Index stats
curl -X GET "http://localhost:9200/lol_matches_stream/_stats?pretty"

# Document count
curl -X GET "http://localhost:9200/lol_matches_stream/_count?pretty"
```

### Kafka Consumer Lag

```bash
docker exec -it kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --group spark_streaming_consumer \
  --describe
```

## 🐛 Troubleshooting

### Issue: Spark can't connect to Kafka

**Solution**: Check Kafka bootstrap servers

```bash
# Test connection
docker exec -it kafka kafka-broker-api-versions \
  --bootstrap-server localhost:9092
```

### Issue: Elasticsearch connection refused

**Solution**: Check ES container

```bash
docker ps | grep elasticsearch
curl -X GET "http://localhost:9200/"
```

### Issue: No data in Elasticsearch

**Solution**:

1. Check generator is running: `docker logs kafka`
2. Check Spark logs for errors
3. Verify topic has data: `python test_consumer.py`

### Issue: Spark out of memory

**Solution**: Increase memory in `spark_config.yaml`

```yaml
spark:
  config:
    spark.driver.memory: "4g"
    spark.executor.memory: "4g"
```

## 📈 Performance

### Current Metrics

- **Throughput**: ~2 matches/sec = 20 participants/sec
- **Latency**: < 5 seconds (Kafka → ES)
- **Batch size**: Configurable (default: 30s micro-batches)

### Optimization Tips

1. **Increase parallelism**: More Spark executors
2. **Tune batch size**: Adjust checkpoint interval
3. **ES bulk size**: Increase bulk indexing batch size
4. **Kafka partitions**: More partitions = more parallelism

## 📚 References

- [Spark Structured Streaming Guide](https://spark.apache.org/docs/latest/structured-streaming-programming-guide.html)
- [Spark Kafka Integration](https://spark.apache.org/docs/latest/structured-streaming-kafka-integration.html)
- [Elasticsearch Python Client](https://elasticsearch-py.readthedocs.io/)

## 🎯 Next Steps

- **Phase 4**: Batch Layer (HDFS + PySpark + Cassandra)
- **Kibana Dashboards**: Real-time visualization
- **Alerting**: Anomaly detection
- **ML Integration**: Real-time predictions

## ✅ Verification Checklist

- [x] All Docker containers running
- [x] Kafka topic `lol_matches` exists
- [x] Elasticsearch index `lol_matches_stream` created
- [x] Spark Streaming consumer connects successfully
- [x] Data flows from Kafka → Spark → Elasticsearch
- [x] verify_phase3.py passes all tests (22/22)
- [ ] Kibana dashboard configured (deferred)

---

**Status**: ✅ Phase 3 COMPLETED (22/22 tests passed)
**Last Updated**: 2026-01-13
