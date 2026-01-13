# Phase 4 - Batch Layer Implementation Guide

**Objective**: Build the batch processing layer of Lambda Architecture to store historical data and support analytics

**Timeline**: Week 6-7 (2 weeks)

**Prerequisites**:

- ✅ Phase 3 completed (Streaming layer operational)
- ✅ Docker containers running (HDFS, Cassandra)
- ✅ Phase 3 pipeline continues running during Phase 4 development

---

## 📋 Table of Contents

1. [Preparation & Readiness](#preparation--readiness)
2. [Phase 4 Overview](#phase-4-overview)
3. [Step 1: Batch Consumer (Kafka → HDFS)](#step-1-batch-consumer-kafka--hdfs)
4. [Step 2: HDFS Organization](#step-2-hdfs-organization)
5. [Step 3: PySpark ETL Pipeline](#step-3-pyspark-etl-pipeline)
6. [Step 4: Cassandra Integration](#step-4-cassandra-integration)
7. [Testing & Verification](#testing--verification)
8. [Troubleshooting](#troubleshooting)

---

## 🚀 Preparation & Readiness

### Pre-Flight Checklist

Before starting Phase 4 development, complete these preparation steps:

#### 1. Backup Phase 3 Configuration

```powershell
# Create backup directory
New-Item -ItemType Directory -Force -Path .\backups\phase3

# Backup Kafka consumer offsets
docker exec kafka kafka-consumer-groups `
  --bootstrap-server localhost:9092 `
  --describe --all-groups > .\backups\phase3\kafka_offsets_$(Get-Date -Format 'yyyyMMdd_HHmmss').txt

# Backup Elasticsearch index info
Invoke-WebRequest "http://localhost:9200/lol_matches_stream/_stats?pretty" `
  -OutFile ".\backups\phase3\es_stats_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"

# Backup Spark checkpoints
Copy-Item -Recurse -Force .\checkpoints\streaming `
  .\backups\phase3\spark_checkpoints_$(Get-Date -Format 'yyyyMMdd_HHmmss')

Write-Host "✅ Phase 3 configuration backed up" -ForegroundColor Green
```

#### 2. Verify HDFS Ready

```powershell
# Check HDFS containers running
Write-Host "`n🔍 Verifying HDFS cluster..." -ForegroundColor Cyan
docker compose ps | Select-String "namenode|datanode"

# Expected output:
# namenode    Up
# datanode    Up

# Check HDFS web UI
Start-Process "http://localhost:9870"
# Expected: Hadoop NameNode web interface

# Verify HDFS is accessible
docker exec namenode hdfs dfsadmin -report

# Expected output should show:
# Live datanodes (1):
# Name: datanode:9866 (datanode)
# Configured Capacity: XXX GB
# DFS Used: XXX GB
# Non DFS Used: XXX GB
# DFS Remaining: XXX GB

Write-Host "✅ HDFS cluster is healthy" -ForegroundColor Green
```

#### 3. Check Cassandra Cluster

```powershell
# Check Cassandra container running
Write-Host "`n🔍 Verifying Cassandra cluster..." -ForegroundColor Cyan
docker compose ps | Select-String "cassandra"

# Expected: cassandra   Up

# Check cluster status
docker exec cassandra nodetool status

# Expected output:
# Status=Up/Down
# State=Normal/Leaving/Joining/Moving
# UN  = Up and Normal
#
# Datacenter: datacenter1
# =======================
# Status  State   Address      Load       Tokens  Owns (effective)  Host ID    Rack
# UN      Normal  172.x.x.x    XX.XX KB   256     100.0%            <UUID>     rack1

# Test CQL connection
docker exec -it cassandra cqlsh -e "DESCRIBE KEYSPACES;"

# Expected: Lists existing keyspaces (system, system_schema, system_auth, etc.)

Write-Host "✅ Cassandra cluster is healthy" -ForegroundColor Green
```

#### 4. Create Phase 4 Working Directory

```powershell
# Create batch-layer directory structure
New-Item -ItemType Directory -Force -Path .\batch-layer\src
New-Item -ItemType Directory -Force -Path .\batch-layer\config
New-Item -ItemType Directory -Force -Path .\batch-layer\tests
New-Item -ItemType Directory -Force -Path .\batch-layer\sql
New-Item -ItemType Directory -Force -Path .\batch-layer\logs

Write-Host "✅ Phase 4 directory structure created" -ForegroundColor Green
```

#### 5. Verify Phase 3 Still Running

```powershell
# Ensure streaming pipeline continues during Phase 4 development
Write-Host "`n🔍 Verifying Phase 3 streaming pipeline..." -ForegroundColor Cyan

# Check data generator
$generatorProcess = Get-Process -Name python -ErrorAction SilentlyContinue |
  Where-Object { $_.CommandLine -like "*generator.py*" }

if ($generatorProcess) {
    Write-Host "✅ Data generator running (PID: $($generatorProcess.Id))" -ForegroundColor Green
} else {
    Write-Host "⚠️ Data generator not running - restart it!" -ForegroundColor Yellow
}

# Check Spark job
docker exec spark-master ps aux | Select-String "spark_streaming_consumer"

# Check Elasticsearch document count
$esCount = (Invoke-WebRequest "http://localhost:9200/lol_matches_stream/_count" `
  -UseBasicParsing | ConvertFrom-Json).count
Write-Host "✅ Elasticsearch: $esCount documents indexed" -ForegroundColor Green

# Check Spark UI
try {
    Invoke-WebRequest "http://localhost:4040" -UseBasicParsing -TimeoutSec 3 | Out-Null
    Write-Host "✅ Spark UI accessible at http://localhost:4040" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Spark UI not accessible - check Spark job" -ForegroundColor Yellow
}
```

#### 6. Verify Kafka Topics

```powershell
# List Kafka topics
docker exec kafka kafka-topics --bootstrap-server localhost:9092 --list

# Expected: lol_matches

# Check topic details
docker exec kafka kafka-topics --bootstrap-server localhost:9092 `
  --describe --topic lol_matches

# Expected output:
# Topic: lol_matches    PartitionCount: 3    ReplicationFactor: 1
# Partition: 0    Leader: 1    Replicas: 1    Isr: 1
# Partition: 1    Leader: 1    Replicas: 1    Isr: 1
# Partition: 2    Leader: 1    Replicas: 1    Isr: 1

Write-Host "✅ Kafka topic verified" -ForegroundColor Green
```

---

## 📚 Phase 4 Overview

### Lambda Architecture - Batch Layer

```
┌─────────────────────────────────────────────────────┐
│          Phase 3 (Speed Layer) - ACTIVE             │
│  Generator → Kafka → Spark Streaming → ES → Kibana  │
└─────────────────────┬───────────────────────────────┘
                      │
                      ↓
┌─────────────────────────────────────────────────────┐
│          Phase 4 (Batch Layer) - NEW                │
│                                                      │
│  Kafka → Batch Consumer → HDFS (Data Lake)         │
│           ↓                                         │
│  PySpark ETL → Transformations → Cassandra         │
│           ↓                                         │
│  Historical Analytics & ML Features                │
└─────────────────────────────────────────────────────┘
```

### Key Differences: Streaming vs Batch

| Aspect          | Speed Layer (Phase 3)       | Batch Layer (Phase 4)        |
| --------------- | --------------------------- | ---------------------------- |
| **Latency**     | Real-time (< 10s)           | Minutes to hours             |
| **Data Volume** | Micro-batches (40-200 docs) | Large batches (1000s docs)   |
| **Processing**  | Incremental                 | Full reprocessing            |
| **Storage**     | Elasticsearch (hot data)    | HDFS + Cassandra (cold data) |
| **Purpose**     | Live dashboards             | Historical analytics, ML     |
| **Retention**   | Short-term (days)           | Long-term (years)            |

### Phase 4 Components

1. **Batch Consumer** (`batch_consumer.py`)

   - Consume from Kafka in large batches (50 messages)
   - Write to HDFS in Parquet format
   - Partition by date (YYYY/MM/DD)
   - Checkpoint mechanism for fault tolerance

2. **HDFS Organization**

   - Directory structure: `/data/lol_matches/YYYY/MM/DD/`
   - File format: Parquet (columnar, compressed)
   - Naming convention: `matches_YYYYMMDD_HHmmss_<batch_id>.parquet`
   - Retention policy: 1 year

3. **PySpark ETL Pipeline** (`pyspark_etl.py`)

   - Read from HDFS
   - Data cleaning and validation
   - Feature engineering for ML
   - Aggregations and transformations
   - Write to Cassandra

4. **Cassandra Storage** (`cassandra_writer.py`)
   - Keyspace: `lol_data`
   - Table: `match_participants`
   - Partition key: `match_date, match_id`
   - Query optimization for analytics

---

## 🔧 Step 1: Batch Consumer (Kafka → HDFS)

### 1.1 Create Configuration File

Create `batch-layer/config/batch_config.yaml`:

```yaml
# Kafka Configuration
kafka:
  bootstrap_servers: "kafka:9092" # Internal Docker network
  topic: "lol_matches"
  group_id: "batch_consumer_group"
  auto_offset_reset: "earliest"
  max_poll_records: 50 # Batch size
  enable_auto_commit: false # Manual commit for reliability

# HDFS Configuration
hdfs:
  namenode_url: "hdfs://namenode:9000"
  base_path: "/data/lol_matches"
  file_format: "parquet"
  compression: "snappy"
  partition_by: "date" # YYYY/MM/DD

# Batch Processing
batch:
  size: 50 # Messages per batch
  timeout: 60 # Seconds to wait for full batch
  checkpoint_dir: "./checkpoints/batch"
  log_dir: "./batch-layer/logs"

# Retry Policy
retry:
  max_attempts: 3
  backoff_seconds: 5

# Monitoring
monitoring:
  log_level: "INFO"
  metrics_enabled: true
  healthcheck_interval: 60 # Seconds
```

### 1.2 Implement Batch Consumer

Create `batch-layer/src/batch_consumer.py`:

```python
#!/usr/bin/env python3
"""
Batch Consumer: Kafka → HDFS
Consumes messages from Kafka in batches and writes to HDFS in Parquet format.
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

import yaml
from kafka import KafkaConsumer, TopicPartition
from kafka.errors import KafkaError
import pyarrow as pa
import pyarrow.parquet as pq
from hdfs import InsecureClient
import pandas as pd


class BatchConsumer:
    """Batch consumer for Kafka → HDFS pipeline"""

    def __init__(self, config_path: str = "batch-layer/config/batch_config.yaml"):
        """Initialize batch consumer with configuration"""
        self.config = self._load_config(config_path)
        self.logger = self._setup_logging()

        # Initialize Kafka consumer
        self.consumer = self._create_consumer()

        # Initialize HDFS client
        self.hdfs_client = self._create_hdfs_client()

        # Checkpoint tracking
        self.checkpoint_dir = Path(self.config['batch']['checkpoint_dir'])
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        self.logger.info("Batch Consumer initialized successfully")

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        log_dir = Path(self.config['batch']['log_dir'])
        log_dir.mkdir(parents=True, exist_ok=True)

        log_file = log_dir / f"batch_consumer_{datetime.now().strftime('%Y%m%d')}.log"

        logging.basicConfig(
            level=getattr(logging, self.config['monitoring']['log_level']),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )

        return logging.getLogger(__name__)

    def _create_consumer(self) -> KafkaConsumer:
        """Create and configure Kafka consumer"""
        kafka_config = self.config['kafka']

        consumer = KafkaConsumer(
            kafka_config['topic'],
            bootstrap_servers=kafka_config['bootstrap_servers'],
            group_id=kafka_config['group_id'],
            auto_offset_reset=kafka_config['auto_offset_reset'],
            enable_auto_commit=kafka_config['enable_auto_commit'],
            max_poll_records=kafka_config['max_poll_records'],
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            key_deserializer=lambda m: m.decode('utf-8') if m else None
        )

        self.logger.info(f"Kafka consumer created for topic: {kafka_config['topic']}")
        return consumer

    def _create_hdfs_client(self) -> InsecureClient:
        """Create HDFS client"""
        hdfs_config = self.config['hdfs']
        namenode_url = hdfs_config['namenode_url'].replace('hdfs://', 'http://')

        # Extract host and port
        parts = namenode_url.replace('http://', '').split(':')
        host = parts[0]
        port = 9870  # WebHDFS port

        client = InsecureClient(f'http://{host}:{port}')

        self.logger.info(f"HDFS client connected to: {host}:{port}")
        return client

    def _get_hdfs_path(self, batch_date: datetime) -> str:
        """Generate HDFS path based on date partitioning"""
        base_path = self.config['hdfs']['base_path']
        year = batch_date.strftime('%Y')
        month = batch_date.strftime('%m')
        day = batch_date.strftime('%d')

        return f"{base_path}/{year}/{month}/{day}"

    def _generate_filename(self, batch_id: int) -> str:
        """Generate unique filename for batch"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"matches_{timestamp}_batch{batch_id}.parquet"

    def consume_batch(self) -> List[Dict[str, Any]]:
        """Consume a batch of messages from Kafka"""
        batch_size = self.config['batch']['size']
        timeout = self.config['batch']['timeout']

        messages = []
        start_time = datetime.now()

        try:
            # Poll messages
            while len(messages) < batch_size:
                # Check timeout
                elapsed = (datetime.now() - start_time).total_seconds()
                if elapsed > timeout:
                    self.logger.warning(f"Batch timeout reached. Got {len(messages)}/{batch_size} messages")
                    break

                # Poll with 1 second timeout
                msg_batch = self.consumer.poll(timeout_ms=1000, max_records=batch_size - len(messages))

                for topic_partition, msgs in msg_batch.items():
                    for msg in msgs:
                        messages.append({
                            'data': msg.value,
                            'offset': msg.offset,
                            'partition': msg.partition,
                            'timestamp': msg.timestamp
                        })

            self.logger.info(f"Consumed batch: {len(messages)} messages")
            return messages

        except KafkaError as e:
            self.logger.error(f"Kafka error during consume: {e}")
            raise

    def write_to_hdfs(self, messages: List[Dict[str, Any]], batch_id: int) -> str:
        """Write batch to HDFS in Parquet format"""
        if not messages:
            self.logger.warning("No messages to write to HDFS")
            return None

        try:
            # Extract match data and flatten participants
            records = []
            for msg in messages:
                match_data = msg['data']

                # Flatten participants
                for participant in match_data.get('participants', []):
                    record = {
                        'match_id': match_data.get('match_id'),
                        'match_timestamp': match_data.get('timestamp'),
                        'match_duration': match_data.get('duration'),
                        'summoner_name': participant.get('summoner_name'),
                        'champion_name': participant.get('champion_name'),
                        'position': participant.get('position'),
                        'team_id': participant.get('team_id'),
                        'win': participant.get('win'),
                        'kills': participant.get('kills'),
                        'deaths': participant.get('deaths'),
                        'assists': participant.get('assists'),
                        'kda': participant.get('kda'),
                        'gold_earned': participant.get('gold_earned'),
                        'total_damage': participant.get('total_damage'),
                        'cs': participant.get('cs'),
                        'vision_score': participant.get('vision_score'),
                        'kafka_offset': msg['offset'],
                        'kafka_partition': msg['partition'],
                        'ingestion_timestamp': datetime.fromtimestamp(msg['timestamp'] / 1000).isoformat()
                    }
                    records.append(record)

            # Convert to DataFrame
            df = pd.DataFrame(records)

            # Add date column for partitioning
            df['match_date'] = pd.to_datetime(df['match_timestamp'], unit='ms').dt.date

            # Determine HDFS path
            batch_date = datetime.now()
            hdfs_dir = self._get_hdfs_path(batch_date)
            filename = self._generate_filename(batch_id)
            hdfs_path = f"{hdfs_dir}/{filename}"

            # Create directory if not exists
            self.hdfs_client.makedirs(hdfs_dir)

            # Write to Parquet
            table = pa.Table.from_pandas(df)

            # Write to local temp file first
            temp_file = f"/tmp/{filename}"
            pq.write_table(
                table,
                temp_file,
                compression=self.config['hdfs']['compression']
            )

            # Upload to HDFS
            self.hdfs_client.upload(hdfs_path, temp_file, overwrite=True)

            # Clean up temp file
            os.remove(temp_file)

            self.logger.info(f"Written {len(records)} records to HDFS: {hdfs_path}")
            return hdfs_path

        except Exception as e:
            self.logger.error(f"Error writing to HDFS: {e}")
            raise

    def commit_offsets(self):
        """Commit Kafka offsets after successful HDFS write"""
        try:
            self.consumer.commit()
            self.logger.info("Kafka offsets committed")
        except KafkaError as e:
            self.logger.error(f"Error committing offsets: {e}")
            raise

    def save_checkpoint(self, batch_id: int, hdfs_path: str, message_count: int):
        """Save checkpoint for recovery"""
        checkpoint = {
            'batch_id': batch_id,
            'timestamp': datetime.now().isoformat(),
            'hdfs_path': hdfs_path,
            'message_count': message_count,
            'consumer_group': self.config['kafka']['group_id']
        }

        checkpoint_file = self.checkpoint_dir / f"checkpoint_{batch_id}.json"
        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint, f, indent=2)

        self.logger.info(f"Checkpoint saved: {checkpoint_file}")

    def run(self, num_batches: int = None):
        """Main execution loop"""
        self.logger.info("Starting Batch Consumer...")

        batch_id = 0

        try:
            while True:
                # Check if we've reached the target number of batches
                if num_batches and batch_id >= num_batches:
                    self.logger.info(f"Completed {num_batches} batches. Exiting.")
                    break

                # Consume batch
                messages = self.consume_batch()

                if not messages:
                    self.logger.info("No messages consumed. Waiting...")
                    continue

                # Write to HDFS
                hdfs_path = self.write_to_hdfs(messages, batch_id)

                # Commit offsets
                self.commit_offsets()

                # Save checkpoint
                self.save_checkpoint(batch_id, hdfs_path, len(messages))

                batch_id += 1
                self.logger.info(f"Batch {batch_id} completed successfully")

        except KeyboardInterrupt:
            self.logger.info("Batch Consumer stopped by user")
        except Exception as e:
            self.logger.error(f"Fatal error: {e}", exc_info=True)
            raise
        finally:
            self.close()

    def close(self):
        """Clean up resources"""
        self.logger.info("Closing Batch Consumer...")
        self.consumer.close()
        self.logger.info("Batch Consumer closed")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Batch Consumer: Kafka → HDFS')
    parser.add_argument('--config', default='batch-layer/config/batch_config.yaml',
                       help='Path to configuration file')
    parser.add_argument('--batches', type=int, default=None,
                       help='Number of batches to process (None = infinite)')

    args = parser.parse_args()

    # Create and run consumer
    consumer = BatchConsumer(config_path=args.config)
    consumer.run(num_batches=args.batches)


if __name__ == '__main__':
    main()
```

### 1.3 Install Dependencies

Create `batch-layer/requirements.txt`:

```txt
# Kafka
kafka-python==2.0.2

# HDFS
hdfs==2.7.0

# Data Processing
pandas==2.1.3
pyarrow==14.0.1

# Configuration
pyyaml==6.0.1

# Monitoring
prometheus-client==0.19.0
```

Install dependencies:

```powershell
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install batch layer dependencies
pip install -r batch-layer/requirements.txt
```

### 1.4 Prepare HDFS Directory

**IMPORTANT**: Before running batch consumer, create HDFS directory with proper permissions:

```powershell
# Create base directory in HDFS
docker exec namenode hdfs dfs -mkdir -p /data/lol_matches

# Set permissions (required for external access)
docker exec namenode hdfs dfs -chmod -R 777 /data/lol_matches

# Verify
docker exec namenode hdfs dfs -ls /data

Write-Host "✅ HDFS directory ready" -ForegroundColor Green
```

### 1.5 Test Batch Consumer

```powershell
# Test with 1 batch
python batch-layer/src/batch_consumer.py --batches 1

# Expected output:
# 2026-01-13 10:00:00 - INFO - Batch Consumer initialized successfully
# 2026-01-13 10:00:05 - INFO - Consumed batch: 50 messages
# 2026-01-13 10:00:10 - INFO - Written 500 records to HDFS: /data/lol_matches/2026/01/13/matches_20260113_100010_batch0.parquet
# 2026-01-13 10:00:10 - INFO - Kafka offsets committed
# 2026-01-13 10:00:10 - INFO - Checkpoint saved
# 2026-01-13 10:00:10 - INFO - Batch 1 completed successfully
```

---

## 📁 Step 2: HDFS Organization

### 2.1 Verify HDFS Directory Structure

```powershell
# List HDFS root directory
docker exec namenode hdfs dfs -ls /

# Create base directory
docker exec namenode hdfs dfs -mkdir -p /data/lol_matches

# Verify creation
docker exec namenode hdfs dfs -ls /data

# Check batch consumer created partitions
docker exec namenode hdfs dfs -ls -R /data/lol_matches

# Expected structure:
# /data/lol_matches/
# ├── 2026/
# │   └── 01/
# │       └── 13/
# │           ├── matches_20260113_100010_batch0.parquet
# │           ├── matches_20260113_101015_batch1.parquet
# │           └── ...
```

### 2.2 Check File Details

```powershell
# Check file size
docker exec namenode hdfs dfs -du -h /data/lol_matches/2026/01/13

# Check file count
docker exec namenode hdfs dfs -count /data/lol_matches

# Read Parquet file metadata (using PySpark later)
```

### 2.3 HDFS Web UI

Open HDFS NameNode UI to browse files visually:

```powershell
Start-Process "http://localhost:9870"
```

Navigate to:

- **Utilities** → **Browse the file system**
- Go to `/data/lol_matches/2026/01/13/`
- View file sizes, replication, block info

---

## ⚡ Step 3: PySpark ETL Pipeline

### 3.1 PySpark Environment Setup

**CRITICAL**: Do NOT run PySpark locally on Windows due to Java environment issues. Use the existing Spark container from Phase 3.

**Why Docker Approach?**

- Windows lacks native Java/Hadoop support
- Existing Spark container has proper environment (Java 11, Spark 3.5.0, Python 3.8)
- Isolation: Won't affect Phase 3 streaming pipeline
- Dependencies downloaded on-demand via `--packages` flag

**Prerequisites**:

```powershell
# 1. Verify Spark container running
docker ps | Select-String "spark-master"

# 2. Create Ivy cache directory with permissions
docker exec -u root spark-master bash -c "mkdir -p /home/spark/.ivy2/cache && chmod -R 777 /home/spark/.ivy2"

# 3. Install PyYAML in container (required for config)
docker exec -u root spark-master pip install pyyaml

# 4. Verify spark-submit location
docker exec spark-master which spark-submit
# Expected: /opt/spark/bin/spark-submit

Write-Host "✅ PySpark environment ready" -ForegroundColor Green
```

### 3.2 Create PySpark ETL Script (Docker-Optimized)

Create `batch-layer/src/pyspark_etl_docker.py`:

```python
#!/usr/bin/env python3
"""
PySpark ETL Pipeline: HDFS → Transformations → Cassandra (Docker-Optimized)
Processes historical data from HDFS and writes to Cassandra.

IMPORTANT: This script runs INSIDE Spark container, not on Windows host.
"""

import sys
import yaml
from datetime import datetime
from typing import Dict, Any

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import (
    col, when, avg, count,
    hour, dayofweek,
    round as spark_round, lit
)


class PySparkETL:
    """PySpark ETL pipeline for batch processing"""

    def __init__(self, config_path: str = "/app/batch-layer/config/batch_config.yaml"):
        """Initialize PySpark ETL"""
        self.config = self._load_config(config_path)
        self.spark = self._create_spark_session()

        print("✅ PySpark ETL initialized")

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration"""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def _create_spark_session(self) -> SparkSession:
        """Create Spark session with Cassandra connector"""
        # NOTE: Cassandra connector auto-downloaded via spark-submit --packages
        spark = SparkSession.builder \
            .appName("LoL_Batch_ETL_Docker") \
            .config("spark.hadoop.fs.defaultFS", "hdfs://namenode:9000") \
            .getOrCreate()

        print(f"✅ Spark session created: {spark.version}")
        return spark

    def read_from_hdfs(self, date_str: str = None) -> DataFrame:
        """Read Parquet files from HDFS using native Spark HDFS client"""
        if date_str is None:
            date_str = datetime.now().strftime('%Y/%m/%d')

        # Use native HDFS access from inside container
        hdfs_path = f"hdfs://namenode:9000/data/lol_matches/{date_str}/*.parquet"

        print(f"📖 Reading from HDFS: {hdfs_path}")

        df = self.spark.read.parquet(hdfs_path)

        record_count = df.count()
        print(f"✅ Loaded {record_count} records from HDFS")
        return df

    def clean_data(self, df: DataFrame) -> DataFrame:
        """Clean and validate data"""
        print("🧹 Cleaning data...")

        initial_count = df.count()

        # Remove nulls in critical fields
        df_clean = df.dropna(subset=['match_id', 'summoner_name', 'champion_name'])

        # Filter invalid data
        df_clean = df_clean.filter(
            (col('kills') >= 0) &
            (col('deaths') >= 0) &
            (col('assists') >= 0) &
            (col('gold_earned') > 0) &
            (col('match_duration') > 0)
        )

        # Recalculate KDA (in case of issues)
        df_clean = df_clean.withColumn(
            'kda_calculated',
            when(col('deaths') == 0, col('kills') + col('assists'))
            .otherwise((col('kills') + col('assists')) / col('deaths'))
        )

        final_count = df_clean.count()
        records_removed = initial_count - final_count
        print(f"✅ Cleaned data: {records_removed} invalid records removed ({final_count} remain)")

        return df_clean

    def feature_engineering(self, df: DataFrame) -> DataFrame:
        """Create features for ML"""
        print("🔧 Engineering features...")

        from pyspark.sql.types import TimestampType

        df_features = df \
            .withColumn('participant_id', col('summoner_name')) \
            .withColumn('gold_per_minute',
                       spark_round(col('gold_earned') / (col('match_duration') / 60), 2)) \
            .withColumn('damage_per_minute',
                       spark_round(col('total_damage') / (col('match_duration') / 60), 2)) \
            .withColumn('cs_per_minute',
                       spark_round(col('cs') / (col('match_duration') / 60), 2)) \
            .withColumn('kill_participation',
                       spark_round((col('kills') + col('assists')) / 10.0, 2)) \
            .withColumn('match_hour',
                       hour(col('match_timestamp').cast('timestamp'))) \
            .withColumn('match_day_of_week',
                       dayofweek(col('match_timestamp').cast('timestamp'))) \
            .withColumn('is_weekend',
                       when(col('match_day_of_week').isin([1, 7]), lit(True)).otherwise(lit(False))) \
            .drop('ingestion_timestamp')

        print("✅ Features engineered: gold_per_minute, damage_per_minute, cs_per_minute, etc.")
        return df_features

    def aggregate_stats(self, df: DataFrame):
        """Create aggregated statistics"""
        print("📊 Computing aggregations...")

        # Champion performance stats
        champion_stats = df.groupBy('champion_name') \
            .agg(
                count('*').alias('games_played'),
                spark_round(avg(col('win').cast('int')) * 100, 2).alias('win_rate'),
                spark_round(avg('kills'), 2).alias('avg_kills'),
                spark_round(avg('deaths'), 2).alias('avg_deaths'),
                spark_round(avg('assists'), 2).alias('avg_assists'),
                spark_round(avg('kda_calculated'), 2).alias('avg_kda'),
                spark_round(avg('gold_per_minute'), 2).alias('avg_gpm'),
                spark_round(avg('damage_per_minute'), 2).alias('avg_dpm')
            )

        print(f"  ✅ Champion stats: {champion_stats.count()} champions")

        # Position stats
        position_stats = df.groupBy('position') \
            .agg(
                count('*').alias('games_played'),
                spark_round(avg(col('win').cast('int')) * 100, 2).alias('win_rate'),
                spark_round(avg('kda_calculated'), 2).alias('avg_kda'),
                spark_round(avg('gold_per_minute'), 2).alias('avg_gpm')
            )

        print(f"  ✅ Position stats: {position_stats.count()} positions")

        return champion_stats, position_stats

    def write_to_cassandra(self, df: DataFrame, table_name: str, keyspace: str = "lol_data"):
        """Write DataFrame to Cassandra"""
        print(f"💾 Writing to Cassandra: {keyspace}.{table_name}")

        df.write \
            .format("org.apache.spark.sql.cassandra") \
            .mode("append") \
            .options(table=table_name, keyspace=keyspace) \
            .save()

        print(f"✅ Written {df.count()} records to Cassandra table: {table_name}")

    def run_etl(self, date_str: str = None):
        """Execute full ETL pipeline"""
        start_time = datetime.now()
        print("\n" + "="*50)
        print("🚀 Starting PySpark ETL Pipeline (Docker Mode)")
        print("="*50 + "\n")

        try:
            # Step 1: Read from HDFS
            df_raw = self.read_from_hdfs(date_str)

            # Step 2: Clean data
            df_clean = self.clean_data(df_raw)

            # Step 3: Feature engineering
            df_features = self.feature_engineering(df_clean)

            # Step 4: Write main participant data to Cassandra
            self.write_to_cassandra(df_features, 'match_participants')

            # Step 5: Compute and write aggregations
            champion_stats, position_stats = self.aggregate_stats(df_features)
            self.write_to_cassandra(champion_stats, 'champion_stats')
            self.write_to_cassandra(position_stats, 'position_stats')

            elapsed = (datetime.now() - start_time).total_seconds()
            print("\n" + "="*50)
            print(f"✅ PySpark ETL Pipeline Completed in {elapsed:.2f}s")
            print("="*50 + "\n")

        except Exception as e:
            print(f"\n❌ ETL Pipeline Failed: {e}")
            raise

    def close(self):
        """Stop Spark session"""
        self.spark.stop()
        print("✅ Spark session stopped")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='PySpark ETL: HDFS → Cassandra (Docker)')
    parser.add_argument('--date', default=None,
                       help='Date to process (YYYY/MM/DD format). Default: today')
    parser.add_argument('--config', default='/app/batch-layer/config/batch_config.yaml',
                       help='Path to configuration file')

    args = parser.parse_args()

    # Create and run ETL
    etl = PySparkETL(config_path=args.config)

    try:
        etl.run_etl(date_str=args.date)
    finally:
        etl.close()


if __name__ == '__main__':
    main()
```

### 3.3 Deploy and Run PySpark ETL

**Step 1: Copy script to Spark container**

```powershell
# Copy Docker-optimized script
docker cp batch-layer/src/pyspark_etl_docker.py spark-master:/app/batch-layer/src/pyspark_etl.py

Write-Host "✅ PySpark ETL script copied to container" -ForegroundColor Green
```

**Step 2: Run ETL with spark-submit**

```powershell
# Run ETL for today's data
docker exec spark-master /opt/spark/bin/spark-submit `
  --master local[*] `
  --packages com.datastax.spark:spark-cassandra-connector_2.12:3.4.0 `
  --conf spark.cassandra.connection.host=cassandra `
  --conf spark.cassandra.connection.port=9042 `
  /app/batch-layer/src/pyspark_etl.py --date 2026/01/13

# Expected output:
# ✅ Spark session created: 3.5.0
# 📖 Reading from HDFS: hdfs://namenode:9000/data/lol_matches/2026/01/13/*.parquet
# ✅ Loaded 500 records from HDFS
# ✅ Cleaned data: 0 invalid records removed (500 remain)
# ✅ Features engineered: gold_per_minute, damage_per_minute, cs_per_minute, etc.
# ✅ Written 500 records to Cassandra table: match_participants
# ✅ Champion stats: 36 champions
# ✅ Position stats: 5 positions
# ✅ Written 36 records to Cassandra table: champion_stats
# ✅ Written 5 records to Cassandra table: position_stats
# ✅ PySpark ETL Pipeline Completed in 14.44s
```

**Step 3: Verify data in Cassandra**

```powershell
# Check record counts
docker exec cassandra cqlsh -e "USE lol_data; SELECT COUNT(*) FROM match_participants;"
# Expected: 500

docker exec cassandra cqlsh -e "USE lol_data; SELECT COUNT(*) FROM champion_stats;"
# Expected: ~36

docker exec cassandra cqlsh -e "USE lol_data; SELECT COUNT(*) FROM position_stats;"
# Expected: 5

# Check sample data
docker exec cassandra cqlsh -e "SELECT champion_name, games_played, win_rate, avg_kda, avg_gpm FROM lol_data.champion_stats LIMIT 5;"

# Check position stats
docker exec cassandra cqlsh -e "SELECT * FROM lol_data.position_stats;"
```

**Key Implementation Notes**:

1. **Dependencies Auto-Download**: `--packages` flag downloads 18 JAR files (Cassandra connector + dependencies) to `/home/spark/.ivy2/` - does NOT modify container permanently

2. **participant_id Column**: Required as part of Cassandra PRIMARY KEY - generated from `summoner_name`

3. **ingestion_timestamp Dropped**: This column from batch consumer doesn't exist in Cassandra schema, so it's dropped during feature engineering

4. **Boolean Cast for Aggregation**: `avg(win)` requires casting boolean to int: `avg(col('win').cast('int'))`

5. **Native HDFS Access**: Inside container, use `hdfs://namenode:9000` directly - no subprocess workarounds needed

6. **Phase 3 Unaffected**: All dependencies are isolated, streaming pipeline continues running normally

---

## 💾 Step 4: Cassandra Integration

### 4.1 Design Cassandra Schema

Create `batch-layer/config/cassandra_schema.cql`:

```sql
-- Create Keyspace
CREATE KEYSPACE IF NOT EXISTS lol_data
WITH REPLICATION = {
    'class': 'SimpleStrategy',
    'replication_factor': 1
};

USE lol_data;

-- Main Table: Match Participants (Historical Data)
CREATE TABLE IF NOT EXISTS match_participants (
    match_date date,
    match_id text,
    participant_id text,
    match_timestamp bigint,
    match_duration int,
    summoner_name text,
    champion_name text,
    position text,
    team_id int,
    win boolean,
    kills int,
    deaths int,
    assists int,
    kda decimal,
    kda_calculated decimal,
    gold_earned int,
    gold_per_minute decimal,
    total_damage int,
    damage_per_minute decimal,
    cs int,
    cs_per_minute decimal,
    vision_score int,
    kill_participation decimal,
    match_hour int,
    match_day_of_week int,
    is_weekend boolean,
    kafka_offset bigint,
    kafka_partition int,
    ingestion_timestamp timestamp,
    PRIMARY KEY ((match_date, match_id), participant_id)
) WITH CLUSTERING ORDER BY (participant_id ASC)
  AND comment = 'Historical match participant data from batch layer';

-- Champion Statistics (Aggregated)
CREATE TABLE IF NOT EXISTS champion_stats (
    champion_name text PRIMARY KEY,
    games_played bigint,
    win_rate decimal,
    avg_kills decimal,
    avg_deaths decimal,
    avg_assists decimal,
    avg_kda decimal,
    avg_gpm decimal,
    avg_dpm decimal,
    last_updated timestamp
) WITH comment = 'Aggregated champion performance statistics';

-- Position Statistics (Aggregated)
CREATE TABLE IF NOT EXISTS position_stats (
    position text PRIMARY KEY,
    games_played bigint,
    win_rate decimal,
    avg_kda decimal,
    avg_gpm decimal,
    last_updated timestamp
) WITH comment = 'Aggregated position performance statistics';

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_participant_champion
ON match_participants (champion_name);

CREATE INDEX IF NOT EXISTS idx_participant_position
ON match_participants (position);

CREATE INDEX IF NOT EXISTS idx_participant_summoner
ON match_participants (summoner_name);
```

### 4.2 Initialize Cassandra Schema

```powershell
# Copy schema file to Cassandra container
docker cp batch-layer/config/cassandra_schema.cql cassandra:/tmp/

# Execute schema initialization
docker exec -it cassandra cqlsh -f /tmp/cassandra_schema.cql

# Verify keyspace created
docker exec -it cassandra cqlsh -e "DESCRIBE KEYSPACES;"

# Verify tables created
docker exec -it cassandra cqlsh -e "USE lol_data; DESCRIBE TABLES;"

# Expected output:
# champion_stats  match_participants  position_stats

Write-Host "✅ Cassandra schema initialized" -ForegroundColor Green
```

### 4.3 Test Cassandra Connection

Create `batch-layer/src/test_cassandra.py`:

```python
#!/usr/bin/env python3
"""Test Cassandra connection and schema"""

from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider


def test_cassandra():
    """Test Cassandra connection"""
    print("🔍 Testing Cassandra connection...")

    # Connect to Cassandra
    cluster = Cluster(['localhost'], port=9042)
    session = cluster.connect()

    print("✅ Connected to Cassandra")

    # Check keyspace
    result = session.execute("SELECT keyspace_name FROM system_schema.keyspaces WHERE keyspace_name='lol_data';")
    if result.one():
        print("✅ Keyspace 'lol_data' exists")
    else:
        print("❌ Keyspace 'lol_data' NOT found")
        return False

    # Use keyspace
    session.set_keyspace('lol_data')

    # Check tables
    tables = ['match_participants', 'champion_stats', 'position_stats']
    for table in tables:
        result = session.execute(f"SELECT table_name FROM system_schema.tables WHERE keyspace_name='lol_data' AND table_name='{table}';")
        if result.one():
            print(f"✅ Table '{table}' exists")
        else:
            print(f"❌ Table '{table}' NOT found")

    # Insert test record
    print("\n🧪 Inserting test record...")
    session.execute("""
        INSERT INTO match_participants (
            match_date, match_id, participant_id, summoner_name, champion_name, win
        ) VALUES (
            '2026-01-13', 'test_match_001', 'test_part_001', 'TestPlayer', 'TestChamp', true
        );
    """)
    print("✅ Test record inserted")

    # Query test record
    result = session.execute("SELECT * FROM match_participants WHERE match_date='2026-01-13' AND match_id='test_match_001';")
    row = result.one()
    if row:
        print(f"✅ Test record retrieved: {row.summoner_name}, {row.champion_name}")

    # Clean up test record
    session.execute("DELETE FROM match_participants WHERE match_date='2026-01-13' AND match_id='test_match_001';")
    print("✅ Test record deleted")

    cluster.shutdown()
    print("\n✅ All Cassandra tests passed!")
    return True


if __name__ == '__main__':
    test_cassandra()
```

Run test:

```powershell
# Install Cassandra driver
pip install cassandra-driver

# Run test
python batch-layer/src/test_cassandra.py
```

---

## ✅ Testing & Verification

### Create Phase 4 Verification Script

Create `verify_phase4.py`:

```python
#!/usr/bin/env python3
"""
Phase 4 Verification Script
Tests all components of the Batch Layer
"""

import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Test imports
def test_imports():
    """Test all required module imports"""
    print("\n1️⃣ Testing Module Imports...")

    try:
        import kafka
        print("  ✅ kafka-python")

        import hdfs
        print("  ✅ hdfs")

        import pandas
        print("  ✅ pandas")

        import pyarrow
        print("  ✅ pyarrow")

        from pyspark.sql import SparkSession
        print("  ✅ pyspark")

        from cassandra.cluster import Cluster
        print("  ✅ cassandra-driver")

        return True
    except ImportError as e:
        print(f"  ❌ Import failed: {e}")
        return False


def test_hdfs_connection():
    """Test HDFS connectivity"""
    print("\n2️⃣ Testing HDFS Connection...")

    try:
        from hdfs import InsecureClient

        client = InsecureClient('http://localhost:9870')

        # List root directory
        files = client.list('/')
        print(f"  ✅ HDFS connected - Root contains: {files}")

        # Check if batch directory exists
        if client.status('/data/lol_matches', strict=False):
            print("  ✅ Batch directory exists: /data/lol_matches")
        else:
            print("  ⚠️ Batch directory not found (will be created by consumer)")

        return True
    except Exception as e:
        print(f"  ❌ HDFS connection failed: {e}")
        return False


def test_cassandra_connection():
    """Test Cassandra connectivity and schema"""
    print("\n3️⃣ Testing Cassandra Connection...")

    try:
        from cassandra.cluster import Cluster

        cluster = Cluster(['localhost'], port=9042)
        session = cluster.connect()

        print("  ✅ Cassandra connected")

        # Check keyspace
        result = session.execute("SELECT keyspace_name FROM system_schema.keyspaces WHERE keyspace_name='lol_data';")
        if result.one():
            print("  ✅ Keyspace 'lol_data' exists")
        else:
            print("  ⚠️ Keyspace 'lol_data' not found - run cassandra_schema.cql")
            cluster.shutdown()
            return False

        # Check tables
        session.set_keyspace('lol_data')
        tables = ['match_participants', 'champion_stats', 'position_stats']

        for table in tables:
            result = session.execute(f"SELECT table_name FROM system_schema.tables WHERE keyspace_name='lol_data' AND table_name='{table}';")
            if result.one():
                print(f"  ✅ Table '{table}' exists")
            else:
                print(f"  ❌ Table '{table}' not found")
                cluster.shutdown()
                return False

        cluster.shutdown()
        return True

    except Exception as e:
        print(f"  ❌ Cassandra connection failed: {e}")
        return False


def test_kafka_connection():
    """Test Kafka connectivity for batch consumer"""
    print("\n4️⃣ Testing Kafka Connection (Batch Consumer)...")

    try:
        from kafka import KafkaConsumer

        consumer = KafkaConsumer(
            'lol_matches',
            bootstrap_servers='localhost:29092',
            group_id='batch_test_group',
            auto_offset_reset='earliest',
            consumer_timeout_ms=5000
        )

        print("  ✅ Kafka consumer created")

        # Get partitions
        partitions = consumer.partitions_for_topic('lol_matches')
        print(f"  ✅ Topic 'lol_matches' has {len(partitions)} partitions")

        consumer.close()
        return True

    except Exception as e:
        print(f"  ❌ Kafka connection failed: {e}")
        return False


def test_configuration_files():
    """Test configuration files exist"""
    print("\n5️⃣ Testing Configuration Files...")

    config_files = [
        'batch-layer/config/batch_config.yaml',
        'batch-layer/config/cassandra_schema.cql'
    ]

    all_exist = True
    for config_file in config_files:
        if Path(config_file).exists():
            print(f"  ✅ {config_file}")
        else:
            print(f"  ❌ {config_file} NOT FOUND")
            all_exist = False

    return all_exist


def test_batch_scripts():
    """Test batch layer scripts exist"""
    print("\n6️⃣ Testing Batch Layer Scripts...")

    scripts = [
        'batch-layer/src/batch_consumer.py',
        'batch-layer/src/pyspark_etl.py',
        'batch-layer/src/test_cassandra.py'
    ]

    all_exist = True
    for script in scripts:
        if Path(script).exists():
            print(f"  ✅ {script}")
        else:
            print(f"  ❌ {script} NOT FOUND")
            all_exist = False

    return all_exist


def test_directory_structure():
    """Test batch layer directory structure"""
    print("\n7️⃣ Testing Directory Structure...")

    directories = [
        'batch-layer',
        'batch-layer/src',
        'batch-layer/config',
        'batch-layer/tests',
        'batch-layer/logs',
        'checkpoints/batch'
    ]

    all_exist = True
    for directory in directories:
        dir_path = Path(directory)
        if dir_path.exists() and dir_path.is_dir():
            print(f"  ✅ {directory}/")
        else:
            print(f"  ❌ {directory}/ NOT FOUND")
            all_exist = False

    return all_exist


def main():
    """Run all verification tests"""
    print("="*60)
    print("🚀 PHASE 4 BATCH LAYER VERIFICATION")
    print("="*60)

    tests = [
        ("Module Imports", test_imports),
        ("HDFS Connection", test_hdfs_connection),
        ("Cassandra Connection", test_cassandra_connection),
        ("Kafka Connection", test_kafka_connection),
        ("Configuration Files", test_configuration_files),
        ("Batch Scripts", test_batch_scripts),
        ("Directory Structure", test_directory_structure)
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "="*60)
    print("📊 VERIFICATION SUMMARY")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status} - {test_name}")

    print(f"\n🎯 Score: {passed}/{total} tests passed")

    if passed == total:
        print("\n✅ Phase 4 Batch Layer: Ready to implement!")
        return 0
    else:
        print("\n⚠️ Some tests failed - fix issues before proceeding")
        return 1


if __name__ == '__main__':
    sys.exit(main())
```

Run verification:

```powershell
python verify_phase4.py
```

---

## 🚨 Troubleshooting

### Issue 1: HDFS Connection Refused

**Symptom**: `ConnectionRefusedError: [WinError 10061]`

**Solution**:

```powershell
# Check HDFS containers
docker compose ps | Select-String "namenode|datanode"

# Restart HDFS
docker compose restart namenode datanode

# Wait 30 seconds
Start-Sleep -Seconds 30

# Check NameNode UI
Start-Process "http://localhost:9870"
```

### Issue 2: Cassandra Not Ready

**Symptom**: `NoHostAvailable` error

**Solution**:

```powershell
# Check Cassandra status
docker exec cassandra nodetool status

# If not ready, restart
docker compose restart cassandra

# Wait for startup (can take 2-3 minutes)
Start-Sleep -Seconds 120

# Test connection
docker exec -it cassandra cqlsh
```

### Issue 3: Kafka Consumer Group Conflict

**Symptom**: Consumer lag or duplicate processing

**Solution**:

```powershell
# Reset consumer group
docker exec kafka kafka-consumer-groups --bootstrap-server localhost:9092 `
  --group batch_consumer_group --reset-offsets --to-earliest --topic lol_matches --execute

# Or delete consumer group
docker exec kafka kafka-consumer-groups --bootstrap-server localhost:9092 `
  --group batch_consumer_group --delete
```

### Issue 4: PySpark on Windows (Java/JAVA_HOME Errors)

**Symptom**: `JAVA_HOME is not set` or `java.io.IOException: Could not locate executable null\bin\winutils.exe`

**Solution**: **DO NOT** try to fix Java on Windows. Use Docker approach:

```powershell
# ❌ WRONG: Running PySpark locally on Windows
python batch-layer/src/pyspark_etl.py

# ✅ CORRECT: Running inside Spark container
docker exec spark-master /opt/spark/bin/spark-submit /app/batch-layer/src/pyspark_etl.py
```

**Why Docker?**

- Windows lacks native Hadoop/Spark support
- Java environment configuration is complex and error-prone
- Container has everything pre-configured (Java 11, Spark 3.5.0, Python 3.8)
- Isolation prevents conflicts with Phase 3 streaming

### Issue 5: Missing Cassandra Connector JARs

**Symptom**: `ClassNotFoundException: com.datastax.spark.connector`

**Solution**: Ensure `--packages` flag is used in spark-submit:

```powershell
# Correct command with --packages
docker exec spark-master /opt/spark/bin/spark-submit `
  --master local[*] `
  --packages com.datastax.spark:spark-cassandra-connector_2.12:3.4.0 `
  --conf spark.cassandra.connection.host=cassandra `
  /app/batch-layer/src/pyspark_etl.py
```

**First Run**: Downloads 18 JAR files (~18 MB) to `/home/spark/.ivy2/cache/`
**Subsequent Runs**: Uses cached JARs (fast startup)

### Issue 6: Permission Denied on Ivy Cache

**Symptom**: `java.io.FileNotFoundException: /home/spark/.ivy2/cache (Permission denied)`

**Solution**: Create directory with proper permissions:

```powershell
docker exec -u root spark-master bash -c "mkdir -p /home/spark/.ivy2/cache && chmod -R 777 /home/spark/.ivy2"
```

### Issue 7: ModuleNotFoundError: yaml

**Symptom**: `ModuleNotFoundError: No module named 'yaml'`

**Solution**: Install PyYAML in Spark container:

```powershell
docker exec -u root spark-master pip install pyyaml
```

### Issue 8: Invalid Date Error (Type Mismatch)

**Symptom**: `java.lang.IllegalArgumentException: Invalid date: 2026-01-13T11:51:47.999000`

**Root Cause**: `ingestion_timestamp` column from batch consumer is STRING type but Cassandra expects TIMESTAMP

**Solution**: Drop the column (it's not in Cassandra schema anyway):

```python
# In feature_engineering() method
df_features = df \
    .withColumn(...) \
    .drop('ingestion_timestamp')  # Add this line
```

### Issue 9: Boolean Aggregation Error

**Symptom**: `[DATATYPE_MISMATCH.UNEXPECTED_INPUT_TYPE] Cannot resolve "avg(win)" due to data type mismatch: Parameter 1 requires the "NUMERIC" type, however "win" has the type "BOOLEAN"`

**Solution**: Cast boolean to int before aggregation:

```python
# ❌ WRONG
avg('win').alias('win_rate')

# ✅ CORRECT
avg(col('win').cast('int')).alias('win_rate')
```

### Issue 10: Missing participant_id Column

**Symptom**: `Error: missing primary key columns: [participant_id]`

**Solution**: Add `participant_id` in feature engineering:

```python
df_features = df \
    .withColumn('participant_id', col('summoner_name')) \
    .withColumn('gold_per_minute', ...)
```

### Issue 11: Phase 3 Streaming Affected?

**Concern**: Will batch layer installation break Phase 3?

**Answer**: **NO** - Batch layer is completely isolated:

✅ **Safe Operations**:

- spark-submit with `--packages` (downloads to separate cache)
- pip install in container (only adds PyYAML)
- No configuration files modified
- No shared state between batch and streaming

✅ **Verification**:

```powershell
# Check Phase 3 still running
docker exec spark-master ps aux | Select-String "spark_streaming_consumer"

# Check Elasticsearch still receiving data
Invoke-RestMethod "http://localhost:9200/lol_matches_stream/_count"
```

---

## 📚 Next Steps

After completing Phase 4 setup:

1. **Run Batch Consumer** for continuous ingestion to HDFS
2. **Schedule PySpark ETL** jobs (daily/hourly)
3. **Monitor HDFS Storage** - set up disk usage alerts
4. **Query Cassandra** - test analytical queries
5. **Integrate with Phase 5** - ML feature engineering from Cassandra

---

## 🎯 Phase 4 Completion Criteria

✅ **Phase 4 Complete When**:

1. Batch consumer successfully writes to HDFS
2. HDFS contains partitioned Parquet files by date
3. PySpark ETL runs without errors
4. Data successfully written to Cassandra tables
5. Can query historical data from Cassandra
6. Verification script passes all tests (7/7)
7. Documentation complete

**Expected Duration**: 2 weeks  
**Next Phase**: Phase 5 - Machine Learning Layer

---

**Created**: January 13, 2026  
**Phase**: 4 - Batch Layer Implementation  
**Status**: 📋 Ready to Start
