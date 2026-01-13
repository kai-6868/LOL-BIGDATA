# CODEBASE STRUCTURE - Big Data LoL System

## 📁 Tổng quan cấu trúc thư mục

```
lol-bigdata-system/
│
├── 📁 data-generator/              # Data generation & Kafka producer
├── 📁 streaming-layer/             # Real-time processing
├── 📁 batch-layer/                 # Batch processing
├── 📁 ml-layer/                    # Machine Learning pipeline
├── 📁 infrastructure/              # Docker, configs, IaC
├── 📁 monitoring/                  # Monitoring & alerting
├── 📁 tests/                       # End-to-end tests
├── 📁 docs/                        # Documentation
├── 📁 notebooks/                   # Jupyter notebooks
├── 📁 scripts/                     # Utility scripts
├── .gitignore
├── README.md
├── requirements.txt
├── docker-compose.yml
└── Makefile
```

---

## 📂 CHI TIẾT CẤU TRÚC

### 1. 📁 data-generator/ (Currently in root)

**Current Status:** ✅ **IMPLEMENTED** (Single file in root)

```
lol_match_generator.py  # Standalone script (root level)
```

**Current Features:**

- ✅ Riot API v2 format compatibility
- ✅ 36 champion pool (hardcoded)
- ✅ Realistic match statistics generation
- ✅ Kafka producer integration (kafka-python)
- ✅ Continuous generation mode
- ✅ Configurable interval (INTERVAL_SECONDS = 0.5)
- ✅ Fixed topic: 'lol_matches'

**Implementation Details:**

```python
# Key configurations:
BOOTSTRAP_SERVERS = 'localhost:9092'
TOPIC_NAME = 'lol_matches'
INTERVAL_SECONDS = 0.5  # 2 matches/second

# Data structure:
- CHAMPIONS: 36 champions list
- POSITIONS: [TOP, JUNGLE, MIDDLE, BOTTOM, UTILITY]
- Match format: Riot API compatible
  - metadata: matchId, participants PUUIDs
  - info: gameCreation, gameDuration, participants, teams
```

**Planned Structure (Future Refactoring):**

```
data-generator/
├── lol_match_generator.py          # Main script ✅ (move from root)
├── config/
│   ├── champions.json              # Extract champion list
│   ├── kafka_config.yaml           # Externalize Kafka config
│   └── generator_config.yaml       # Externalize settings
├── schemas/
│   └── riot_api_v2_schema.json     # Document format
├── tests/
│   └── test_generator.py           # Unit tests
└── README.md                       # Usage documentation
```

**Công nghệ:**

- Python 3.9+ ✅
- kafka-python ✅
- json, random, time (stdlib) ✅
- Future: PyYAML, Faker (for enhancement)

---

### 2. 📁 streaming-layer/

```
streaming-layer/
├── src/
│   ├── __init__.py
│   ├── spark_streaming_app.py      # Main Spark Streaming app
│   ├── consumers/
│   │   ├── __init__.py
│   │   └── kafka_consumer.py       # Kafka integration
│   ├── processors/
│   │   ├── __init__.py
│   │   ├── window_aggregator.py    # Windowing logic
│   │   ├── stats_calculator.py     # Statistics calculation
│   │   └── enrichment.py           # Data enrichment
│   ├── sinks/
│   │   ├── __init__.py
│   │   ├── elasticsearch_sink.py   # ES writer
│   │   └── console_sink.py         # Debug output
│   └── utils/
│       ├── __init__.py
│       ├── spark_session.py        # Spark session factory
│       └── monitoring.py           # Metrics collection
│
├── config/
│   ├── spark_config.yaml           # Spark configuration
│   ├── elasticsearch_config.yaml   # ES connection
│   └── window_config.yaml          # Window settings
│
├── kibana/
│   ├── dashboards/
│   │   ├── realtime_overview.json
│   │   ├── champion_stats.json
│   │   └── win_rate_analysis.json
│   └── visualizations/
│       ├── time_series.json
│       └── pie_charts.json
│
├── tests/
│   ├── test_streaming_app.py
│   ├── test_processors.py
│   └── test_sinks.py
│
├── requirements.txt
└── README.md
```

**Công nghệ:**

- Apache Spark 3.4+ (Structured Streaming)
- PySpark
- Elasticsearch-py
- Kafka-python

---

### 3. 📁 batch-layer/

```
batch-layer/
├── src/
│   ├── __init__.py
│   ├── batch_consumer.py           # Kafka to HDFS
│   ├── pyspark_etl.py              # Main ETL job
│   ├── jobs/
│   │   ├── __init__.py
│   │   ├── extract_job.py          # Data extraction
│   │   ├── transform_job.py        # Transformation logic
│   │   └── load_job.py             # Load to Cassandra
│   ├── transformers/
│   │   ├── __init__.py
│   │   ├── flatten_json.py         # JSON flattening
│   │   ├── feature_extractor.py    # Feature extraction
│   │   └── aggregator.py           # Data aggregation
│   └── utils/
│       ├── __init__.py
│       ├── hdfs_helper.py          # HDFS operations
│       ├── cassandra_helper.py     # Cassandra operations
│       └── date_utils.py           # Date handling
│
├── config/
│   ├── hdfs_config.yaml            # HDFS settings
│   ├── cassandra_config.yaml       # Cassandra connection
│   ├── spark_batch_config.yaml     # Spark batch config
│   └── schedule.yaml               # Job scheduling
│
├── sql/
│   ├── cassandra_schema.cql        # Cassandra DDL
│   ├── create_keyspace.cql
│   └── analytics_queries.cql       # Sample queries
│
├── tests/
│   ├── test_batch_consumer.py
│   ├── test_etl_job.py
│   └── test_transformers.py
│
├── requirements.txt
└── README.md
```

**Công nghệ:**

- Apache Spark (Batch mode)
- PySpark
- Hadoop HDFS
- Cassandra Driver
- Airflow (scheduling)

---

### 4. 📁 ml-layer/

```
ml-layer/
├── src/
│   ├── __init__.py
│   ├── feature_engineering.py      # Feature engineering
│   ├── model_training.py           # Model training
│   ├── model_prediction.py         # Batch prediction
│   ├── model_evaluation.py         # Model evaluation
│   ├── features/
│   │   ├── __init__.py
│   │   ├── player_features.py      # Player-level features
│   │   ├── champion_features.py    # Champion features
│   │   └── team_features.py        # Team features
│   ├── models/
│   │   ├── __init__.py
│   │   ├── random_forest_model.py  # RF implementation
│   │   ├── model_registry.py       # Model versioning
│   │   └── serving.py              # Model serving API
│   └── utils/
│       ├── __init__.py
│       ├── metrics.py              # Custom metrics
│       └── visualization.py        # Plot functions
│
├── config/
│   ├── features_config.yaml        # Feature definitions
│   ├── model_config.yaml           # Model hyperparameters
│   └── mlflow_config.yaml          # MLflow settings
│
├── notebooks/
│   ├── 01_eda.ipynb                # Exploratory analysis
│   ├── 02_feature_engineering.ipynb
│   ├── 03_model_training.ipynb
│   └── 04_model_evaluation.ipynb
│
├── models/
│   ├── random_forest_v1.pkl
│   ├── feature_scaler.pkl
│   └── label_encoder.pkl
│
├── mlflow/
│   ├── experiment_tracking.py
│   └── model_registry.py
│
├── tests/
│   ├── test_features.py
│   ├── test_model_training.py
│   └── test_prediction.py
│
├── requirements.txt
└── README.md
```

**Công nghệ:**

- Scikit-learn
- MLflow
- XGBoost (alternative model)
- Pandas, NumPy
- Matplotlib, Seaborn

---

### 5. 📁 infrastructure/

```
infrastructure/
├── docker/
│   ├── kafka/
│   │   ├── Dockerfile
│   │   └── server.properties
│   ├── spark/
│   │   ├── Dockerfile
│   │   └── spark-defaults.conf
│   ├── elasticsearch/
│   │   ├── Dockerfile
│   │   └── elasticsearch.yml
│   ├── cassandra/
│   │   ├── Dockerfile
│   │   └── cassandra.yaml
│   └── jupyter/
│       ├── Dockerfile
│       └── jupyter_notebook_config.py
│
├── kubernetes/                      # (Optional) K8s manifests
│   ├── kafka/
│   ├── spark/
│   ├── elasticsearch/
│   └── cassandra/
│
├── terraform/                       # (Optional) IaC
│   ├── main.tf
│   ├── variables.tf
│   └── outputs.tf
│
├── docker-compose.yml               # Main compose file
├── docker-compose.dev.yml           # Dev override
├── docker-compose.prod.yml          # Prod override
│
└── README.md
```

**Công nghệ:**

- Docker & Docker Compose
- Kubernetes (optional)
- Terraform (optional)
- Apache Zookeeper

---

### 6. 📁 monitoring/

```
monitoring/
├── prometheus/
│   ├── prometheus.yml              # Prometheus config
│   ├── alerts.yml                  # Alert rules
│   └── targets.json                # Scrape targets
│
├── grafana/
│   ├── dashboards/
│   │   ├── kafka_metrics.json
│   │   ├── spark_metrics.json
│   │   ├── elasticsearch_metrics.json
│   │   ├── cassandra_metrics.json
│   │   └── ml_model_metrics.json
│   ├── datasources/
│   │   └── prometheus.yaml
│   └── grafana.ini
│
├── exporters/
│   ├── kafka_exporter.py
│   ├── spark_exporter.py
│   └── custom_metrics.py
│
├── alertmanager/
│   └── alertmanager.yml
│
└── README.md
```

**Công nghệ:**

- Prometheus
- Grafana
- Alertmanager
- Node Exporter
- JMX Exporter

---

### 7. 📁 tests/

```
tests/
├── integration/
│   ├── test_end_to_end.py          # Full pipeline test
│   ├── test_streaming_to_es.py
│   └── test_batch_to_cassandra.py
│
├── load/
│   ├── kafka_load_test.py          # Kafka throughput
│   ├── es_query_load_test.py       # ES performance
│   └── cassandra_write_test.py     # Cassandra write perf
│
├── data_quality/
│   ├── test_schema_validation.py
│   ├── test_data_completeness.py
│   └── test_data_accuracy.py
│
├── fixtures/
│   ├── sample_matches.json
│   └── test_data.json
│
└── README.md
```

**Công nghệ:**

- pytest
- pytest-benchmark
- Locust (load testing)
- Great Expectations (data quality)

---

### 8. 📁 docs/

```
docs/
├── architecture/
│   ├── system_design.md
│   ├── data_flow.md
│   ├── component_diagram.png
│   └── sequence_diagram.png
│
├── api/
│   ├── api_reference.md
│   ├── kafka_topics.md
│   ├── elasticsearch_indices.md
│   └── cassandra_schema.md
│
├── deployment/
│   ├── local_setup.md
│   ├── docker_deployment.md
│   ├── cloud_deployment.md
│   └── kubernetes_deployment.md
│
├── guides/
│   ├── getting_started.md
│   ├── development_guide.md
│   ├── troubleshooting.md
│   └── best_practices.md
│
└── README.md
```

---

### 9. 📁 notebooks/

```
notebooks/
├── exploration/
│   ├── 01_data_exploration.ipynb
│   ├── 02_kafka_consumer_test.ipynb
│   └── 03_elasticsearch_queries.ipynb
│
├── analytics/
│   ├── champion_analysis.ipynb
│   ├── win_rate_trends.ipynb
│   └── player_performance.ipynb
│
└── README.md
```

---

### 10. 📁 scripts/

```
scripts/
├── setup/
│   ├── init_kafka.sh               # Kafka topic creation
│   ├── init_elasticsearch.sh       # ES index setup
│   ├── init_cassandra.sh           # Cassandra keyspace
│   └── setup_all.sh                # Full setup
│
├── deployment/
│   ├── deploy_streaming.sh
│   ├── deploy_batch.sh
│   └── deploy_ml.sh
│
├── maintenance/
│   ├── backup_cassandra.sh
│   ├── clean_old_data.sh
│   └── health_check.py
│
├── data/
│   ├── load_sample_data.py
│   └── generate_test_data.py
│
└── README.md
```

---

## 📦 ROOT FILES

### requirements.txt

```txt
# Core dependencies
kafka-python==2.0.2
pyspark==3.4.1
elasticsearch==8.9.0
cassandra-driver==3.28.0
pandas==2.0.3
numpy==1.24.3
scikit-learn==1.3.0
mlflow==2.5.0

# Data generation
Faker==19.2.0
avro-python3==1.10.2

# Monitoring
prometheus-client==0.17.1
grafana-client==3.5.0

# Testing
pytest==7.4.0
pytest-benchmark==4.0.0
locust==2.15.1
great-expectations==0.17.12

# Utilities
PyYAML==6.0
python-dotenv==1.0.0
click==8.1.6
rich==13.5.2

# Development
jupyter==1.0.0
black==23.7.0
flake8==6.1.0
mypy==1.4.1
```

### docker-compose.yml

```yaml
version: "3.8"

services:
  zookeeper:
    image: confluentinc/cp-zookeeper:7.4.0
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
    ports:
      - "2181:2181"

  kafka:
    image: confluentinc/cp-kafka:7.4.0
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:29092,PLAINTEXT_HOST://localhost:9092
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1

  namenode:
    image: bde2020/hadoop-namenode:2.0.0-hadoop3.2.1-java8
    ports:
      - "9870:9870"
      - "9000:9000"
    environment:
      - CLUSTER_NAME=test
    env_file:
      - ./infrastructure/docker/hadoop/hadoop.env

  datanode:
    image: bde2020/hadoop-datanode:2.0.0-hadoop3.2.1-java8
    environment:
      SERVICE_PRECONDITION: "namenode:9870"
    env_file:
      - ./infrastructure/docker/hadoop/hadoop.env

  spark-master:
    image: bitnami/spark:3.4.1
    ports:
      - "8080:8080"
      - "7077:7077"
    environment:
      - SPARK_MODE=master

  spark-worker:
    image: bitnami/spark:3.4.1
    depends_on:
      - spark-master
    environment:
      - SPARK_MODE=worker
      - SPARK_MASTER_URL=spark://spark-master:7077

  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.9.0
    ports:
      - "9200:9200"
      - "9300:9300"
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false

  kibana:
    image: docker.elastic.co/kibana/kibana:8.9.0
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch

  cassandra:
    image: cassandra:4.1
    ports:
      - "9042:9042"
    environment:
      - CASSANDRA_CLUSTER_NAME=lol_cluster

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    depends_on:
      - prometheus
    volumes:
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards

  jupyter:
    build: ./infrastructure/docker/jupyter
    ports:
      - "8888:8888"
    volumes:
      - ./notebooks:/home/jovyan/work
```

### Makefile

```makefile
.PHONY: help setup start stop clean test

help:
	@echo "Available commands:"
	@echo "  make setup    - Setup infrastructure"
	@echo "  make start    - Start all services"
	@echo "  make stop     - Stop all services"
	@echo "  make test     - Run tests"
	@echo "  make clean    - Clean up everything"

setup:
	docker-compose up -d
	./scripts/setup/setup_all.sh

start:
	docker-compose up -d
	python data-generator/src/lol_match_generator.py &
	spark-submit streaming-layer/src/spark_streaming_app.py &

stop:
	docker-compose down

test:
	pytest tests/ -v

clean:
	docker-compose down -v
	rm -rf data/*
	rm -rf logs/*
```

---

## 🔧 CÔNG NGHỆ STACK SUMMARY

| Layer                  | Công nghệ              | Version | Mục đích               |
| ---------------------- | ---------------------- | ------- | ---------------------- |
| **Data Ingestion**     | Apache Kafka           | 3.5     | Message broker         |
|                        | Zookeeper              | 3.8     | Kafka coordination     |
| **Stream Processing**  | Apache Spark Streaming | 3.4     | Real-time processing   |
| **Batch Processing**   | Apache Spark (Batch)   | 3.4     | Batch ETL              |
|                        | Hadoop HDFS            | 3.3     | Data lake storage      |
| **Search & Analytics** | Elasticsearch          | 8.9     | Search engine          |
|                        | Kibana                 | 8.9     | Visualization          |
| **Database**           | Apache Cassandra       | 4.1     | NoSQL storage          |
| **Machine Learning**   | Scikit-learn           | 1.3     | ML algorithms          |
|                        | MLflow                 | 2.5     | ML lifecycle           |
| **Monitoring**         | Prometheus             | Latest  | Metrics collection     |
|                        | Grafana                | Latest  | Dashboards             |
| **Container**          | Docker                 | Latest  | Containerization       |
|                        | Docker Compose         | Latest  | Orchestration          |
| **Language**           | Python                 | 3.9+    | Primary language       |
| **Testing**            | pytest                 | 7.4     | Unit/integration tests |
|                        | Locust                 | 2.15    | Load testing           |

---

## 🚀 QUICK START

```bash
# 1. Clone repository
git clone <repo-url>
cd lol-bigdata-system

# 2. Setup infrastructure
make setup

# 3. Start all services
make start

# 4. Access dashboards
# Kibana: http://localhost:5601
# Grafana: http://localhost:3000
# Spark UI: http://localhost:8080
# Jupyter: http://localhost:8888

# 5. Run tests
make test
```

---

**Next Steps**: Bắt đầu implement từ Phase 1 trong PLANMODE.md
