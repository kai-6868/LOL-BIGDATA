#!/usr/bin/env python3
"""
Batch Consumer: Kafka → HDFS
Consumes messages from Kafka in batches and writes to HDFS in Parquet format.
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

import yaml
from kafka import KafkaConsumer, TopicPartition
from kafka.errors import KafkaError
import pyarrow as pa
import pyarrow.parquet as pq
from hdfs import InsecureClient
import pandas as pd


class BatchConsumer:
    """Batch consumer for Kafka → HDFS pipeline"""
    
    def __init__(self, config_path: str = "batch-layer/config/batch_config.yaml"):
        """Initialize batch consumer with configuration"""
        self.config = self._load_config(config_path)
        self.logger = self._setup_logging()
        
        # Initialize Kafka consumer
        self.consumer = self._create_consumer()
        
        # Initialize HDFS client
        self.hdfs_client = self._create_hdfs_client()
        
        # Checkpoint tracking
        self.checkpoint_dir = Path(self.config['batch']['checkpoint_dir'])
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info("Batch Consumer initialized successfully")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        log_dir = Path(self.config['batch']['log_dir'])
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / f"batch_consumer_{datetime.now().strftime('%Y%m%d')}.log"
        
        logging.basicConfig(
            level=getattr(logging, self.config['monitoring']['log_level']),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        return logging.getLogger(__name__)
    
    def _create_consumer(self) -> KafkaConsumer:
        """Create and configure Kafka consumer"""
        kafka_config = self.config['kafka']
        
        consumer = KafkaConsumer(
            kafka_config['topic'],
            bootstrap_servers=kafka_config['bootstrap_servers'],
            group_id=kafka_config['group_id'],
            auto_offset_reset=kafka_config['auto_offset_reset'],
            enable_auto_commit=kafka_config['enable_auto_commit'],
            max_poll_records=kafka_config['max_poll_records'],
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            key_deserializer=lambda m: m.decode('utf-8') if m else None
        )
        
        self.logger.info(f"Kafka consumer created for topic: {kafka_config['topic']}")
        return consumer
    
    def _create_hdfs_client(self) -> InsecureClient:
        """Create HDFS client"""
        hdfs_config = self.config['hdfs']
        namenode_url = hdfs_config['namenode_url'].replace('hdfs://', 'http://')
        
        # Extract host and port
        parts = namenode_url.replace('http://', '').split(':')
        host = parts[0]
        port = 9870  # WebHDFS port
        
        client = InsecureClient(f'http://{host}:{port}')
        
        self.logger.info(f"HDFS client connected to: {host}:{port}")
        return client
    
    def _get_hdfs_path(self, batch_date: datetime) -> str:
        """Generate HDFS path based on date partitioning"""
        base_path = self.config['hdfs']['base_path']
        year = batch_date.strftime('%Y')
        month = batch_date.strftime('%m')
        day = batch_date.strftime('%d')
        
        return f"{base_path}/{year}/{month}/{day}"
    
    def _generate_filename(self, batch_id: int) -> str:
        """Generate unique filename for batch"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"matches_{timestamp}_batch{batch_id}.parquet"
    
    def consume_batch(self) -> List[Dict[str, Any]]:
        """Consume a batch of messages from Kafka"""
        batch_size = self.config['batch']['size']
        timeout = self.config['batch']['timeout']
        
        messages = []
        start_time = datetime.now()
        
        try:
            # Poll messages
            while len(messages) < batch_size:
                # Check timeout
                elapsed = (datetime.now() - start_time).total_seconds()
                if elapsed > timeout:
                    self.logger.warning(f"Batch timeout reached. Got {len(messages)}/{batch_size} messages")
                    break
                
                # Poll with 1 second timeout
                msg_batch = self.consumer.poll(timeout_ms=1000, max_records=batch_size - len(messages))
                
                for topic_partition, msgs in msg_batch.items():
                    for msg in msgs:
                        messages.append({
                            'data': msg.value,
                            'offset': msg.offset,
                            'partition': msg.partition,
                            'timestamp': msg.timestamp
                        })
            
            self.logger.info(f"Consumed batch: {len(messages)} messages")
            return messages
            
        except KafkaError as e:
            self.logger.error(f"Kafka error during consume: {e}")
            raise
    
    def write_to_hdfs(self, messages: List[Dict[str, Any]], batch_id: int) -> str:
        """Write batch to HDFS in Parquet format"""
        if not messages:
            self.logger.warning("No messages to write to HDFS")
            return None
        
        try:
            # Extract match data and flatten participants
            records = []
            for msg in messages:
                match_data = msg['data']
                
                # Extract metadata and info from Riot API v2 format
                metadata = match_data.get('metadata', {})
                info = match_data.get('info', {})
                
                match_id = metadata.get('matchId', 'unknown')
                game_creation = info.get('gameCreation')
                game_duration = info.get('gameDuration')
                
                # Flatten participants
                for participant in info.get('participants', []):
                    # Calculate KDA
                    kills = participant.get('kills', 0)
                    deaths = participant.get('deaths', 0)
                    assists = participant.get('assists', 0)
                    kda = (kills + assists) / deaths if deaths > 0 else (kills + assists)
                    
                    # Calculate CS (creep score)
                    cs = participant.get('totalMinionsKilled', 0) + participant.get('neutralMinionsKilled', 0)
                    
                    record = {
                        'match_id': match_id,
                        'match_timestamp': game_creation,
                        'match_duration': game_duration,
                        'summoner_name': participant.get('summonerName'),
                        'champion_name': participant.get('championName'),
                        'position': participant.get('teamPosition'),
                        'team_id': participant.get('teamId'),
                        'win': participant.get('win'),
                        'kills': kills,
                        'deaths': deaths,
                        'assists': assists,
                        'kda': round(kda, 2),
                        'gold_earned': participant.get('goldEarned'),
                        'total_damage': participant.get('totalDamageDealtToChampions'),
                        'cs': cs,
                        'vision_score': participant.get('visionScore'),
                        'kafka_offset': msg['offset'],
                        'kafka_partition': msg['partition'],
                        'ingestion_timestamp': datetime.fromtimestamp(msg['timestamp'] / 1000).isoformat()
                    }
                    records.append(record)
            
            # Convert to DataFrame
            df = pd.DataFrame(records)
            
            # Add date column for partitioning
            # Handle case where match_timestamp might be in seconds or milliseconds
            if df['match_timestamp'].max() > 1e12:  # milliseconds
                df['match_date'] = pd.to_datetime(df['match_timestamp'], unit='ms').dt.date
            else:  # seconds
                df['match_date'] = pd.to_datetime(df['match_timestamp'], unit='s').dt.date
            
            # Determine HDFS path
            batch_date = datetime.now()
            hdfs_dir = self._get_hdfs_path(batch_date)
            filename = self._generate_filename(batch_id)
            hdfs_path = f"{hdfs_dir}/{filename}"
            
            # Create directory if not exists
            self.hdfs_client.makedirs(hdfs_dir)
            
            # Write to Parquet
            table = pa.Table.from_pandas(df)
            
            # Write to local temp file first
            import tempfile
            temp_dir = tempfile.gettempdir()
            local_temp_file = os.path.join(temp_dir, filename)
            pq.write_table(
                table, 
                local_temp_file,
                compression=self.config['hdfs']['compression']
            )
            
            # Upload to HDFS via docker exec (workaround for hostname resolution)
            import subprocess
            container_temp = f"/tmp/{filename}"
            
            # Copy to namenode container
            subprocess.run(
                ['docker', 'cp', local_temp_file, f'namenode:{container_temp}'],
                check=True,
                capture_output=True
            )
            
            # Move to HDFS from inside container
            subprocess.run(
                ['docker', 'exec', 'namenode', 'hdfs', 'dfs', '-put', container_temp, hdfs_path],
                check=True,
                capture_output=True
            )
            
            # Clean up
            subprocess.run(
                ['docker', 'exec', 'namenode', 'rm', container_temp],
                check=False
            )
            os.remove(local_temp_file)
            
            self.logger.info(f"Written {len(records)} records to HDFS: {hdfs_path}")
            return hdfs_path
            
        except Exception as e:
            self.logger.error(f"Error writing to HDFS: {e}")
            raise
    
    def commit_offsets(self):
        """Commit Kafka offsets after successful HDFS write"""
        try:
            self.consumer.commit()
            self.logger.info("Kafka offsets committed")
        except KafkaError as e:
            self.logger.error(f"Error committing offsets: {e}")
            raise
    
    def save_checkpoint(self, batch_id: int, hdfs_path: str, message_count: int):
        """Save checkpoint for recovery"""
        checkpoint = {
            'batch_id': batch_id,
            'timestamp': datetime.now().isoformat(),
            'hdfs_path': hdfs_path,
            'message_count': message_count,
            'consumer_group': self.config['kafka']['group_id']
        }
        
        checkpoint_file = self.checkpoint_dir / f"checkpoint_{batch_id}.json"
        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint, f, indent=2)
        
        self.logger.info(f"Checkpoint saved: {checkpoint_file}")
    
    def run(self, num_batches: int = None):
        """Main execution loop"""
        self.logger.info("Starting Batch Consumer...")
        
        batch_id = 0
        
        try:
            while True:
                # Check if we've reached the target number of batches
                if num_batches and batch_id >= num_batches:
                    self.logger.info(f"Completed {num_batches} batches. Exiting.")
                    break
                
                # Consume batch
                messages = self.consume_batch()
                
                if not messages:
                    self.logger.info("No messages consumed. Waiting...")
                    continue
                
                # Write to HDFS
                hdfs_path = self.write_to_hdfs(messages, batch_id)
                
                # Commit offsets
                self.commit_offsets()
                
                # Save checkpoint
                self.save_checkpoint(batch_id, hdfs_path, len(messages))
                
                batch_id += 1
                self.logger.info(f"Batch {batch_id} completed successfully")
                
        except KeyboardInterrupt:
            self.logger.info("Batch Consumer stopped by user")
        except Exception as e:
            self.logger.error(f"Fatal error: {e}", exc_info=True)
            raise
        finally:
            self.close()
    
    def close(self):
        """Clean up resources"""
        self.logger.info("Closing Batch Consumer...")
        self.consumer.close()
        self.logger.info("Batch Consumer closed")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Batch Consumer: Kafka → HDFS')
    parser.add_argument('--config', default='batch-layer/config/batch_config.yaml',
                       help='Path to configuration file')
    parser.add_argument('--batches', type=int, default=None,
                       help='Number of batches to process (None = infinite)')
    
    args = parser.parse_args()
    
    # Create and run consumer
    consumer = BatchConsumer(config_path=args.config)
    consumer.run(num_batches=args.batches)


if __name__ == '__main__':
    main()
