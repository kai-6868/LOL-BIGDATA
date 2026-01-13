#!/usr/bin/env python3
"""
PySpark ETL Pipeline: HDFS → Transformations → Cassandra (Docker Version)
Chạy trong Spark container - dùng Spark native HDFS access
"""

import sys
import yaml
from datetime import datetime
from typing import Dict, Any

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import (
    col, when, avg, sum as spark_sum, count, 
    date_format, hour, dayofweek, 
    round as spark_round, lit
)


class PySparkETL:
    """PySpark ETL pipeline for batch processing"""
    
    def __init__(self, config_path: str = "/app/batch-layer/config/batch_config.yaml"):
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
        spark = SparkSession.builder \
            .appName("LoL_Batch_ETL") \
            .config("spark.cassandra.connection.host", "cassandra") \
            .config("spark.cassandra.connection.port", "9042") \
            .config("spark.sql.extensions", "com.datastax.spark.connector.CassandraSparkExtensions") \
            .config("spark.hadoop.fs.defaultFS", "hdfs://namenode:9000") \
            .master("local[*]") \
            .getOrCreate()
        
        print(f"✅ Spark session created: {spark.version}")
        return spark
    
    def read_from_hdfs(self, date_str: str = None) -> DataFrame:
        """Read Parquet files from HDFS for a specific date"""
        if date_str is None:
            date_str = datetime.now().strftime('%Y/%m/%d')
        
        # Spark native HDFS access
        hdfs_path = f"hdfs://namenode:9000/data/lol_matches/{date_str}/*.parquet"
        
        print(f"📖 Reading from HDFS: {hdfs_path}")
        
        try:
            df = self.spark.read.parquet(hdfs_path)
            record_count = df.count()
            print(f"✅ Loaded {record_count} records from HDFS")
            return df
        except Exception as e:
            print(f"❌ Error reading from HDFS: {e}")
            print(f"💡 Troubleshooting:")
            print(f"   1. Check HDFS path exists: hdfs dfs -ls /data/lol_matches/{date_str}")
            print(f"   2. Verify batch consumer has written data")
            print(f"   3. Check namenode accessible from Spark container")
            raise
    
    def clean_data(self, df: DataFrame) -> DataFrame:
        """Clean and validate data"""
        print("🧹 Cleaning data...")
        
        initial_count = df.count()
        
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
            .otherwise(spark_round((col('kills') + col('assists')) / col('deaths'), 2))
        )
        
        final_count = df_clean.count()
        records_removed = initial_count - final_count
        print(f"✅ Cleaned data: {records_removed} invalid records removed ({final_count} remain)")
        
        return df_clean
    
    def feature_engineering(self, df: DataFrame) -> DataFrame:
        """Create features for ML"""
        print("🔧 Engineering features...")
        
        from pyspark.sql.types import TimestampType
        
        df_features = df \
            .withColumn('participant_id', col('summoner_name')) \
            .withColumn('gold_per_minute', 
                       spark_round(col('gold_earned') / (col('match_duration') / 60), 2)) \
            .withColumn('damage_per_minute', 
                       spark_round(col('total_damage') / (col('match_duration') / 60), 2)) \
            .withColumn('cs_per_minute', 
                       spark_round(col('cs') / (col('match_duration') / 60), 2)) \
            .withColumn('kill_participation', 
                       spark_round((col('kills') + col('assists')) / 10.0, 2)) \
            .withColumn('match_hour', 
                       hour(col('match_timestamp').cast('timestamp'))) \
            .withColumn('match_day_of_week', 
                       dayofweek(col('match_timestamp').cast('timestamp'))) \
            .withColumn('is_weekend', 
                       when(col('match_day_of_week').isin([1, 7]), lit(True)).otherwise(lit(False))) \
            .drop('ingestion_timestamp')
        
        print("✅ Features engineered: gold_per_minute, damage_per_minute, cs_per_minute, etc.")
        return df_features
    
    def aggregate_stats(self, df: DataFrame):
        """Create aggregated statistics"""
        print("📊 Computing aggregations...")
        
        # Champion performance stats
        champion_stats = df.groupBy('champion_name') \
            .agg(
                count('*').alias('games_played'),
                spark_round(avg(col('win').cast('int')) * 100, 2).alias('win_rate'),
                spark_round(avg('kills'), 2).alias('avg_kills'),
                spark_round(avg('deaths'), 2).alias('avg_deaths'),
                spark_round(avg('assists'), 2).alias('avg_assists'),
                spark_round(avg('kda_calculated'), 2).alias('avg_kda'),
                spark_round(avg('gold_per_minute'), 2).alias('avg_gpm'),
                spark_round(avg('damage_per_minute'), 2).alias('avg_dpm')
            )
        
        print(f"  ✅ Champion stats: {champion_stats.count()} champions")
        
        # Position stats
        position_stats = df.groupBy('position') \
            .agg(
                count('*').alias('games_played'),
                spark_round(avg(col('win').cast('int')) * 100, 2).alias('win_rate'),
                spark_round(avg('kda_calculated'), 2).alias('avg_kda'),
                spark_round(avg('gold_per_minute'), 2).alias('avg_gpm')
            )
        
        print(f"  ✅ Position stats: {position_stats.count()} positions")
        
        return champion_stats, position_stats
    
    def write_to_cassandra(self, df: DataFrame, table_name: str, keyspace: str = "lol_data"):
        """Write DataFrame to Cassandra"""
        print(f"💾 Writing to Cassandra: {keyspace}.{table_name}")
        
        record_count = df.count()
        
        df.write \
            .format("org.apache.spark.sql.cassandra") \
            .mode("append") \
            .options(table=table_name, keyspace=keyspace) \
            .save()
        
        print(f"✅ Written {record_count} records to Cassandra table: {table_name}")
    
    def run_etl(self, date_str: str = None):
        """Execute full ETL pipeline"""
        print("\n" + "="*70)
        print("🚀 Starting PySpark ETL Pipeline (Docker Mode)")
        print("="*70 + "\n")
        
        start_time = datetime.now()
        
        try:
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
            
            elapsed = (datetime.now() - start_time).total_seconds()
            
            print("\n" + "="*70)
            print(f"✅ PySpark ETL Pipeline Completed in {elapsed:.2f}s")
            print("="*70 + "\n")
            
        except Exception as e:
            print(f"\n❌ ETL Pipeline Failed: {e}")
            raise
    
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
    parser.add_argument('--config', default='/app/batch-layer/config/batch_config.yaml',
                       help='Path to configuration file')
    
    args = parser.parse_args()
    
    # Create and run ETL
    etl = PySparkETL(config_path=args.config)
    
    try:
        etl.run_etl(date_str=args.date)
    except Exception as e:
        print(f"\n💥 Fatal error: {e}")
        sys.exit(1)
    finally:
        etl.close()


if __name__ == '__main__':
    main()
