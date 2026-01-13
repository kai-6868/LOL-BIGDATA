```
                            LoL Match Generator
                         (lol_match_generator.py)
                                   │
                                   ↓
                        ┌──────────────────────┐
                        │   KAFKA CLUSTER      │
                        │   Topic: lol_matches │
                        │   (3 partitions)     │
                        └──────────┬───────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
                    ↓                             ↓
    ╔═══════════════════════════╗   ╔═══════════════════════════╗
    ║  LUỒNG 1: STREAMING       ║   ║  LUỒNG 2: BATCHING        ║
    ║  (Real-time)              ║   ║  (Historical + ML)        ║
    ╚═══════════════════════════╝   ╚═══════════════════════════╝
                    │                             │
                    ↓                             ↓
        ┌─────────────────────┐      ┌─────────────────────┐
        │  Spark Streaming    │      │  Batch Consumer     │
        │  (30s batches)      │      │  (50 msg/batch)     │
        │                     │      │                     │
        │ • Read Kafka        │      │ • Read Kafka        │
        │ • Window 5min       │      │ • Save to HDFS      │
        │ • Win rate calc     │      │                     │
        └──────────┬──────────┘      └──────────┬──────────┘
                   │                             │
                   ↓                             ↓
        ┌─────────────────────┐      ┌─────────────────────┐
        │  ELASTICSEARCH      │      │  HDFS Storage       │
        │  (Search Engine)    │      │  /data/lol_matches/ │
        │                     │      │                     │
        │ • Index: lol_stream │      │ • JSON batches      │
        │ • Real-time index   │      │ • /YYYY/MM/DD/      │
        └──────────┬──────────┘      └──────────┬──────────┘
                   │                             │
                   ↓                             ↓
        ┌─────────────────────┐      ┌─────────────────────┐
        │  KIBANA             │      │ Batch Processing    │
        │  (Visualization)    │      │ (PySpark)           │
        │                     │      │                     │
        │ • Dashboard         │      │ • Read HDFS         │
        │ • Live charts       │      │ • Flatten JSON      │
        │ • Win rate by champ │      │ • Transform data    │
        │ • Time series       │      └──────────┬──────────┘
        └─────────────────────┘                 │
                                                 ↓
                                      ┌─────────────────────┐
                                      │  CASSANDRA DB       │
                                      │  (NoSQL)            │
                                      │                     │
                                      │ • Keyspace: lol_data│
                                      │ • Table: match_part │
                                      └──────────┬──────────┘
                                                 │
                                                 ↓
                                      ┌─────────────────────┐
                                      │  ML PREDICTION      │
                                      │  (Random Forest)    │
                                      │                     │
                                      │ • Feature engineer  │
                                      │ • Train model       │
                                      │ • Win rate predict  │
                                      │ • Feature importance│
                                      └─────────────────────┘
```