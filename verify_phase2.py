"""
Phase 2 Verification Script
Comprehensive testing for Data Ingestion Layer
"""
import sys
import os
import time
from kafka import KafkaConsumer, KafkaProducer, KafkaAdminClient
from kafka.admin import NewTopic
from kafka.errors import TopicAlreadyExistsError
import json

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

class Phase2Verifier:
    """Verify Phase 2: Data Ingestion Layer"""
    
    def __init__(self):
        self.kafka_servers = 'localhost:29092'
        self.topic = 'lol_matches'
        self.test_results = []
    
    def print_header(self, text):
        """Print formatted header"""
        print(f"\n{BLUE}{'='*60}{RESET}")
        print(f"{BLUE}{text:^60}{RESET}")
        print(f"{BLUE}{'='*60}{RESET}")
    
    def print_test(self, name, passed, message=""):
        """Print test result"""
        status = f"{GREEN}✓ PASS{RESET}" if passed else f"{RED}✗ FAIL{RESET}"
        print(f"{status} - {name}")
        if message:
            print(f"      {message}")
        self.test_results.append((name, passed))
    
    def test_kafka_connection(self):
        """Test 1: Kafka connection"""
        self.print_header("TEST 1: Kafka Connection")
        
        try:
            producer = KafkaProducer(
                bootstrap_servers=self.kafka_servers,
                request_timeout_ms=5000
            )
            producer.close()
            self.print_test("Kafka connection", True, 
                          f"Connected to {self.kafka_servers}")
            return True
        except Exception as e:
            self.print_test("Kafka connection", False, str(e))
            return False
    
    def test_topic_exists(self):
        """Test 2: Topic existence"""
        self.print_header("TEST 2: Topic Configuration")
        
        try:
            admin = KafkaAdminClient(bootstrap_servers=self.kafka_servers)
            topics = admin.list_topics()
            
            if self.topic in topics:
                self.print_test("Topic exists", True, 
                              f"Topic '{self.topic}' found")
                
                # Check partitions using admin client metadata
                cluster_metadata = admin._client.cluster
                topic_metadata = cluster_metadata.topics()
                
                if self.topic in topic_metadata:
                    partitions = cluster_metadata.partitions_for_topic(self.topic)
                    if partitions:
                        self.print_test("Topic partitions", True, 
                                      f"Partitions: {len(partitions)}")
                    else:
                        self.print_test("Topic partitions", False, 
                                      "No partitions found")
                
                admin.close()
                return True
            else:
                self.print_test("Topic exists", False, 
                              f"Topic '{self.topic}' not found")
                admin.close()
                return False
                
        except Exception as e:
            self.print_test("Topic configuration", False, str(e))
            return False
    
    def test_producer_send(self):
        """Test 3: Producer can send messages"""
        self.print_header("TEST 3: Producer Functionality")
        
        try:
            producer = KafkaProducer(
                bootstrap_servers=self.kafka_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            
            # Send test message
            test_data = {
                'test': True,
                'timestamp': int(time.time()),
                'message': 'Phase 2 verification test'
            }
            
            future = producer.send(self.topic, test_data)
            result = future.get(timeout=10)
            
            producer.close()
            
            self.print_test("Producer send message", True,
                          f"Message sent to partition {result.partition}")
            return True
            
        except Exception as e:
            self.print_test("Producer send message", False, str(e))
            return False
    
    def test_consumer_receive(self):
        """Test 4: Consumer can receive messages"""
        self.print_header("TEST 4: Consumer Functionality")
        
        try:
            consumer = KafkaConsumer(
                self.topic,
                bootstrap_servers=self.kafka_servers,
                auto_offset_reset='earliest',
                consumer_timeout_ms=5000,
                value_deserializer=lambda m: json.loads(m.decode('utf-8'))
            )
            
            message_count = 0
            for message in consumer:
                message_count += 1
                if message_count >= 1:  # Read at least 1 message
                    break
            
            consumer.close()
            
            if message_count > 0:
                self.print_test("Consumer receive message", True,
                              f"Received {message_count} message(s)")
                return True
            else:
                self.print_test("Consumer receive message", False,
                              "No messages received")
                return False
                
        except Exception as e:
            self.print_test("Consumer receive message", False, str(e))
            return False
    
    def test_generator_module(self):
        """Test 5: Generator module can be imported"""
        self.print_header("TEST 5: Generator Module")
        
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 
                                           'data-generator'))
            from src.generator import MatchGenerator
            
            self.print_test("Import MatchGenerator", True,
                          "Module imported successfully")
            
            # Test config loading
            try:
                generator = MatchGenerator()
                self.print_test("Generator initialization", True,
                              "Generator initialized with config")
                return True
            except Exception as e:
                self.print_test("Generator initialization", False, str(e))
                return False
                
        except Exception as e:
            self.print_test("Import MatchGenerator", False, str(e))
            return False
    
    def test_match_data_format(self):
        """Test 6: Generated match data format"""
        self.print_header("TEST 6: Match Data Format")
        
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 
                                           'data-generator'))
            from src.generator import MatchGenerator
            
            generator = MatchGenerator()
            match_data = generator.generate_match()
            
            # Check structure
            checks = [
                ('metadata' in match_data, "Has 'metadata' field"),
                ('info' in match_data, "Has 'info' field"),
                ('matchId' in match_data.get('metadata', {}), "Has matchId"),
                (len(match_data.get('info', {}).get('participants', [])) == 10, 
                 "Has 10 participants"),
                (len(match_data.get('info', {}).get('teams', [])) == 2, 
                 "Has 2 teams"),
            ]
            
            all_passed = True
            for check, desc in checks:
                self.print_test(desc, check)
                if not check:
                    all_passed = False
            
            return all_passed
            
        except Exception as e:
            self.print_test("Match data format", False, str(e))
            return False
    
    def test_end_to_end(self):
        """Test 7: End-to-end data flow"""
        self.print_header("TEST 7: End-to-End Data Flow")
        
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 
                                           'data-generator'))
            from src.generator import MatchGenerator
            
            # First, create consumer and seek to end to get current offset
            consumer = KafkaConsumer(
                self.topic,
                bootstrap_servers=self.kafka_servers,
                auto_offset_reset='latest',
                consumer_timeout_ms=5000,
                value_deserializer=lambda m: json.loads(m.decode('utf-8'))
            )
            
            # Consume any existing messages to move to end
            for _ in consumer:
                pass
            
            # Now generate and send new message
            generator = MatchGenerator()
            match_data = generator.generate_match()
            success = generator.send_match(match_data)
            
            if not success:
                consumer.close()
                self.print_test("Send match data", False, "Failed to send")
                return False
            
            self.print_test("Send match data", True, 
                          f"Sent: {match_data['metadata']['matchId']}")
            
            # Wait for message to be committed
            time.sleep(2)
            
            # Now try to receive the specific message we just sent
            received = False
            message_count = 0
            for message in consumer:
                message_count += 1
                if message.value.get('metadata', {}).get('matchId') == match_data['metadata']['matchId']:
                    received = True
                    break
                if message_count > 10:  # Don't loop forever
                    break
            
            consumer.close()
            generator.producer.close()
            
            self.print_test("Receive match data", received,
                          f"Verified match in Kafka (checked {message_count} message(s))")
            
            return success and received
            
        except Exception as e:
            self.print_test("End-to-end flow", False, str(e))
            return False
    
    def run_all_tests(self):
        """Run all verification tests"""
        print(f"\n{YELLOW}{'*'*60}{RESET}")
        print(f"{YELLOW}{'PHASE 2 VERIFICATION - DATA INGESTION LAYER':^60}{RESET}")
        print(f"{YELLOW}{'*'*60}{RESET}")
        
        tests = [
            self.test_kafka_connection,
            self.test_topic_exists,
            self.test_producer_send,
            self.test_consumer_receive,
            self.test_generator_module,
            self.test_match_data_format,
            self.test_end_to_end,
        ]
        
        for test in tests:
            test()
            time.sleep(0.5)
        
        # Summary
        self.print_header("SUMMARY")
        passed = sum(1 for _, result in self.test_results if result)
        total = len(self.test_results)
        
        print(f"\nTotal Tests: {total}")
        print(f"{GREEN}Passed: {passed}{RESET}")
        print(f"{RED}Failed: {total - passed}{RESET}")
        
        if passed == total:
            print(f"\n{GREEN}{'='*60}{RESET}")
            print(f"{GREEN}{'✓ PHASE 2 VERIFICATION PASSED':^60}{RESET}")
            print(f"{GREEN}{'='*60}{RESET}")
            print(f"\n{GREEN}✓ Data Ingestion Layer is working correctly!{RESET}")
            print(f"{GREEN}✓ Ready to proceed to Phase 3: Streaming Layer{RESET}\n")
            return True
        else:
            print(f"\n{RED}{'='*60}{RESET}")
            print(f"{RED}{'✗ PHASE 2 VERIFICATION FAILED':^60}{RESET}")
            print(f"{RED}{'='*60}{RESET}")
            print(f"\n{RED}✗ Please fix the issues above before proceeding{RESET}\n")
            return False


if __name__ == '__main__':
    verifier = Phase2Verifier()
    success = verifier.run_all_tests()
    sys.exit(0 if success else 1)
