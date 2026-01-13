"""
Phase 3 Verification Script - Streaming Layer
Comprehensive testing for Spark Streaming pipeline
"""

import sys
import time
import json
from datetime import datetime
from kafka import KafkaProducer, KafkaConsumer
from elasticsearch import Elasticsearch
import requests

# Test counters
tests_passed = 0
tests_failed = 0


def print_test_header(test_num, test_name):
    """Print test header"""
    print(f"\n{'=' * 60}")
    print(f"TEST {test_num}: {test_name}")
    print('=' * 60)


def print_result(success, message):
    """Print test result"""
    global tests_passed, tests_failed
    
    if success:
        tests_passed += 1
        print(f"✓ {message}")
    else:
        tests_failed += 1
        print(f"✗ {message}")
    
    return success


# ==============================================================================
# TEST 1: Verify Elasticsearch Connection
# ==============================================================================
def test_elasticsearch_connection():
    """Test Elasticsearch connection and health"""
    print_test_header(1, "Elasticsearch Connection & Health")
    
    try:
        # Connect to Elasticsearch
        es = Elasticsearch(
            hosts=["http://localhost:9200"],
            verify_certs=False,
            request_timeout=10
        )
        
        # Check connection
        if not es.ping():
            return print_result(False, "Cannot ping Elasticsearch")
        
        print_result(True, "Connected to Elasticsearch")
        
        # Check cluster health
        health = es.cluster.health()
        status = health['status']
        print_result(True, f"Cluster health: {status}")
        
        # Check if status is green or yellow
        if status in ['green', 'yellow']:
            print_result(True, "Cluster is operational")
            return True
        else:
            return print_result(False, f"Cluster status is {status}")
        
    except Exception as e:
        return print_result(False, f"Elasticsearch connection failed: {e}")


# ==============================================================================
# TEST 2: Verify ES Index Creation
# ==============================================================================
def test_elasticsearch_index():
    """Test Elasticsearch index creation with mapping"""
    print_test_header(2, "Elasticsearch Index Setup")
    
    try:
        # Import indexer
        sys.path.insert(0, 'streaming-layer/src')
        from elasticsearch_indexer import ElasticsearchIndexer
        
        # Create indexer
        indexer = ElasticsearchIndexer(
            hosts=["http://localhost:9200"],
            index_name="lol_matches_stream",
            mapping_file="streaming-layer/config/es_mapping.json"
        )
        
        print_result(True, "ElasticsearchIndexer initialized")
        
        # Check if index exists
        if indexer.index_exists():
            print_result(True, "Index 'lol_matches_stream' exists")
        else:
            return print_result(False, "Index does not exist")
        
        # Get index mapping
        mapping = indexer.es.indices.get_mapping(index=indexer.index_name)
        properties = mapping[indexer.index_name]['mappings']['properties']
        
        # Check required fields
        required_fields = [
            'match_id', 'timestamp', 'champion_name', 'position',
            'kills', 'deaths', 'assists', 'kda', 'win'
        ]
        
        missing_fields = [f for f in required_fields if f not in properties]
        
        if missing_fields:
            return print_result(False, f"Missing fields in mapping: {missing_fields}")
        
        print_result(True, f"All required fields present in mapping ({len(required_fields)} fields)")
        
        indexer.close()
        return True
        
    except Exception as e:
        return print_result(False, f"Index verification failed: {e}")


# ==============================================================================
# TEST 3: Test ES Indexing Functionality
# ==============================================================================
def test_elasticsearch_indexing():
    """Test Elasticsearch document indexing"""
    print_test_header(3, "Elasticsearch Indexing")
    
    try:
        sys.path.insert(0, 'streaming-layer/src')
        from elasticsearch_indexer import ElasticsearchIndexer
        
        # Create indexer
        indexer = ElasticsearchIndexer(
            hosts=["http://localhost:9200"],
            index_name="lol_matches_stream",
            mapping_file="streaming-layer/config/es_mapping.json"
        )
        
        # Test document
        test_doc = {
            "match_id": "VERIFY_TEST_001",
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
        
        # Index document
        success = indexer.index_document(test_doc)
        
        if not success:
            indexer.close()
            return print_result(False, "Failed to index test document")
        
        print_result(True, "Single document indexed successfully")
        
        # Refresh index to make document searchable
        indexer.refresh_index()
        
        # Wait a bit for indexing
        time.sleep(1)
        
        # Search for the document
        es = indexer.es
        search_result = es.search(
            index=indexer.index_name,
            body={
                "query": {
                    "match": {
                        "match_id": "VERIFY_TEST_001"
                    }
                }
            }
        )
        
        hits = search_result['hits']['total']['value']
        
        if hits > 0:
            print_result(True, f"Document found in index (hits: {hits})")
        else:
            indexer.close()
            return print_result(False, "Document not found after indexing")
        
        # Test bulk indexing
        bulk_docs = [
            {**test_doc, "match_id": f"VERIFY_TEST_{i:03d}"}
            for i in range(2, 6)
        ]
        
        success_count, failed_count = indexer.bulk_index(bulk_docs)
        
        if success_count == len(bulk_docs) and failed_count == 0:
            print_result(True, f"Bulk indexed {success_count} documents")
        else:
            indexer.close()
            return print_result(False, f"Bulk indexing failed: {success_count} success, {failed_count} failed")
        
        indexer.close()
        return True
        
    except Exception as e:
        return print_result(False, f"Indexing test failed: {e}")


# ==============================================================================
# TEST 4: Verify Kafka-Spark Integration
# ==============================================================================
def test_kafka_connection():
    """Test Kafka connection for Spark consumer"""
    print_test_header(4, "Kafka Connection for Spark")
    
    try:
        # Test producer connection
        producer = KafkaProducer(
            bootstrap_servers=['localhost:29092'],
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        
        print_result(True, "Kafka producer connected")
        
        # Test consumer connection
        consumer = KafkaConsumer(
            'lol_matches',
            bootstrap_servers=['localhost:29092'],
            auto_offset_reset='latest',
            consumer_timeout_ms=1000
        )
        
        print_result(True, "Kafka consumer connected")
        
        # Check topic
        topics = consumer.topics()
        if 'lol_matches' in topics:
            print_result(True, "Topic 'lol_matches' exists")
        else:
            consumer.close()
            producer.close()
            return print_result(False, "Topic 'lol_matches' not found")
        
        consumer.close()
        producer.close()
        return True
        
    except Exception as e:
        return print_result(False, f"Kafka connection failed: {e}")


# ==============================================================================
# TEST 5: Verify Configuration Files
# ==============================================================================
def test_configuration_files():
    """Test configuration files exist and are valid"""
    print_test_header(5, "Configuration Files")
    
    try:
        import os
        
        # Check spark_config.yaml
        config_file = "streaming-layer/config/spark_config.yaml"
        if not os.path.exists(config_file):
            return print_result(False, f"Config file not found: {config_file}")
        
        # Try to import yaml, if not available, skip YAML parsing
        try:
            import yaml
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            print_result(True, "spark_config.yaml exists and is valid YAML")
            
            # Check required sections
            required_sections = ['spark', 'kafka', 'streaming', 'elasticsearch']
            for section in required_sections:
                if section not in config:
                    return print_result(False, f"Missing section in config: {section}")
            
            print_result(True, f"All required config sections present ({len(required_sections)} sections)")
            
        except ImportError:
            # YAML not available, just check file exists
            print_result(True, "spark_config.yaml exists (YAML parsing skipped)")
            with open(config_file, 'r') as f:
                content = f.read()
                if 'spark:' in content and 'kafka:' in content:
                    print_result(True, "Config file has expected sections")
                else:
                    return print_result(False, "Config file missing required sections")
        
        # Check es_mapping.json
        mapping_file = "streaming-layer/config/es_mapping.json"
        if not os.path.exists(mapping_file):
            return print_result(False, f"Mapping file not found: {mapping_file}")
        
        with open(mapping_file, 'r') as f:
            mapping = json.load(f)
        
        print_result(True, "es_mapping.json exists and is valid JSON")
        
        # Check mapping structure
        if 'mappings' in mapping and 'properties' in mapping['mappings']:
            print_result(True, "Mapping has correct structure")
        else:
            return print_result(False, "Invalid mapping structure")
        
        return True
        
    except Exception as e:
        return print_result(False, f"Configuration test failed: {e}")


# ==============================================================================
# TEST 6: Verify Module Imports
# ==============================================================================
def test_module_imports():
    """Test that all streaming modules can be imported"""
    print_test_header(6, "Module Imports")
    
    try:
        sys.path.insert(0, 'streaming-layer/src')
        
        # Test elasticsearch_indexer
        from elasticsearch_indexer import ElasticsearchIndexer
        print_result(True, "Imported ElasticsearchIndexer")
        
        # Test processors
        from processors import (
            parse_match_data,
            calculate_derived_metrics,
            prepare_for_elasticsearch
        )
        print_result(True, "Imported processors functions")
        
        # Test spark_streaming_consumer (only syntax check, not Spark itself)
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "spark_streaming_consumer", 
            "streaming-layer/src/spark_streaming_consumer.py"
        )
        module = importlib.util.module_from_spec(spec)
        
        # Just check file syntax without executing Spark imports
        with open("streaming-layer/src/spark_streaming_consumer.py", 'r') as f:
            code = f.read()
            compile(code, "spark_streaming_consumer.py", 'exec')
        
        print_result(True, "Spark consumer file syntax valid")
        
        return True
        
    except Exception as e:
        return print_result(False, f"Module import failed: {e}")


# ==============================================================================
# TEST 7: Verify Processors Logic
# ==============================================================================
def test_processors():
    """Test data processing functions"""
    print_test_header(7, "Data Processors")
    
    try:
        sys.path.insert(0, 'streaming-layer/src')
        from processors import prepare_for_elasticsearch
        
        # Test data
        test_row = {
            'match_id': 'TEST_123',
            'timestamp': 1234567890000,
            'game_duration': 1800,
            'participant_id': 'P1',
            'summoner_name': 'TestPlayer',
            'champion_name': 'Ahri',
            'team_id': 100,
            'position': 'MIDDLE',
            'win': True,
            'kills': 10,
            'deaths': 2,
            'assists': 15,
            'kda': 12.5,
            'total_damage_dealt': 50000,
            'gold_earned': 15000,
            'cs': 200,
            'vision_score': 30,
            'gold_per_minute': 500.0,
            'damage_per_minute': 1666.67,
            'cs_per_minute': 6.67
        }
        
        # Test prepare_for_elasticsearch
        docs = prepare_for_elasticsearch([test_row])
        
        if len(docs) == 1:
            print_result(True, "prepare_for_elasticsearch returned 1 document")
        else:
            return print_result(False, f"Expected 1 document, got {len(docs)}")
        
        # Check document structure
        doc = docs[0]
        required_fields = ['match_id', 'champion_name', 'kills', 'deaths', 'assists', 'kda']
        
        missing = [f for f in required_fields if f not in doc]
        
        if missing:
            return print_result(False, f"Missing fields in prepared document: {missing}")
        
        print_result(True, "Document has all required fields")
        
        # Check values
        if doc['match_id'] == 'TEST_123' and doc['champion_name'] == 'Ahri':
            print_result(True, "Document values are correct")
        else:
            return print_result(False, "Document values are incorrect")
        
        return True
        
    except Exception as e:
        return print_result(False, f"Processor test failed: {e}")


# ==============================================================================
# Main Execution
# ==============================================================================
def main():
    """Run all verification tests"""
    global tests_passed, tests_failed
    
    print("\n" + "=" * 60)
    print("PHASE 3 VERIFICATION - STREAMING LAYER")
    print("=" * 60)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run all tests
    test_elasticsearch_connection()
    test_elasticsearch_index()
    test_elasticsearch_indexing()
    test_kafka_connection()
    test_configuration_files()
    test_module_imports()
    test_processors()
    
    # Print summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    print(f"✓ Tests Passed: {tests_passed}")
    print(f"✗ Tests Failed: {tests_failed}")
    print(f"Total Tests: {tests_passed + tests_failed}")
    
    if tests_failed == 0:
        print("\n" + "=" * 60)
        print("✓ PHASE 3 VERIFICATION PASSED")
        print("✓ Streaming Layer is properly configured!")
        print("✓ Ready to start Spark Streaming consumer")
        print("=" * 60)
        return 0
    else:
        print("\n" + "=" * 60)
        print("✗ PHASE 3 VERIFICATION FAILED")
        print(f"✗ {tests_failed} test(s) failed")
        print("✗ Please fix the issues before proceeding")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
