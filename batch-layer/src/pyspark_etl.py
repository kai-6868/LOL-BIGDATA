#!/usr/bin/env python3
"""
PySpark ETL Pipeline: HDFS → Transformations → Cassandra
Processes historical data from HDFS and writes to Cassandra.
"""

import sys
import yaml
import subprocess
from datetime import datetime, timedelta
from typing import Dict, Any
from pathlib import Path

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import (
    col, when, avg, sum as spark_sum, count, 
    from_unixtime, hour, dayofweek, 
    round as spark_round, lit
)
from pyspark.sql.types import *


class PySparkETL:
    """PySpark ETL pipeline for batch processing"""
    
    def __init__(self, config_path: str = "batch-layer/config/batch_config.yaml"):
        """Initialize PySpark ETL"""
        self.config = self._load_config(config_path)
        self.spark = self._create_spark_session()
        
        print("✅ PySpark ETL initialized")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration"""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _create_spark_session(self) -> SparkSession:
        """Create Spark session with Cassandra connector"""
        import os
        os.environ['HADOOP_HOME'] = os.path.join(os.path.dirname(__file__), '..', '..')
        
        spark = SparkSession.builder \
            .appName("LoL_Batch_ETL") \
            .config("spark.jars.packages", "com.datastax.spark:spark-cassandra-connector_2.12:3.4.0") \
            .config("spark.cassandra.connection.host", "localhost") \
            .config("spark.cassandra.connection.port", "9042") \
            .config("spark.sql.extensions", "com.datastax.spark.connector.CassandraSparkExtensions") \
            .config("spark.driver.host", "localhost") \
            .config("spark.driver.bindAddress", "localhost") \
            .config("spark.sql.warehouse.dir", "file:///tmp/spark-warehouse") \
            .master("local[*]") \
            .getOrCreate()
        
        print(f"✅ Spark session created: {spark.version}")
        return spark
    
    def read_from_hdfs(self, date_str: str = None) -> DataFrame:
        """Read Parquet files from HDFS for a specific date"""
        if date_str is None:
            date_str = datetime.now().strftime('%Y/%m/%d')
        
        # Download from HDFS to local temp directory
        import tempfile
        temp_dir = tempfile.mkdtemp()
        hdfs_path = f"/data/lol_matches/{date_str}"
        
        print(f"📖 Reading from HDFS: {hdfs_path}")
        
        # List files in HDFS
        result = subprocess.run(
            ['docker', 'exec', 'namenode', 'hdfs', 'dfs', '-ls', hdfs_path],
            capture_output=True, text=True
        )
        
        if result.returncode != 0:
            raise FileNotFoundError(f"HDFS path not found: {hdfs_path}")
        
        # Get parquet files
        files = [line.split()[-1] for line in result.stdout.split('\n') 
                if line.strip() and line.strip().endswith('.parquet')]
        
        # Download each file
        for hdfs_file in files:
            filename = Path(hdfs_file).name
            local_file = f"{temp_dir}/{filename}"
            
            # Copy from HDFS via docker
            subprocess.run(
                ['docker', 'exec', 'namenode', 'hdfs', 'dfs', '-get', hdfs_file, '/tmp/'],
                check=True, capture_output=True
            )
            subprocess.run(
                ['docker', 'cp', f'namenode:/tmp/{filename}', local_file],
                check=True, capture_output=True
            )
        
        # Read parquet files
        df = self.spark.read.parquet(f"{temp_dir}/*.parquet")
        
        print(f"✅ Loaded {df.count()} records from HDFS")
        return df
    
    def clean_data(self, df: DataFrame) -> DataFrame:
        """Clean and validate data"""
        print("🧹 Cleaning data...")
        
        # Remove nulls in critical fields
        df_clean = df.dropna(subset=['match_id', 'summoner_name', 'champion_name'])
        
        # Filter invalid data
        df_clean = df_clean.filter(
            (col('kills') >= 0) & 
            (col('deaths') >= 0) & 
            (col('assists') >= 0) &
            (col('gold_earned') > 0) &
            (col('match_duration') > 0)
        )
        
        # Recalculate KDA (in case of issues)
        df_clean = df_clean.withColumn(
            'kda_calculated',
            when(col('deaths') == 0, col('kills') + col('assists'))
            .otherwise((col('kills') + col('assists')) / col('deaths'))
        )
        
        records_removed = df.count() - df_clean.count()
        print(f"✅ Cleaned data: {records_removed} invalid records removed")
        
        return df_clean
    
    def feature_engineering(self, df: DataFrame) -> DataFrame:
        """Create features for ML"""
        print("🔧 Engineering features...")
        
        df_features = df \
            .withColumn('gold_per_minute', spark_round(col('gold_earned') / (col('match_duration') / 60), 2)) \
            .withColumn('damage_per_minute', spark_round(col('total_damage') / (col('match_duration') / 60), 2)) \
            .withColumn('cs_per_minute', spark_round(col('cs') / (col('match_duration') / 60), 2)) \
            .withColumn('kill_participation', 
                       when(col('team_id').isNotNull(), 
                            spark_round((col('kills') + col('assists')) / 10, 2))
                       .otherwise(0)) \
            .withColumn('match_hour', hour(from_unixtime(col('match_timestamp') / 1000))) \
            .withColumn('match_day_of_week', dayofweek(from_unixtime(col('match_timestamp') / 1000))) \
            .withColumn('is_weekend', when(col('match_day_of_week').isin([1, 7]), lit(True)).otherwise(lit(False)))
        
        print("✅ Features engineered")
        return df_features
    
    def aggregate_stats(self, df: DataFrame):
        """Create aggregated statistics"""
        print("📊 Computing aggregations...")
        
        # Champion performance stats
        champion_stats = df.groupBy('champion_name') \
            .agg(
                count('*').alias('games_played'),
                avg(col('win').cast('int')).alias('win_rate'),
                avg('kills').alias('avg_kills'),
                avg('deaths').alias('avg_deaths'),
                avg('assists').alias('avg_assists'),
                avg('kda_calculated').alias('avg_kda'),
                avg('gold_per_minute').alias('avg_gpm'),
                avg('damage_per_minute').alias('avg_dpm')
            ) \
            .withColumn('win_rate', spark_round(col('win_rate') * 100, 2)) \
            .withColumn('last_updated', lit(datetime.now()))
        
        # Position stats
        position_stats = df.groupBy('position') \
            .agg(
                count('*').alias('games_played'),
                avg(col('win').cast('int')).alias('win_rate'),
                avg('kda_calculated').alias('avg_kda'),
                avg('gold_per_minute').alias('avg_gpm')
            ) \
            .withColumn('win_rate', spark_round(col('win_rate') * 100, 2)) \
            .withColumn('last_updated', lit(datetime.now()))
        
        print("✅ Aggregations computed")
        
        return champion_stats, position_stats
    
    def write_to_cassandra(self, df: DataFrame, table_name: str, keyspace: str = "lol_data"):
        """Write DataFrame to Cassandra"""
        print(f"💾 Writing to Cassandra: {keyspace}.{table_name}")
        
        df.write \
            .format("org.apache.spark.sql.cassandra") \
            .mode("append") \
            .options(table=table_name, keyspace=keyspace) \
            .save()
        
        print(f"✅ Written {df.count()} records to Cassandra")
    
    def run_etl(self, date_str: str = None):
        """Execute full ETL pipeline"""
        print("\n" + "="*50)
        print("🚀 Starting PySpark ETL Pipeline")
        print("="*50 + "\n")
        
        # Step 1: Read from HDFS
        df_raw = self.read_from_hdfs(date_str)
        
        # Step 2: Clean data
        df_clean = self.clean_data(df_raw)
        
        # Step 3: Feature engineering
        df_features = self.feature_engineering(df_clean)
        
        # Step 4: Write main participant data to Cassandra
        self.write_to_cassandra(df_features, 'match_participants')
        
        # Step 5: Compute and write aggregations
        champion_stats, position_stats = self.aggregate_stats(df_features)
        self.write_to_cassandra(champion_stats, 'champion_stats')
        self.write_to_cassandra(position_stats, 'position_stats')
        
        print("\n" + "="*50)
        print("✅ PySpark ETL Pipeline Completed")
        print("="*50 + "\n")
    
    def close(self):
        """Stop Spark session"""
        self.spark.stop()
        print("✅ Spark session stopped")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='PySpark ETL: HDFS → Cassandra')
    parser.add_argument('--date', default=None,
                       help='Date to process (YYYY/MM/DD format). Default: today')
    parser.add_argument('--config', default='batch-layer/config/batch_config.yaml',
                       help='Path to configuration file')
    
    args = parser.parse_args()
    
    # Create and run ETL
    etl = PySparkETL(config_path=args.config)
    
    try:
        etl.run_etl(date_str=args.date)
    finally:
        etl.close()


if __name__ == '__main__':
    main()
