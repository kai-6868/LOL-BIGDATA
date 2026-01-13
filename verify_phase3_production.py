"""
Phase 3 - Production Deployment Verification Script
===================================================
Comprehensive verification for Spark Streaming pipeline in production.

This script verifies:
1. All Docker services are running
2. Kafka topic properly configured
3. Spark Application UI accessible
4. Elasticsearch receiving documents
5. End-to-end pipeline functioning
"""

import sys
import time
import requests
from datetime import datetime

def print_header(title):
    """Print section header"""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print('=' * 70)

def print_result(success, message):
    """Print test result"""
    status = "✓" if success else "✗"
    print(f"{status} {message}")
    return success

def check_spark_ui():
    """Check Spark Application UI accessibility"""
    print_header("TEST 1: Spark Application UI")
    
    try:
        # Test port 4040
        response = requests.get("http://localhost:4040", timeout=5)
        if response.status_code == 200 and "Spark" in response.text:
            print_result(True, "Spark Application UI accessible at http://localhost:4040")
            return True
        else:
            print_result(False, f"Unexpected response from port 4040: {response.status_code}")
            
            # Try port 4041
            response = requests.get("http://localhost:4041", timeout=5)
            if response.status_code == 200:
                print_result(True, "Spark Application UI accessible at http://localhost:4041")
                return True
                
    except requests.exceptions.ConnectionError:
        print_result(False, "Cannot connect to Spark UI (ports 4040/4041)")
        print("  → Ensure Spark job is running: .\\submit_spark_job.ps1")
        return False
    except Exception as e:
        print_result(False, f"Error checking Spark UI: {e}")
        return False
    
    return False

def check_spark_master():
    """Check Spark Master UI"""
    print_header("TEST 2: Spark Master UI")
    
    try:
        response = requests.get("http://localhost:8080", timeout=5)
        if response.status_code == 200:
            print_result(True, "Spark Master UI accessible at http://localhost:8080")
            
            # Check for running applications
            if "Running Applications" in response.text:
                print_result(True, "Running Applications section visible")
                return True
            else:
                print_result(False, "No running applications found")
                return False
        else:
            print_result(False, f"Cannot access Spark Master UI: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print_result(False, "Cannot connect to Spark Master UI (port 8080)")
        print("  → Check: docker compose ps spark-master")
        return False
    except Exception as e:
        print_result(False, f"Error checking Spark Master: {e}")
        return False

def check_elasticsearch_docs():
    """Check Elasticsearch document count"""
    print_header("TEST 3: Elasticsearch Document Count")
    
    try:
        # First check
        response1 = requests.get("http://localhost:9200/lol_matches_stream/_count", timeout=5)
        if response1.status_code == 200:
            count1 = response1.json()["count"]
            print_result(True, f"Initial document count: {count1}")
            
            if count1 == 0:
                print_result(False, "No documents indexed yet")
                print("  → Wait for Spark job to process batches")
                return False
            
            # Wait and check again
            print("\n  Waiting 10 seconds to verify continuous indexing...")
            time.sleep(10)
            
            response2 = requests.get("http://localhost:9200/lol_matches_stream/_count", timeout=5)
            count2 = response2.json()["count"]
            print_result(True, f"Document count after 10s: {count2}")
            
            if count2 > count1:
                increase = count2 - count1
                print_result(True, f"Documents increased by {increase} (continuous indexing working)")
                return True
            else:
                print_result(False, "Document count not increasing")
                print("  → Check Spark logs: docker logs spark-master --tail 50")
                return False
        else:
            print_result(False, f"Cannot access Elasticsearch: {response1.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print_result(False, "Cannot connect to Elasticsearch (port 9200)")
        print("  → Check: docker compose ps elasticsearch")
        return False
    except Exception as e:
        print_result(False, f"Error checking Elasticsearch: {e}")
        return False

def check_kafka_topic():
    """Check Kafka topic exists (via container exec)"""
    print_header("TEST 4: Kafka Topic Configuration")
    
    import subprocess
    
    try:
        # Check topic exists
        result = subprocess.run(
            ["docker", "exec", "kafka", "kafka-topics", 
             "--bootstrap-server", "localhost:9092", 
             "--list"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0 and "lol_matches" in result.stdout:
            print_result(True, "Topic 'lol_matches' exists")
            
            # Get topic details
            result = subprocess.run(
                ["docker", "exec", "kafka", "kafka-topics",
                 "--bootstrap-server", "localhost:9092",
                 "--describe", "--topic", "lol_matches"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if "PartitionCount: 3" in result.stdout:
                print_result(True, "Topic has 3 partitions (correct)")
                return True
            else:
                print_result(False, "Topic partition count incorrect")
                return False
        else:
            print_result(False, "Topic 'lol_matches' not found")
            print("  → Create topic: docker exec kafka kafka-topics --create ...")
            return False
            
    except subprocess.TimeoutExpired:
        print_result(False, "Timeout executing Kafka command")
        return False
    except FileNotFoundError:
        print_result(False, "Docker command not found (is Docker installed?)")
        return False
    except Exception as e:
        print_result(False, f"Error checking Kafka topic: {e}")
        return False

def check_es_index_health():
    """Check Elasticsearch index health"""
    print_header("TEST 5: Elasticsearch Index Health")
    
    try:
        # Check index exists
        response = requests.get("http://localhost:9200/lol_matches_stream", timeout=5)
        if response.status_code == 200:
            print_result(True, "Index 'lol_matches_stream' exists")
            
            # Check index stats
            response = requests.get("http://localhost:9200/lol_matches_stream/_stats", timeout=5)
            if response.status_code == 200:
                stats = response.json()
                shards = stats["_shards"]
                
                if shards["failed"] == 0:
                    print_result(True, f"All shards healthy: {shards['successful']}/{shards['total']}")
                    return True
                else:
                    print_result(False, f"Failed shards: {shards['failed']}")
                    return False
            else:
                print_result(False, "Cannot retrieve index stats")
                return False
        else:
            print_result(False, "Index 'lol_matches_stream' not found")
            print("  → Run: python verify_phase3.py (to create index)")
            return False
            
    except Exception as e:
        print_result(False, f"Error checking index health: {e}")
        return False

def main():
    """Main verification workflow"""
    print("\n" + "=" * 70)
    print("  PHASE 3 PRODUCTION DEPLOYMENT VERIFICATION")
    print("  Spark Streaming Pipeline - End-to-End Check")
    print("=" * 70)
    print(f"\nTimestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    
    # Run all tests
    results.append(("Kafka Topic", check_kafka_topic()))
    results.append(("Elasticsearch Index", check_es_index_health()))
    results.append(("Spark Master UI", check_spark_master()))
    results.append(("Spark Application UI", check_spark_ui()))
    results.append(("Elasticsearch Docs", check_elasticsearch_docs()))
    
    # Summary
    print_header("VERIFICATION SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:10} {test_name}")
    
    print(f"\n{'=' * 70}")
    print(f"Results: {passed}/{total} tests passed")
    print('=' * 70)
    
    if passed == total:
        print("\n✓ Phase 3 production deployment verified successfully!")
        print("\nAccess points:")
        print("  - Spark Application UI: http://localhost:4040")
        print("  - Spark Master UI: http://localhost:8080")
        print("  - Elasticsearch API: http://localhost:9200")
        print("\nPipeline: Generator → Kafka → Spark → Elasticsearch ✓")
        return 0
    else:
        print("\n✗ Some tests failed. Check logs and troubleshooting guide.")
        print("\nCommon fixes:")
        print("  1. Restart services: docker compose restart")
        print("  2. Clear checkpoints: Remove-Item .\\checkpoints\\streaming\\*")
        print("  3. Resubmit job: .\\submit_spark_job.ps1")
        print("\nFull troubleshooting: SPARK_TROUBLESHOOTING.md")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nVerification interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        sys.exit(1)
