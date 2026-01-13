"""
LoL Match Data Generator - Refactored Module
Generate realistic League of Legends match data in Riot API format
"""
from kafka import KafkaProducer
import json
import random
import time
import logging
from datetime import datetime
from typing import Dict, List
import yaml
import os


class MatchGenerator:
    """Generate fake LoL match data compatible with Riot API format"""
    
    def __init__(self, config_path: str = None):
        """
        Initialize Match Generator
        
        Args:
            config_path: Path to YAML config file
        """
        # Load config
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(__file__), 
                '..', 'config', 'config.yaml'
            )
        
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        # Setup logging
        self._setup_logging()
        
        # Initialize Kafka Producer
        self.producer = self._create_producer()
        
        # Data references
        self.champions = self.config['data']['champions']
        self.positions = self.config['data']['positions']
        self.summoner_names = self._generate_summoner_names()
        
        self.logger.info("MatchGenerator initialized successfully")
    
    def _setup_logging(self):
        """Configure logging"""
        log_config = self.config['logging']
        
        # Create logs directory if not exists
        log_file = log_config['file']
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        logging.basicConfig(
            level=getattr(logging, log_config['level']),
            format=log_config['format'],
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def _create_producer(self) -> KafkaProducer:
        """Create and configure Kafka Producer"""
        kafka_config = self.config['kafka']
        
        try:
            producer = KafkaProducer(
                bootstrap_servers=kafka_config['bootstrap_servers'],
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks=kafka_config['acks'],
                retries=kafka_config['retries'],
                compression_type=kafka_config['compression_type']
            )
            self.logger.info(f"Connected to Kafka: {kafka_config['bootstrap_servers']}")
            return producer
        except Exception as e:
            self.logger.error(f"Failed to connect to Kafka: {e}")
            raise
    
    def _generate_summoner_names(self) -> List[str]:
        """Generate pool of summoner names"""
        return [
            "Faker", "Dopa", "TheShy", "Rookie", "Uzi", "Caps", "Perkz", "Rekkles",
            "Doublelift", "Bjergsen", "Sneaky", "Impact", "CoreJJ", "Jensen", "Licorice",
            "Player1", "Player2", "Player3", "Player4", "Player5", "Player6", "Player7"
        ]
    
    def generate_match(self) -> Dict:
        """
        Generate a single match data
        
        Returns:
            Dict containing match metadata and info in Riot API v2 format
        """
        match_id = f"SEA_{random.randint(1000000000, 9999999999)}"
        timestamp = int(datetime.now().timestamp() * 1000)
        
        # Select 10 unique champions and summoners
        selected_champions = random.sample(self.champions, 10)
        selected_summoners = random.sample(self.summoner_names, 10)
        
        # Determine winner
        winning_team = random.choice([100, 200])
        
        # Generate 10 participants
        participants = []
        for i in range(10):
            team_id = 100 if i < 5 else 200
            won = (team_id == winning_team)
            
            participant = {
                "puuid": f"puuid_{i}",
                "summonerId": f"summoner_{i}",
                "summonerName": selected_summoners[i],
                "championName": selected_champions[i],
                "teamPosition": self.positions[i % 5],
                "teamId": team_id,
                "win": won,
                "kills": random.randint(0, 20),
                "deaths": random.randint(0, 15),
                "assists": random.randint(0, 25),
                "goldEarned": random.randint(8000, 20000),
                "totalDamageDealtToChampions": random.randint(10000, 50000),
                "totalMinionsKilled": random.randint(100, 300),
                "neutralMinionsKilled": random.randint(0, 100),
                "visionScore": random.randint(10, 80),
                "champLevel": random.randint(12, 18),
                "item0": random.randint(1000, 4000),
                "item1": random.randint(1000, 4000),
                "item2": random.randint(1000, 4000),
                "item3": random.randint(1000, 4000),
                "item4": random.randint(1000, 4000),
                "item5": random.randint(1000, 4000),
                "item6": random.randint(3340, 3364),
            }
            participants.append(participant)
        
        # Construct match data in Riot API v2 format
        match_data = {
            "metadata": {
                "matchId": match_id,
                "participants": [p["puuid"] for p in participants]
            },
            "info": {
                "gameId": int(match_id.split('_')[1]),
                "platformId": "SEA",
                "gameCreation": timestamp,
                "gameDuration": random.randint(1200, 2400),  # 20-40 minutes
                "gameMode": "CLASSIC",
                "gameType": "MATCHED_GAME",
                "queueId": 420,  # Ranked Solo/Duo
                "participants": participants,
                "teams": [
                    {"teamId": 100, "win": (winning_team == 100)},
                    {"teamId": 200, "win": (winning_team == 200)}
                ]
            }
        }
        
        return match_data
    
    def send_match(self, match_data: Dict) -> bool:
        """
        Send match data to Kafka
        
        Args:
            match_data: Match data dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            topic = self.config['kafka']['topic']
            future = self.producer.send(topic, match_data)
            future.get(timeout=10)  # Wait for confirmation
            
            self.logger.debug(f"Sent match: {match_data['metadata']['matchId']}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to send match: {e}")
            return False
    
    def run_continuous(self):
        """Run generator in continuous mode"""
        interval = self.config['generator']['interval_seconds']
        
        self.logger.info("=" * 60)
        self.logger.info("Starting CONTINUOUS generation mode")
        self.logger.info(f"  Topic: {self.config['kafka']['topic']}")
        self.logger.info(f"  Interval: {interval}s per match")
        self.logger.info(f"  Rate: {1/interval:.1f} matches/second")
        self.logger.info("  Press Ctrl+C to stop")
        self.logger.info("=" * 60)
        
        match_count = 0
        try:
            while True:
                match_data = self.generate_match()
                if self.send_match(match_data):
                    match_count += 1
                    match_id = match_data['metadata']['matchId']
                    self.logger.info(f"[{match_count}] Sent: {match_id}")
                
                time.sleep(interval)
        
        except KeyboardInterrupt:
            self.logger.info("\n" + "=" * 60)
            self.logger.info("Generation stopped by user")
            self.logger.info(f"Total matches generated: {match_count}")
            self.logger.info("=" * 60)
        
        finally:
            self.producer.close()
            self.logger.info("Producer closed")
    
    def run_batch(self, batch_size: int = None):
        """Run generator in batch mode"""
        if batch_size is None:
            batch_size = self.config['generator']['batch_size']
        
        self.logger.info("=" * 60)
        self.logger.info(f"Starting BATCH generation mode ({batch_size} matches)")
        self.logger.info("=" * 60)
        
        for i in range(batch_size):
            match_data = self.generate_match()
            if self.send_match(match_data):
                match_id = match_data['metadata']['matchId']
                self.logger.info(f"[{i+1}/{batch_size}] Sent: {match_id}")
        
        self.producer.close()
        self.logger.info("=" * 60)
        self.logger.info(f"Batch completed: {batch_size} matches sent")
        self.logger.info("=" * 60)


if __name__ == "__main__":
    # CLI usage
    import argparse
    
    parser = argparse.ArgumentParser(description='LoL Match Data Generator')
    parser.add_argument('--mode', choices=['continuous', 'batch'], 
                       default='continuous', help='Generation mode')
    parser.add_argument('--batch-size', type=int, default=100,
                       help='Number of matches in batch mode')
    parser.add_argument('--config', type=str, default=None,
                       help='Path to config file')
    
    args = parser.parse_args()
    
    generator = MatchGenerator(config_path=args.config)
    
    if args.mode == 'continuous':
        generator.run_continuous()
    else:
        generator.run_batch(args.batch_size)
