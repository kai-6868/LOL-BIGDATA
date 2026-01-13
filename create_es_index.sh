#!/bin/bash
# create_es_index.sh
# Create Elasticsearch Index for LoL Streaming Data

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

echo ""
echo "Verifying index..."
curl http://localhost:9200/lol_stream
