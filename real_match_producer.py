"""
Real Match Data Producer
Continuously fetch real match data from Riot API and publish to Kafka
"""

import json
import time
import sys
from pathlib import Path
from datetime import datetime

# Add data-ingestion to path
sys.path.insert(0, str(Path(__file__).parent / 'data-ingestion'))

from riot_api_client import RiotAPIClient
from match_transformer import MatchTransformer
from kafka import KafkaProducer
import logging
import random

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RealMatchProducer:
    """Fetch real matches from Riot API and publish to Kafka"""
    
    # Default regions (major regions with most players)
    DEFAULT_REGIONS = ['na1', 'euw1', 'kr', 'br1']
    
    def __init__(self, api_keys: list, regions: list = None):
        # Support both single key and list of keys
        if isinstance(api_keys, str):
            api_keys = [api_keys]
        
        self.api_keys = api_keys
        self.current_key_index = 0
        
        # Support multiple regions
        if regions is None:
            regions = self.DEFAULT_REGIONS
        elif isinstance(regions, str):
            regions = [regions]
        
        self.regions = regions
        self.current_region_index = 0
        
        # Create API clients for each key
        self.api_clients = [RiotAPIClient(key) for key in api_keys]
        
        # Transformer
        self.transformer = MatchTransformer()
        
        # Kafka producer (simple config like lol_match_generator)
        self.producer = KafkaProducer(
            bootstrap_servers=['localhost:9092', 'localhost:9093', 'localhost:9094'],
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        
        logger.info("✅ Kafka producer connected to cluster (3 brokers)")
        
        # Track processed matches
        self.processed_matches = set()
        
        logger.info(f"✅ Real Match Producer initialized")
        logger.info(f"   Regions: {', '.join(self.regions)}")
        logger.info(f"   API Keys: {len(self.api_keys)}")
        logger.info(f"   Max throughput: ~{len(self.api_keys) * 20} req/sec")
    
    def _get_next_region(self):
        """Rotate through regions"""
        region = self.regions[self.current_region_index]
        self.current_region_index = (self.current_region_index + 1) % len(self.regions)
        return region
    
    def _get_next_client(self):
        """Rotate through API clients"""
        client = self.api_clients[self.current_key_index]
        self.current_key_index = (self.current_key_index + 1) % len(self.api_clients)
        return client
    
    def publish_match(self, match_id: str, region: str):
        """Fetch and publish a match"""
        if match_id in self.processed_matches:
            return 0
        
        client = self._get_next_client()
        match_data = client.get_match_details(match_id, region)
        if not match_data:
            return 0
        
        records = self.transformer.transform_match(match_data)
        count = 0
        
        for record in records:
            self.producer.send('lol-matches', value=record)
            count += 1
        
        self.processed_matches.add(match_id)
        logger.info(f"✅ [{region.upper()}] Published match {match_id}: {count} players")
        return count
    
    def run_continuous(self, matches_per_region: int = 20, delay: int = 2):
        """Run continuous data collection - publish each match immediately"""
        logger.info(f"🚀 Starting continuous data collection...")
        logger.info(f"   Matches per region: {matches_per_region}")
        logger.info(f"   Delay: {delay}s between matches")
        logger.info(f"   Publishing: IMMEDIATE (no batching)")
        
        total_published = 0
        match_count = 0
        
        try:
            while True:
                # Rotate to next region
                region = self._get_next_region()
                
                logger.info(f"\n{'='*60}")
                logger.info(f"🌍 Region: {region.upper()}")
                logger.info(f"{'='*60}")
                
                # Get Challenger players for this region
                client = self._get_next_client()
                players = client.get_challenger_players(region)
                logger.info(f"Found {len(players)} Challenger players")
                
                if not players:
                    logger.warning(f"No players found, skipping...")
                    time.sleep(5)
                    continue
                
                # Get matches from random players
                selected_players = random.sample(players, min(3, len(players)))
                
                for player in selected_players:
                    puuid = player.get('puuid')
                    if not puuid:
                        continue
                    
                    # Get recent matches
                    client = self._get_next_client()
                    match_ids = client.get_match_ids(puuid, count=matches_per_region, region=region)
                    logger.info(f"\nPlayer {puuid[:8]}: {len(match_ids)} matches")
                    
                    # Process each match IMMEDIATELY
                    for match_id in match_ids:
                        if match_id in self.processed_matches:
                            continue
                        
                        try:
                            # Fetch match
                            client = self._get_next_client()
                            match_data = client.get_match_details(match_id, region)
                            if not match_data:
                                continue
                            
                            # Transform
                            records = self.transformer.transform_match(match_data)
                            if not records:
                                continue
                            
                            # Publish IMMEDIATELY (like lol_match_generator)
                            for record in records:
                                self.producer.send('lol-matches', value=record)
                            
                            self.producer.flush()  # Flush after each match
                            
                            match_count += 1
                            total_published += len(records)
                            self.processed_matches.add(match_id)
                            
                            timestamp = datetime.now().strftime('%H:%M:%S')
                            logger.info(f"[{timestamp}] ✅ Match #{match_count}: {match_id} ({len(records)} players)")
                            
                            # Delay before next match
                            time.sleep(delay)
                            
                        except Exception as e:
                            logger.error(f"Failed to process {match_id}: {e}")
                            continue
                
                logger.info(f"\n📊 Summary:")
                logger.info(f"   Total matches: {match_count}")
                logger.info(f"   Total records: {total_published}")
                
        except KeyboardInterrupt:
            logger.info("\n\n⛔ Stopped by user")
        except Exception as e:
            logger.error(f"\n\n❌ Error: {e}", exc_info=True)
        finally:
            self.producer.close()
            logger.info(f"\n✅ Total: {match_count} matches, {total_published} records")


def main():
    """Main entry point"""
    import os
    
    api_keys = []
    
    # Method 1: From command line (space-separated)
    if len(sys.argv) > 1:
        # Check if it's a file path
        if os.path.isfile(sys.argv[1]):
            # Read from file (one key per line)
            with open(sys.argv[1], 'r') as f:
                api_keys = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        else:
            # Multiple keys from command line
            api_keys = sys.argv[1:]
    
    # Method 2: From environment variable
    if not api_keys:
        env_keys = os.getenv('RIOT_API_KEYS')  # Comma-separated
        if env_keys:
            api_keys = [k.strip() for k in env_keys.split(',')]
    
    # Method 3: Single key from environment
    if not api_keys:
        single_key = os.getenv('RIOT_API_KEY')
        if single_key:
            api_keys = [single_key]
    
    # Validate
    if not api_keys:
        print("❌ Error: API key(s) required\n")
        print("Usage:")
        print("  # Single key:")
        print("  python real_match_producer.py RGAPI-xxx")
        print("")
        print("  # Multiple keys:")
        print("  python real_match_producer.py RGAPI-xxx RGAPI-yyy RGAPI-zzz")
        print("")
        print("  # From file:")
        print("  python real_match_producer.py api_keys.txt")
        print("")
        print("  # Environment variable:")
        print("  set RIOT_API_KEYS=RGAPI-xxx,RGAPI-yyy")
        print("  python real_match_producer.py")
        sys.exit(1)
    
    # Create producer
    producer = RealMatchProducer(api_keys=api_keys)
    
    # Run continuous collection (publish each match immediately)
    producer.run_continuous(matches_per_region=20, delay=2)


if __name__ == "__main__":
    main()
