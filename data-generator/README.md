# LoL Match Data Generator

Generate realistic League of Legends match data in Riot API v2 format for Big Data pipeline testing.

## Features

- ✅ Riot API v2 compatible format
- ✅ 36 champion pool
- ✅ Realistic match statistics (kills, deaths, assists, gold, damage, CS, vision)
- ✅ Configurable generation rate
- ✅ Continuous and batch modes
- ✅ Kafka producer integration
- ✅ Comprehensive logging
- ✅ Unit tests included

## Installation

```bash
# Install dependencies (from project root)
pip install -r requirements.txt
```

## Configuration

Edit `config/config.yaml` to customize:

```yaml
kafka:
  bootstrap_servers: "localhost:29092"
  topic: "lol_matches"

generator:
  interval_seconds: 0.5 # 2 matches/second
  mode: "continuous"
```

## Usage

### Quick Start (Continuous Mode)

```bash
# From data-generator directory
python src/generator.py
```

### Batch Mode

```bash
# Generate 50 matches
python src/generator.py --mode batch --batch-size 50
```

### Custom Config

```bash
python src/generator.py --config /path/to/config.yaml
```

### As Python Module

```python
from src.generator import MatchGenerator

# Initialize
generator = MatchGenerator()

# Generate single match
match_data = generator.generate_match()

# Send to Kafka
generator.send_match(match_data)

# Run continuous
generator.run_continuous()

# Run batch
generator.run_batch(batch_size=100)
```

## Generated Data Format

```json
{
  "metadata": {
    "matchId": "SEA_1234567890",
    "participants": ["puuid_0", "puuid_1", ...]
  },
  "info": {
    "gameId": 1234567890,
    "platformId": "SEA",
    "gameCreation": 1704980000000,
    "gameDuration": 1800,
    "participants": [
      {
        "puuid": "puuid_0",
        "summonerName": "Faker",
        "championName": "Ahri",
        "teamPosition": "MIDDLE",
        "teamId": 100,
        "win": true,
        "kills": 10,
        "deaths": 2,
        "assists": 15,
        "goldEarned": 15000,
        ...
      }
    ],
    "teams": [
      {"teamId": 100, "win": true},
      {"teamId": 200, "win": false}
    ]
  }
}
```

## Testing

```bash
# Run unit tests
cd tests
python -m pytest test_generator.py -v

# Or use pytest from project root
pytest data-generator/tests/ -v
```

## Logging

Logs are written to `logs/generator.log` and console.

Configure log level in `config/config.yaml`:

```yaml
logging:
  level: "INFO" # DEBUG, INFO, WARNING, ERROR
```

## Project Structure

```
data-generator/
├── src/
│   ├── __init__.py
│   └── generator.py         # Main generator module
├── config/
│   └── config.yaml          # Configuration file
├── tests/
│   └── test_generator.py    # Unit tests
├── logs/                    # Log files (auto-created)
└── README.md
```

## Requirements

- Python 3.9+
- kafka-python 2.0.2
- PyYAML 6.0.1
- Running Kafka cluster

## Next Steps

1. ✅ Phase 2 Complete: Data generation working
2. → Phase 3: Build Spark Streaming consumer
3. → Phase 4: Implement batch processing layer

## Troubleshooting

### Connection Refused

```bash
# Check Kafka is running
docker ps | grep kafka

# Verify port in config
# Use 29092 for external (host) connections
# Use 9092 for internal (container) connections
```

### No Messages Received

```bash
# Check topic exists
docker exec kafka kafka-topics --bootstrap-server localhost:9092 --list

# Consume messages manually
docker exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic lol_matches \
  --from-beginning
```

---

_Part of Big Data LoL Analysis System - Phase 2_
