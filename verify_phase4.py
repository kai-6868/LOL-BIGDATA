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
        
        import yaml
        print("  ✅ pyyaml")
        
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
            
            # Check for actual data
            try:
                files = client.list('/data/lol_matches/2026/01/13')
                print(f"  ✅ Found {len(files)} file(s) in today's partition")
            except:
                print("  ⚠️ No data in today's partition yet")
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
                # Check record count
                count_result = session.execute(f"SELECT COUNT(*) FROM {table};")
                count = count_result.one()[0]
                print(f"  ✅ Table '{table}' exists ({count} records)")
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
        'batch-layer/src/pyspark_etl_docker.py',
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


def test_spark_container():
    """Test Spark container and ETL setup"""
    print("\n8️⃣ Testing Spark Container Setup...")
    
    import subprocess
    
    try:
        # Check Spark container
        result = subprocess.run(['docker', 'ps', '--filter', 'name=spark-master', '--format', '{{.Names}}'],
                              capture_output=True, text=True, timeout=5)
        if 'spark-master' in result.stdout:
            print("  ✅ Spark container running")
        else:
            print("  ❌ Spark container not found")
            return False
        
        # Check spark-submit exists
        result = subprocess.run(['docker', 'exec', 'spark-master', 'which', 'spark-submit'],
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"  ✅ spark-submit found: {result.stdout.strip()}")
        else:
            print("  ❌ spark-submit not found")
            return False
        
        # Check PyYAML installed
        result = subprocess.run(['docker', 'exec', 'spark-master', 'python', '-c', 'import yaml; print(yaml.__version__)'],
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"  ✅ PyYAML installed: {result.stdout.strip()}")
        else:
            print("  ⚠️ PyYAML not installed - run: docker exec -u root spark-master pip install pyyaml")
        
        # Check Ivy cache directory
        result = subprocess.run(['docker', 'exec', 'spark-master', 'test', '-d', '/home/spark/.ivy2/cache'],
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("  ✅ Ivy cache directory exists")
        else:
            print("  ⚠️ Ivy cache not configured")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Spark container test failed: {e}")
        return False


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
        ("Directory Structure", test_directory_structure),
        ("Spark Container Setup", test_spark_container)
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
        print("\n✅ Phase 4 Batch Layer: FULLY OPERATIONAL!")
        print("\n📋 Next Steps:")
        print("  1. Schedule ETL jobs (cron/airflow)")
        print("  2. Monitor HDFS storage usage")
        print("  3. Query Cassandra for analytics")
        print("  4. Proceed to Phase 5 - ML Layer")
        return 0
    elif passed >= total - 2:
        print("\n⚠️ Phase 4 mostly working - minor issues to fix")
        return 0
    else:
        print("\n⚠️ Some critical tests failed - fix issues before proceeding")
        return 1


if __name__ == '__main__':
    sys.exit(main())
