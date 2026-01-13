"""
Spark Structured Streaming Consumer for LoL Match Data
Consumes from Kafka and indexes to Elasticsearch
Uses Spark 3.5.0 Structured Streaming API
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    from_json, col, when, round as spark_round,
    to_timestamp, from_unixtime, expr
)
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType,
    LongType, BooleanType, ArrayType
)
import yaml
import logging
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.elasticsearch_indexer import ElasticsearchIndexer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SparkStreamingConsumer:
    """
    Spark Structured Streaming consumer for real-time match data processing
    """
    
    def __init__(self, config_file: str = "streaming-layer/config/spark_config.yaml"):
        """
        Initialize Spark Structured Streaming consumer
        
        Args:
            config_file: Path to configuration file
        """
        # Load configuration
        with open(config_file, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Setup logging
        log_level = self.config.get('logging', {}).get('level', 'INFO')
        logging.getLogger().setLevel(getattr(logging, log_level))
        
        # Initialize Spark session
        self.spark = None
        self.es_indexer = None
        
        self._initialize_spark()
        self._initialize_elasticsearch()
    
    def _initialize_spark(self):
        """Initialize Spark Session for Structured Streaming"""
        try:
            # Create Spark Session
            spark_config = self.config['spark']
            builder = SparkSession.builder.appName(spark_config['app_name'])
            
            # Set master
            master = spark_config.get('master', 'local[*]')
            builder = builder.master(master)
            
            # Add Kafka package for Structured Streaming
            builder = builder.config(
                "spark.jars.packages",
                "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0"
            )
            
            # Add configurations
            for key, value in spark_config.get('config', {}).items():
                builder = builder.config(key, value)
            
            # Create session
            self.spark = builder.getOrCreate()
            self.spark.sparkContext.setLogLevel("WARN")
            
            logger.info(f"✓ Initialized Spark Structured Streaming")
            
        except Exception as e:
            logger.error(f"✗ Failed to initialize Spark: {e}")
            raise
    
    def _initialize_elasticsearch(self):
        """Initialize Elasticsearch indexer"""
        try:
            es_config = self.config['elasticsearch']
            # Use internal Docker hostname if available, otherwise external
            hosts = es_config.get('hosts', es_config.get('hosts_external', ['http://localhost:9200']))
            
            self.es_indexer = ElasticsearchIndexer(
                hosts=hosts,
                index_name=es_config['index_name'],
                mapping_file=es_config.get('mapping_file', 'streaming-layer/config/es_mapping.json')
            )
            logger.info("✓ Initialized Elasticsearch indexer")
            
        except Exception as e:
            logger.error(f"✗ Failed to initialize Elasticsearch: {e}")
            raise
    
    def _define_schema(self):
        """Define schema for match data"""
        participant_schema = StructType([
            StructField("participantId", IntegerType()),
            StructField("summonerName", StringType()),
            StructField("championName", StringType()),
            StructField("teamId", IntegerType()),
            StructField("teamPosition", StringType()),
            StructField("win", BooleanType()),
            StructField("kills", IntegerType()),
            StructField("deaths", IntegerType()),
            StructField("assists", IntegerType()),
            StructField("totalDamageDealtToChampions", LongType()),
            StructField("goldEarned", IntegerType()),
            StructField("totalMinionsKilled", IntegerType()),
            StructField("neutralMinionsKilled", IntegerType()),
            StructField("visionScore", IntegerType())
        ])
        
        match_schema = StructType([
            StructField("metadata", StructType([
                StructField("matchId", StringType())
            ])),
            StructField("info", StructType([
                StructField("gameCreation", LongType()),
                StructField("gameDuration", IntegerType()),
                StructField("participants", ArrayType(participant_schema))
            ]))
        ])
        
        return match_schema
    
    def process_batch(self, batch_df, batch_id):
        """
        Process a micro-batch of data
        
        Args:
            batch_df: DataFrame containing batch data
            batch_id: Batch identifier
        """
        try:
            if batch_df.isEmpty():
                return
            
            # Explode participants array
            participants_df = batch_df.select(
                col("data.metadata.matchId").alias("match_id"),
                col("data.info.gameCreation").alias("timestamp"),
                col("data.info.gameDuration").alias("game_duration"),
                expr("explode(data.info.participants)").alias("participant")
            )
            
            # Extract participant fields
            participants_df = participants_df.select(
                "match_id",
                "timestamp",
                "game_duration",
                col("participant.participantId").cast("string").alias("participant_id"),
                col("participant.summonerName").alias("summoner_name"),
                col("participant.championName").alias("champion_name"),
                col("participant.teamId").alias("team_id"),
                col("participant.teamPosition").alias("position"),
                col("participant.win").alias("win"),
                col("participant.kills").alias("kills"),
                col("participant.deaths").alias("deaths"),
                col("participant.assists").alias("assists"),
                col("participant.totalDamageDealtToChampions").alias("total_damage_dealt"),
                col("participant.goldEarned").alias("gold_earned"),
                (col("participant.totalMinionsKilled") + 
                 col("participant.neutralMinionsKilled")).alias("cs"),
                col("participant.visionScore").alias("vision_score")
            )
            
            # Calculate derived metrics
            participants_df = participants_df.withColumn(
                "kda",
                spark_round(
                    when(col("deaths") == 0, col("kills") + col("assists"))
                    .otherwise((col("kills") + col("assists")) / col("deaths")),
                    2
                )
            )
            
            participants_df = participants_df.withColumn(
                "gold_per_minute",
                spark_round(col("gold_earned") / (col("game_duration") / 60), 2)
            )
            
            participants_df = participants_df.withColumn(
                "damage_per_minute",
                spark_round(col("total_damage_dealt") / (col("game_duration") / 60), 2)
            )
            
            participants_df = participants_df.withColumn(
                "cs_per_minute",
                spark_round(col("cs") / (col("game_duration") / 60), 2)
            )
            
            # Convert to list of dictionaries
            rows = participants_df.collect()
            documents = [row.asDict() for row in rows]
            
            # Bulk index to Elasticsearch
            if documents:
                success, failed = self.es_indexer.bulk_index(documents)
                logger.info(
                    f"Batch {batch_id}: {len(documents)} participants, "
                    f"{success} indexed, {failed} failed"
                )
        
        except Exception as e:
            logger.error(f"✗ Error processing batch {batch_id}: {e}")
    
    def start(self):
        """Start structured streaming consumption"""
        try:
            # Kafka configuration
            kafka_config = self.config['kafka']
            
            # Use internal Docker hostname if available, otherwise external
            bootstrap_servers = kafka_config.get('bootstrap_servers', 
                                                kafka_config.get('bootstrap_servers_external', 'localhost:29092'))
            
            logger.info(f"Subscribing to Kafka topic: {kafka_config['topic']}")
            
            # Define schema
            match_schema = self._define_schema()
            
            # Read from Kafka
            kafka_df = self.spark \
                .readStream \
                .format("kafka") \
                .option("kafka.bootstrap.servers", bootstrap_servers) \
                .option("subscribe", kafka_config['topic']) \
                .option("startingOffsets", kafka_config['auto_offset_reset']) \
                .load()
            
            # Parse JSON data
            parsed_df = kafka_df.select(
                from_json(col("value").cast("string"), match_schema).alias("data")
            )
            
            # Checkpoint location
            checkpoint_location = self.config['streaming']['checkpoint_location']
            os.makedirs(checkpoint_location, exist_ok=True)
            
            # Start streaming query
            logger.info("=" * 60)
            logger.info("✓ Starting Spark Structured Streaming Consumer")
            logger.info(f"  Kafka: {kafka_config['bootstrap_servers']}")
            logger.info(f"  Topic: {kafka_config['topic']}")
            logger.info(f"  Elasticsearch: {self.config['elasticsearch']['hosts']}")
            logger.info("=" * 60)
            
            query = parsed_df \
                .writeStream \
                .foreachBatch(self.process_batch) \
                .option("checkpointLocation", checkpoint_location) \
                .start()
            
            query.awaitTermination()
            
        except KeyboardInterrupt:
            logger.info("\n✓ Stopping streaming consumer...")
            self.stop()
        except Exception as e:
            logger.error(f"✗ Error in streaming: {e}")
            self.stop()
            raise
    
    def stop(self):
        """Stop streaming and cleanup"""
        try:
            if self.spark:
                self.spark.stop()
            if self.es_indexer:
                self.es_indexer.close()
            logger.info("✓ Streaming consumer stopped")
        except Exception as e:
            logger.error(f"✗ Error stopping consumer: {e}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Spark Streaming Consumer for LoL Matches")
    parser.add_argument(
        '--config',
        type=str,
        default='streaming-layer/config/spark_config.yaml',
        help='Path to configuration file'
    )
    
    args = parser.parse_args()
    
    # Create and start consumer
    consumer = SparkStreamingConsumer(config_file=args.config)
    consumer.start()


if __name__ == "__main__":
    main()
