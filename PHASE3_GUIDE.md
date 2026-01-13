# PHASE 3 GUIDE - Streaming Layer Implementation

## 🎯 Objective

Implement real-time streaming pipeline using Spark Streaming to process LoL match data from Kafka and index into Elasticsearch for visualization in Kibana.

---

## 📋 Phase 3 Overview

### Components

1. **Spark Streaming Consumer** - Consume from Kafka topic `lol_matches`
2. **Real-time Processing** - Calculate metrics (win rate, KDA, gold/min)
3. **Elasticsearch Indexer** - Index processed data for visualization
4. **Kibana Dashboard** - Real-time visualization

### Architecture Flow

```
Kafka (lol_matches)
    ↓
Spark Streaming (micro-batches: 30s)
    ↓
Real-time Aggregations (window: 5 min)
    ↓
Elasticsearch (time-series index)
    ↓
Kibana (real-time dashboard)
```

---

## 🛠️ STEP 1: Verify Prerequisites

### 1.1 Check Running Services

```bash
# Check Docker containers
docker ps

# Expected containers:
# - kafka, zookeeper
# - spark-master, spark-worker
# - elasticsearch, kibana
# - cassandra, prometheus, grafana
```

### 1.2 Verify Kafka Topic

```bash
# List topics
docker exec -it kafka kafka-topics --list --bootstrap-server localhost:9092

# Should see: lol_matches
```

### 1.3 Check Elasticsearch

```bash
# Test ES connection
curl -X GET "http://localhost:9200/_cluster/health?pretty"

# Should return: status "green" or "yellow"
```

### 1.4 Check Kibana

```bash
# Open browser
http://localhost:5601

# Should see Kibana home page
```

### 1.5 Verify All Services Health

```powershell
# Check all containers status
docker compose ps

# Expected output: All containers with status "Up"
# - zookeeper, kafka (message queue)
# - spark-master, spark-worker (processing)
# - elasticsearch, kibana (storage & visualization)
# - cassandra (batch storage)
# - prometheus, grafana (monitoring)

# Quick health check command
docker compose ps | Select-String "Up"
```

---

## 📦 STEP 2: Install Required Packages

### 2.1 Update requirements.txt

Add to `requirements.txt`:

```txt
# Existing packages...

# Phase 3 - Streaming Layer
pyspark==3.5.0
elasticsearch==8.11.0
```

### 2.2 Install Packages

```bash
# Activate virtual environment
.\.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Install new packages
pip install pyspark==3.5.0 elasticsearch==8.11.0
```

---

## 🔧 STEP 3: Create Streaming Layer Structure

### 3.1 Directory Structure

```
streaming-layer/
├── src/
│   ├── __init__.py
│   ├── spark_streaming_consumer.py    # Main Spark Streaming app
│   ├── elasticsearch_indexer.py       # ES client and indexing
│   └── processors.py                  # Data processing functions
├── config/
│   ├── spark_config.yaml              # Spark configuration
│   └── es_mapping.json                # Elasticsearch index mapping
└── tests/
    └── test_streaming.py              # Unit tests
```

### 3.2 Create Directory

```bash
mkdir -p streaming-layer/src
mkdir -p streaming-layer/config
mkdir -p streaming-layer/tests
```

---

## 💻 STEP 4: Implement Elasticsearch Indexer

### 4.1 Create ES Index Mapping

Create `streaming-layer/config/es_mapping.json`:

```json
{
  "settings": {
    "number_of_shards": 3,
    "number_of_replicas": 1,
    "refresh_interval": "5s"
  },
  "mappings": {
    "properties": {
      "match_id": {
        "type": "keyword"
      },
      "timestamp": {
        "type": "date",
        "format": "epoch_millis"
      },
      "game_duration": {
        "type": "integer"
      },
      "participant_id": {
        "type": "keyword"
      },
      "summoner_name": {
        "type": "keyword"
      },
      "champion_name": {
        "type": "keyword"
      },
      "team_id": {
        "type": "integer"
      },
      "position": {
        "type": "keyword"
      },
      "win": {
        "type": "boolean"
      },
      "kills": {
        "type": "integer"
      },
      "deaths": {
        "type": "integer"
      },
      "assists": {
        "type": "integer"
      },
      "kda": {
        "type": "float"
      },
      "total_damage_dealt": {
        "type": "long"
      },
      "gold_earned": {
        "type": "integer"
      },
      "cs": {
        "type": "integer"
      },
      "vision_score": {
        "type": "integer"
      },
      "gold_per_minute": {
        "type": "float"
      },
      "damage_per_minute": {
        "type": "float"
      },
      "cs_per_minute": {
        "type": "float"
      }
    }
  }
}
```

### 4.2 Create ES Indexer Module

Create `streaming-layer/src/elasticsearch_indexer.py`:

```python
"""
Elasticsearch Indexer for LoL Match Data
Handles connection, index creation, and bulk indexing
"""

from elasticsearch import Elasticsearch, helpers
from elasticsearch.exceptions import ConnectionError, RequestError
import json
import logging
from typing import List, Dict, Any
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ElasticsearchIndexer:
    """
    Elasticsearch indexer for LoL match streaming data
    """

    def __init__(self,
                 hosts: List[str] = None,
                 index_name: str = "lol_matches_stream",
                 mapping_file: str = None):
        """
        Initialize ES client

        Args:
            hosts: List of ES hosts (default: ["http://localhost:9200"])
            index_name: Name of the index
            mapping_file: Path to mapping JSON file
        """
        self.hosts = hosts or ["http://localhost:9200"]
        self.index_name = index_name
        self.mapping_file = mapping_file

        # Initialize ES client
        self.es = None
        self.connect()

        # Create index if not exists
        if self.es and not self.index_exists():
            self.create_index()

    def connect(self) -> bool:
        """
        Connect to Elasticsearch

        Returns:
            bool: True if connection successful
        """
        try:
            self.es = Elasticsearch(
                hosts=self.hosts,
                verify_certs=False,
                request_timeout=30
            )

            # Test connection
            if self.es.ping():
                logger.info(f"✓ Connected to Elasticsearch: {self.hosts}")
                return True
            else:
                logger.error("✗ Failed to ping Elasticsearch")
                return False

        except ConnectionError as e:
            logger.error(f"✗ Connection error: {e}")
            self.es = None
            return False

    def index_exists(self) -> bool:
        """
        Check if index exists

        Returns:
            bool: True if index exists
        """
        try:
            return self.es.indices.exists(index=self.index_name)
        except Exception as e:
            logger.error(f"Error checking index existence: {e}")
            return False

    def create_index(self) -> bool:
        """
        Create index with mapping

        Returns:
            bool: True if creation successful
        """
        try:
            # Load mapping from file
            mapping = None
            if self.mapping_file:
                with open(self.mapping_file, 'r') as f:
                    mapping = json.load(f)

            # Create index
            if mapping:
                self.es.indices.create(
                    index=self.index_name,
                    body=mapping
                )
            else:
                self.es.indices.create(index=self.index_name)

            logger.info(f"✓ Created index: {self.index_name}")
            return True

        except RequestError as e:
            if e.error == 'resource_already_exists_exception':
                logger.warning(f"Index {self.index_name} already exists")
                return True
            else:
                logger.error(f"✗ Error creating index: {e}")
                return False
        except Exception as e:
            logger.error(f"✗ Unexpected error creating index: {e}")
            return False

    def index_document(self, document: Dict[str, Any]) -> bool:
        """
        Index single document

        Args:
            document: Document to index

        Returns:
            bool: True if indexing successful
        """
        try:
            # Add @timestamp for Kibana
            document['@timestamp'] = document.get('timestamp',
                                                  int(datetime.now().timestamp() * 1000))

            response = self.es.index(
                index=self.index_name,
                document=document
            )

            return response['result'] in ['created', 'updated']

        except Exception as e:
            logger.error(f"✗ Error indexing document: {e}")
            return False

    def bulk_index(self, documents: List[Dict[str, Any]]) -> tuple:
        """
        Bulk index documents

        Args:
            documents: List of documents to index

        Returns:
            tuple: (success_count, failed_count)
        """
        try:
            if not documents:
                return (0, 0)

            # Prepare actions for bulk API
            actions = []
            for doc in documents:
                # Add @timestamp
                doc['@timestamp'] = doc.get('timestamp',
                                           int(datetime.now().timestamp() * 1000))

                actions.append({
                    '_index': self.index_name,
                    '_source': doc
                })

            # Execute bulk
            success, failed = helpers.bulk(
                self.es,
                actions,
                raise_on_error=False,
                stats_only=True
            )

            logger.info(f"✓ Bulk indexed: {success} docs, {failed} failed")
            return (success, failed)

        except Exception as e:
            logger.error(f"✗ Error in bulk indexing: {e}")
            return (0, len(documents))

    def delete_index(self) -> bool:
        """
        Delete index

        Returns:
            bool: True if deletion successful
        """
        try:
            if self.index_exists():
                self.es.indices.delete(index=self.index_name)
                logger.info(f"✓ Deleted index: {self.index_name}")
                return True
            else:
                logger.warning(f"Index {self.index_name} does not exist")
                return False
        except Exception as e:
            logger.error(f"✗ Error deleting index: {e}")
            return False

    def refresh_index(self) -> bool:
        """
        Refresh index to make documents searchable

        Returns:
            bool: True if refresh successful
        """
        try:
            self.es.indices.refresh(index=self.index_name)
            return True
        except Exception as e:
            logger.error(f"✗ Error refreshing index: {e}")
            return False

    def count_documents(self) -> int:
        """
        Count documents in index

        Returns:
            int: Document count
        """
        try:
            count = self.es.count(index=self.index_name)
            return count['count']
        except Exception as e:
            logger.error(f"✗ Error counting documents: {e}")
            return 0

    def close(self):
        """Close ES connection"""
        if self.es:
            self.es.close()
            logger.info("✓ Closed Elasticsearch connection")


# Example usage
if __name__ == "__main__":
    # Initialize indexer
    indexer = ElasticsearchIndexer(
        hosts=["http://localhost:9200"],
        index_name="lol_matches_stream",
        mapping_file="streaming-layer/config/es_mapping.json"
    )

    # Test document
    test_doc = {
        "match_id": "TEST_123",
        "timestamp": int(datetime.now().timestamp() * 1000),
        "game_duration": 1800,
        "participant_id": "P1",
        "summoner_name": "TestPlayer",
        "champion_name": "Ahri",
        "team_id": 100,
        "position": "MIDDLE",
        "win": True,
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

    # Index test document
    success = indexer.index_document(test_doc)
    print(f"Indexing: {'Success' if success else 'Failed'}")

    # Count documents
    count = indexer.count_documents()
    print(f"Total documents: {count}")

    # Close connection
    indexer.close()
```

---

## ⚡ STEP 5: Implement Spark Streaming Consumer

### 5.1 Create Spark Configuration

Create `streaming-layer/config/spark_config.yaml`:

```yaml
spark:
  app_name: "LoL_Match_Streaming"
  master: "spark://localhost:7077"

  # Spark configurations
  config:
    spark.driver.memory: "2g"
    spark.executor.memory: "2g"
    spark.executor.cores: "2"
    spark.default.parallelism: "4"
    spark.streaming.backpressure.enabled: "true"
    spark.streaming.kafka.maxRatePerPartition: "100"

kafka:
  bootstrap_servers: "localhost:29092"
  topic: "lol_matches"
  group_id: "spark_streaming_consumer"
  auto_offset_reset: "latest"

streaming:
  batch_interval: 30 # seconds
  window_duration: 300 # seconds (5 minutes)
  slide_interval: 60 # seconds (1 minute)
  checkpoint_location: "checkpoints/streaming"

elasticsearch:
  hosts:
    - "http://localhost:9200"
  index_name: "lol_matches_stream"
  mapping_file: "streaming-layer/config/es_mapping.json"

logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

### 5.2 Create Processors Module

Create `streaming-layer/src/processors.py`:

```python
"""
Data Processing Functions for Spark Streaming
Calculate real-time metrics from match data
"""

from pyspark.sql import DataFrame
from pyspark.sql.functions import (
    col, when, round as spark_round,
    sum as spark_sum, avg, count,
    window, current_timestamp
)
from typing import Dict, Any
import json


def parse_match_data(rdd):
    """
    Parse JSON match data from Kafka

    Args:
        rdd: RDD containing Kafka messages

    Returns:
        List of participant records
    """
    def extract_participants(message):
        """Extract all participants from a match"""
        try:
            match = json.loads(message)
            participants = []

            for participant in match.get('info', {}).get('participants', []):
                participants.append({
                    'match_id': match['metadata']['matchId'],
                    'timestamp': match['info']['gameCreation'],
                    'game_duration': match['info']['gameDuration'],
                    'participant_id': participant['participantId'],
                    'summoner_name': participant['summonerName'],
                    'champion_name': participant['championName'],
                    'team_id': participant['teamId'],
                    'position': participant['teamPosition'],
                    'win': participant['win'],
                    'kills': participant['kills'],
                    'deaths': participant['deaths'],
                    'assists': participant['assists'],
                    'total_damage_dealt': participant['totalDamageDealtToChampions'],
                    'gold_earned': participant['goldEarned'],
                    'cs': participant['totalMinionsKilled'] + participant.get('neutralMinionsKilled', 0),
                    'vision_score': participant['visionScore']
                })

            return participants
        except Exception as e:
            print(f"Error parsing match: {e}")
            return []

    # Flat map to extract all participants
    return rdd.flatMap(extract_participants)


def calculate_derived_metrics(df: DataFrame) -> DataFrame:
    """
    Calculate derived metrics (KDA, per-minute stats)

    Args:
        df: DataFrame with participant data

    Returns:
        DataFrame with added metrics
    """
    # Calculate KDA
    df = df.withColumn(
        'kda',
        spark_round(
            when(col('deaths') == 0, col('kills') + col('assists'))
            .otherwise((col('kills') + col('assists')) / col('deaths')),
            2
        )
    )

    # Calculate per-minute metrics
    df = df.withColumn(
        'gold_per_minute',
        spark_round(col('gold_earned') / (col('game_duration') / 60), 2)
    )

    df = df.withColumn(
        'damage_per_minute',
        spark_round(col('total_damage_dealt') / (col('game_duration') / 60), 2)
    )

    df = df.withColumn(
        'cs_per_minute',
        spark_round(col('cs') / (col('game_duration') / 60), 2)
    )

    return df


def calculate_champion_stats(df: DataFrame) -> DataFrame:
    """
    Calculate champion-level statistics

    Args:
        df: DataFrame with participant data

    Returns:
        DataFrame with champion aggregations
    """
    champion_stats = df.groupBy('champion_name').agg(
        count('*').alias('games_played'),
        spark_sum(when(col('win'), 1).otherwise(0)).alias('wins'),
        avg('kills').alias('avg_kills'),
        avg('deaths').alias('avg_deaths'),
        avg('assists').alias('avg_assists'),
        avg('kda').alias('avg_kda'),
        avg('gold_per_minute').alias('avg_gpm'),
        avg('damage_per_minute').alias('avg_dpm'),
        avg('cs_per_minute').alias('avg_cspm')
    )

    # Calculate win rate
    champion_stats = champion_stats.withColumn(
        'win_rate',
        spark_round((col('wins') / col('games_played')) * 100, 2)
    )

    return champion_stats


def calculate_position_stats(df: DataFrame) -> DataFrame:
    """
    Calculate position-level statistics

    Args:
        df: DataFrame with participant data

    Returns:
        DataFrame with position aggregations
    """
    position_stats = df.groupBy('position').agg(
        count('*').alias('games_played'),
        avg('kills').alias('avg_kills'),
        avg('deaths').alias('avg_deaths'),
        avg('assists').alias('avg_assists'),
        avg('gold_per_minute').alias('avg_gpm'),
        avg('damage_per_minute').alias('avg_dpm')
    )

    return position_stats
```

(End of processors.py)

---

## ✅ STEP 10: Production Deployment & Verification

### 10.1 Deploy to Docker Cluster

#### Create Spark Job Submission Script

Create `submit_spark_job.ps1`:

```powershell
#!/usr/bin/env pwsh
Write-Host "=" * 50
Write-Host "Submitting Spark Streaming Job to Docker Cluster"
Write-Host "=" * 50

# Install Python dependencies in Spark container
Write-Host "`nInstalling Python dependencies..."
docker exec spark-master pip install pyyaml elasticsearch kafka-python

# Submit Spark job
Write-Host "`nSubmitting job..."
docker exec spark-master spark-submit `
    --master spark://spark-master:7077 `
    --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 `
    --py-files /opt/spark/work-dir/streaming-layer/src/elasticsearch_indexer.py `
    /opt/spark/work-dir/streaming-layer/src/spark_streaming_consumer.py
```

#### Run the Job

```powershell
# Start data generator in separate window
Start-Process powershell -ArgumentList "-NoExit", "-Command", `
  "cd 'E:\FILEMANAGEMENT_PC\_WORKSPACE\PROGRESS\bigbig'; `
  .\.venv\Scripts\Activate.ps1; `
  python data-generator/src/generator.py --mode continuous"

# Wait for generator to start
Start-Sleep -Seconds 3

# Submit Spark job
.\submit_spark_job.ps1
```

### 10.2 Verification Steps

#### Step 1: Verify Spark Application Started

```powershell
# Wait for initialization (15-20 seconds)
Start-Sleep -Seconds 15

# Check Spark UI accessible
curl http://localhost:4040

# Expected: HTTP 200 OK, SparkUI HTML content
```

#### Step 2: Check Spark Master UI

```powershell
# Open browser to Spark Master UI
Start-Process "http://localhost:8080"

# Verify:
# - Running Applications section shows "LoL_Match_Streaming"
# - Application ID: app-YYYYMMDDHHMMSS-XXXX
# - Status: RUNNING
# - Cores in Use: 2
```

#### Step 3: Access Spark Application UI

```powershell
# Open Spark Application UI
Start-Process "http://localhost:4040"

# Navigate to "Streaming" tab
# Verify:
# - Active Streaming Query visible
# - Input Rate > 0 records/sec
# - Processing Rate > 0 records/sec
# - Batch Duration: ~5-10 seconds
# - No failed batches
```

#### Step 4: Verify Elasticsearch Indexing

```powershell
# Check document count
Invoke-WebRequest "http://localhost:9200/lol_matches_stream/_count?pretty"

# Expected output:
# {
#   "count": 3855,  # (increasing over time)
#   "_shards": {
#     "total": 3,
#     "successful": 3
#   }
# }

# Wait 10 seconds and check again
Start-Sleep -Seconds 10
Invoke-WebRequest "http://localhost:9200/lol_matches_stream/_count?pretty"
# Count should be higher (approximately +200 documents per 10 seconds)
```

#### Step 5: Check Spark Job Logs

```powershell
# View Spark master logs
docker logs spark-master --tail 50

# Expected output patterns:
# - "✓ Initialized Spark Structured Streaming"
# - "✓ Connected to Elasticsearch"
# - "✓ Starting Spark Structured Streaming Consumer"
# - "Batch X: Y participants, Y indexed, 0 failed"
# - "✓ Bulk indexed: X docs, 0 failed"

# NO errors like:
# - "ERROR" lines
# - "Exception" traces
# - "Connection refused"
# - "offset was changed" (checkpoint error)
```

#### Step 6: Monitor Data Generator

```powershell
# Generator should show output like:
# 2026-01-13 02:56:35,247 - INFO - Sent: SEA_win vs. PHX_lose | Duration: 1845s
# 2026-01-13 02:56:35,748 - INFO - Sent: CLG_win vs. FNC_lose | Duration: 1792s

# Verify rate: ~2 matches per second
```

### 10.3 Complete Verification Checklist

```
✅ Prerequisites
  ✓ Docker containers running (11 services)
  ✓ Kafka topic 'lol_matches' exists
  ✓ Elasticsearch healthy (green/yellow)

✅ Data Flow
  ✓ Generator producing matches to Kafka
  ✓ Kafka receiving messages (check with kafka-console-consumer)
  ✓ Spark consuming from Kafka
  ✓ Elasticsearch receiving documents

✅ Spark Application
  ✓ Spark Master UI shows running app (http://localhost:8080)
  ✓ Spark Application UI accessible (http://localhost:4040)
  ✓ Streaming tab shows active query
  ✓ Input rate > 0 records/sec
  ✓ No failed batches

✅ Elasticsearch
  ✓ Index 'lol_matches_stream' exists
  ✓ Document count increasing (check every 10 seconds)
  ✓ Bulk indexing: 0 failed documents
  ✓ No connection errors in logs

✅ System Health
  ✓ No ERROR messages in Spark logs
  ✓ No Exception traces
  ✓ Checkpoints being written (./checkpoints/streaming/)
  ✓ All batches processed successfully
```

### 10.4 Expected Performance Metrics

```
Data Generator:
  - Generation rate: 2 matches/second
  - Messages to Kafka: ~10-20 participants/second

Spark Streaming:
  - Batch interval: 5 seconds
  - Input rate: 10-20 records/batch
  - Processing time: 1-3 seconds/batch
  - Total delay: < 5 seconds

Elasticsearch:
  - Bulk indexing: 20-200 docs/batch
  - Index rate: ~40-400 docs/second
  - Failed docs: 0
  - Query response: < 100ms
```

---

## 🚨 TROUBLESHOOTING GUIDE

### Issue 1: Kafka Container Keeps Restarting

**Symptom**:

```powershell
docker compose ps
# Kafka container missing or status "Restarting"
```

**Root Cause**: Cluster ID mismatch between Kafka metadata and Zookeeper

**Check Logs**:

```powershell
docker logs kafka --tail 100 | Select-String "InconsistentClusterIdException"

# Error message:
# InconsistentClusterIdException: The Cluster ID Or8zQec0Sgyru-dkddFCvQ
# doesn't match stored clusterId Some(6r9_qcVoTuCw7V6yvDjAqA)
```

**Solution**:

```powershell
# Step 1: Stop Kafka and remove volumes
docker compose down -v kafka
docker volume rm bigbig_kafka_data

# Step 2: Recreate Kafka with fresh metadata
docker compose up -d kafka

# Step 3: Wait for Kafka to fully start (30-60 seconds)
Start-Sleep -Seconds 60

# Step 4: Check Kafka is healthy
docker logs kafka --tail 20
# Should see: "Kafka Server started"

# Step 5: Recreate topic
docker exec kafka kafka-topics --bootstrap-server localhost:9092 \
  --create --topic lol_matches --partitions 3 --replication-factor 1

# Step 6: Verify topic
docker exec kafka kafka-topics --bootstrap-server localhost:9092 \
  --describe --topic lol_matches

# Expected output:
# Topic: lol_matches  PartitionCount: 3  ReplicationFactor: 1
# Partition: 0  Leader: 1  Replicas: 1  Isr: 1
# Partition: 1  Leader: 1  Replicas: 1  Isr: 1
# Partition: 2  Leader: 1  Replicas: 1  Isr: 1
```

### Issue 2: Spark Job Crashes with Offset Error

**Symptom**:

```
Query terminated with error. Partition lol_matches-2's offset was
changed from 383 to 28, some data may have been missed.
IllegalStateException: failOnDataLoss triggered
```

**Root Cause**: Checkpoint contains old offsets that don't match current Kafka topic (after recreation)

**Solution**:

```powershell
# Step 1: Clear old checkpoints
Remove-Item -Recurse -Force .\checkpoints\streaming\* -ErrorAction SilentlyContinue

# Step 2: Verify checkpoints cleared
Get-ChildItem .\checkpoints\streaming\
# Should be empty or show only .gitkeep

# Step 3: Restart data generator
Start-Process powershell -ArgumentList "-NoExit", "-Command", `
  "cd 'E:\FILEMANAGEMENT_PC\_WORKSPACE\PROGRESS\bigbig'; `
  .\.venv\Scripts\Activate.ps1; `
  python data-generator/src/generator.py --mode continuous"

# Step 4: Wait for generator
Start-Sleep -Seconds 3

# Step 5: Resubmit Spark job
.\submit_spark_job.ps1

# Step 6: Monitor logs for successful start
docker logs spark-master --tail 50

# Expected:
# - "✓ Initialized Spark Structured Streaming"
# - "✓ Connected to Elasticsearch"
# - "Batch X: Y participants, Y indexed, 0 failed"
# NO "offset was changed" errors
```

### Issue 3: Spark UI Not Accessible (Port 4040)

**Symptom**:

```powershell
curl http://localhost:4040
# Error: Unable to connect
```

**Root Cause**: No active Spark application running

**Diagnosis**:

```powershell
# Check if Spark job process exists
docker exec spark-master ps aux | Select-String "spark_streaming_consumer"

# If no output → job not running
```

**Solution**:

```powershell
# Step 1: Check Spark Master UI
Start-Process "http://localhost:8080"
# Look for "Running Applications" section
# If empty → no job running

# Step 2: Verify data generator running
# Look for separate PowerShell window with generator output
# If not found, restart generator:
Start-Process powershell -ArgumentList "-NoExit", "-Command", `
  "cd 'E:\FILEMANAGEMENT_PC\_WORKSPACE\PROGRESS\bigbig'; `
  .\.venv\Scripts\Activate.ps1; `
  python data-generator/src/generator.py --mode continuous"

# Step 3: Wait for data flow
Start-Sleep -Seconds 3

# Step 4: Submit Spark job
.\submit_spark_job.ps1

# Step 5: Wait for UI initialization (15-20 seconds)
Start-Sleep -Seconds 15

# Step 6: Test UI
curl http://localhost:4040 -UseBasicParsing | Select-Object -First 3

# Expected: StatusCode 200, Content shows "Spark UI"

# Step 7: Open in browser
Start-Process "http://localhost:4040"
```

### Issue 4: Elasticsearch Connection Failed

**Symptom**:

```
ConnectionError: Connection refused to http://elasticsearch:9200
```

**Solution**:

```powershell
# Check ES container status
docker compose ps elasticsearch

# If not running:
docker compose restart elasticsearch
Start-Sleep -Seconds 30

# Test connection
curl http://localhost:9200

# Recreate index
curl -X DELETE "http://localhost:9200/lol_matches_stream"
python verify_phase3.py
```

### Issue 5: No Documents in Elasticsearch

**Symptom**: Document count stays at 0

**Diagnosis**:

```powershell
# Check Spark logs for indexing errors
docker logs spark-master --tail 100 | Select-String "failed"

# Check ES index health
curl "http://localhost:9200/lol_matches_stream/_stats?pretty"
```

**Solution**:

```powershell
# Verify data generator producing
# Generator window should show "Sent: ..." messages

# Check Kafka has messages
docker exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic lol_matches --from-beginning --max-messages 1

# If no messages → restart generator
# If messages present but no ES docs → check Spark job logs for errors
```

---

## 📋 Post-Deployment Checklist
