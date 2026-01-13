# Makefile for LoL Big Data System

.PHONY: help setup start stop restart logs clean test

# Default target
.DEFAULT_GOAL := help

# Colors for output
GREEN  := $(shell tput -Txterm setaf 2)
YELLOW := $(shell tput -Txterm setaf 3)
WHITE  := $(shell tput -Txterm setaf 7)
RESET  := $(shell tput -Txterm sgr0)

## Help
help:
	@echo ''
	@echo '${GREEN}LoL Big Data System - Makefile Commands${RESET}'
	@echo ''
	@echo 'Usage:'
	@echo '  ${YELLOW}make${RESET} ${GREEN}<target>${RESET}'
	@echo ''
	@echo 'Targets:'
	@echo '  ${YELLOW}setup${RESET}          - Setup project (first time)'
	@echo '  ${YELLOW}start-all${RESET}      - Start all services'
	@echo '  ${YELLOW}stop-all${RESET}       - Stop all services'
	@echo '  ${YELLOW}restart${RESET}        - Restart all services'
	@echo '  ${YELLOW}logs${RESET}           - View all logs'
	@echo '  ${YELLOW}status${RESET}         - Check services status'
	@echo '  ${YELLOW}clean${RESET}          - Clean up Docker volumes'
	@echo '  ${YELLOW}test${RESET}           - Run tests'
	@echo '  ${YELLOW}format${RESET}         - Format Python code'
	@echo '  ${YELLOW}lint${RESET}           - Lint Python code'
	@echo ''

## Setup: First time setup
setup:
	@echo "${GREEN}Setting up project...${RESET}"
	@echo "${YELLOW}Creating virtual environment...${RESET}"
	python -m venv venv
	@echo "${YELLOW}Activating virtual environment and installing dependencies...${RESET}"
	. venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt
	@echo "${YELLOW}Creating directories...${RESET}"
	mkdir -p data/{raw,processed,models}
	mkdir -p logs
	mkdir -p checkpoints
	@echo "${GREEN}Setup complete!${RESET}"

## Docker: Start all Docker services
start-all:
	@echo "${GREEN}Starting all services...${RESET}"
	docker-compose up -d
	@echo "${YELLOW}Waiting for services to be ready...${RESET}"
	sleep 30
	@echo "${YELLOW}Creating Kafka topics...${RESET}"
	bash scripts/create_topics.sh
	@echo "${YELLOW}Initializing Cassandra schema...${RESET}"
	bash scripts/init_cassandra.sh
	@echo "${YELLOW}Creating Elasticsearch index...${RESET}"
	bash scripts/create_es_index.sh
	@echo "${GREEN}All services started!${RESET}"
	@make status

## Docker: Stop all services
stop-all:
	@echo "${YELLOW}Stopping all services...${RESET}"
	docker-compose down
	@echo "${GREEN}All services stopped!${RESET}"

## Docker: Restart all services
restart:
	@echo "${YELLOW}Restarting all services...${RESET}"
	docker-compose restart
	@echo "${GREEN}All services restarted!${RESET}"

## Docker: View logs
logs:
	docker-compose logs -f

## Docker: Check status
status:
	@echo "${GREEN}Services Status:${RESET}"
	docker-compose ps

## Docker: Clean up volumes
clean:
	@echo "${YELLOW}WARNING: This will remove all Docker volumes and data!${RESET}"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		echo "${YELLOW}Stopping services...${RESET}"; \
		docker-compose down -v; \
		echo "${YELLOW}Removing volumes...${RESET}"; \
		docker volume prune -f; \
		echo "${GREEN}Cleanup complete!${RESET}"; \
	else \
		echo "${GREEN}Cleanup cancelled.${RESET}"; \
	fi

## Testing: Run all tests
test:
	@echo "${GREEN}Running tests...${RESET}"
	. venv/bin/activate && pytest tests/ -v --cov=src --cov-report=html
	@echo "${GREEN}Tests complete! Coverage report: htmlcov/index.html${RESET}"

## Testing: Run unit tests
test-unit:
	@echo "${GREEN}Running unit tests...${RESET}"
	. venv/bin/activate && pytest tests/unit/ -v

## Testing: Run integration tests
test-integration:
	@echo "${GREEN}Running integration tests...${RESET}"
	. venv/bin/activate && pytest tests/integration/ -v

## Code Quality: Format code
format:
	@echo "${GREEN}Formatting code with Black...${RESET}"
	. venv/bin/activate && black data-generator/ streaming-layer/ batch-layer/ ml-layer/
	@echo "${GREEN}Code formatted!${RESET}"

## Code Quality: Lint code
lint:
	@echo "${GREEN}Linting code with flake8...${RESET}"
	. venv/bin/activate && flake8 data-generator/ streaming-layer/ batch-layer/ ml-layer/
	@echo "${GREEN}Linting complete!${RESET}"

## Data Generator: Start data generator
start-generator:
	@echo "${GREEN}Starting data generator...${RESET}"
	. venv/bin/activate && python data-generator/src/lol_match_generator.py

## Streaming: Start streaming layer
start-streaming:
	@echo "${GREEN}Starting streaming layer...${RESET}"
	spark-submit \
		--packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1,org.elasticsearch:elasticsearch-spark-30_2.12:8.11.0 \
		streaming-layer/src/spark_streaming_app.py

## Batch: Start batch consumer
start-batch-consumer:
	@echo "${GREEN}Starting batch consumer...${RESET}"
	. venv/bin/activate && python batch-layer/src/batch_consumer.py

## Batch: Run batch processing
run-batch-processing:
	@echo "${GREEN}Running batch processing...${RESET}"
	spark-submit \
		--packages com.datastax.spark:spark-cassandra-connector_2.12:3.4.0 \
		batch-layer/src/pyspark_processor.py

## ML: Train model
train-model:
	@echo "${GREEN}Training ML model...${RESET}"
	. venv/bin/activate && python ml-layer/src/model_training.py

## ML: Run prediction
run-prediction:
	@echo "${GREEN}Running prediction...${RESET}"
	. venv/bin/activate && python ml-layer/src/prediction_service.py

## Health: Check all services health
health:
	@echo "${GREEN}Checking services health...${RESET}"
	@echo "${YELLOW}Kafka:${RESET}"
	@docker exec kafka kafka-topics --bootstrap-server localhost:9092 --list || echo "Kafka: DOWN"
	@echo "${YELLOW}HDFS:${RESET}"
	@curl -s http://localhost:9870/jmx > /dev/null && echo "HDFS: UP" || echo "HDFS: DOWN"
	@echo "${YELLOW}Spark:${RESET}"
	@curl -s http://localhost:8080 > /dev/null && echo "Spark: UP" || echo "Spark: DOWN"
	@echo "${YELLOW}Elasticsearch:${RESET}"
	@curl -s http://localhost:9200/_cluster/health > /dev/null && echo "Elasticsearch: UP" || echo "Elasticsearch: DOWN"
	@echo "${YELLOW}Cassandra:${RESET}"
	@docker exec cassandra nodetool status > /dev/null && echo "Cassandra: UP" || echo "Cassandra: DOWN"

## Monitoring: Open dashboards
dashboards:
	@echo "${GREEN}Opening dashboards...${RESET}"
	@echo "${YELLOW}Kibana: http://localhost:5601${RESET}"
	@echo "${YELLOW}Spark UI: http://localhost:8080${RESET}"
	@echo "${YELLOW}HDFS UI: http://localhost:9870${RESET}"
	@echo "${YELLOW}Grafana: http://localhost:3000${RESET}"

## Development: Start Jupyter
jupyter:
	@echo "${GREEN}Starting Jupyter Notebook...${RESET}"
	. venv/bin/activate && jupyter notebook notebooks/

## Development: Python shell
shell:
	@echo "${GREEN}Starting Python shell...${RESET}"
	. venv/bin/activate && ipython

## Database: Cassandra shell
cqlsh:
	@echo "${GREEN}Starting Cassandra shell...${RESET}"
	docker exec -it cassandra cqlsh

## Database: Query Elasticsearch
es-query:
	@echo "${GREEN}Querying Elasticsearch...${RESET}"
	curl -X GET "http://localhost:9200/lol_stream/_search?pretty" -H "Content-Type: application/json" -d'{"query":{"match_all":{}},"size":10}'

## Kafka: View topics
kafka-topics:
	@echo "${GREEN}Kafka Topics:${RESET}"
	docker exec kafka kafka-topics --bootstrap-server localhost:9092 --list

## Kafka: Consume messages
kafka-consume:
	@echo "${GREEN}Consuming from lol_matches topic...${RESET}"
	docker exec -it kafka kafka-console-consumer \
		--bootstrap-server localhost:9092 \
		--topic lol_matches \
		--from-beginning

## HDFS: List files
hdfs-ls:
	@echo "${GREEN}HDFS Files:${RESET}"
	docker exec namenode hdfs dfs -ls /data/lol_matches/

## Backup: Backup data
backup:
	@echo "${GREEN}Backing up data...${RESET}"
	mkdir -p backups/$(shell date +%Y%m%d_%H%M%S)
	docker exec cassandra nodetool snapshot
	@echo "${GREEN}Backup complete!${RESET}"

## Deploy: Build Docker images
build:
	@echo "${GREEN}Building Docker images...${RESET}"
	docker-compose build
	@echo "${GREEN}Build complete!${RESET}"

## Deploy: Pull latest images
pull:
	@echo "${GREEN}Pulling latest images...${RESET}"
	docker-compose pull
	@echo "${GREEN}Pull complete!${RESET}"

## Maintenance: Remove old data
prune:
	@echo "${YELLOW}Pruning old data...${RESET}"
	docker system prune -f
	@echo "${GREEN}Prune complete!${RESET}"

## Documentation: Generate docs
docs:
	@echo "${GREEN}Generating documentation...${RESET}"
	. venv/bin/activate && cd docs && make html
	@echo "${GREEN}Docs generated! Open docs/_build/html/index.html${RESET}"

## CI/CD: Run pre-commit checks
pre-commit:
	@echo "${GREEN}Running pre-commit checks...${RESET}"
	@make format
	@make lint
	@make test-unit
	@echo "${GREEN}Pre-commit checks complete!${RESET}"
