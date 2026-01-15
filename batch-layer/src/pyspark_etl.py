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
    
    def __init__(self, config_path: str = None):
        """Initialize PySpark ETL"""
        if config_path is None:
            # Auto-detect config path relative to this file
            script_dir = Path(__file__).parent
            config_path = script_dir.parent / "config" / "batch_config.yaml"
        
        self.config = self._load_config(config_path)
        self.spark = self._create_spark_session()
        
        print("✅ PySpark ETL initialized")
    
    def _load_config(self, config_path) -> Dict[str, Any]:
        """Load configuration"""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _create_spark_session(self) -> SparkSession:
        """Create Spark session with Cassandra connector"""
        import os
        from pathlib import Path
        import platform
        
        # Detect if running in Docker (Linux) or Windows
        is_docker = platform.system() == 'Linux'
        
        # Check if Hadoop setup should be skipped (HADOOP_HOME="" means skip)
        skip_hadoop = os.environ.get('HADOOP_HOME') == ''
        
        if not is_docker and not skip_hadoop:
            # Windows: Set HADOOP_HOME to project directory
            project_root = Path(__file__).parent.parent.parent
            hadoop_home = project_root / "hadoop"
            hadoop_bin = hadoop_home / "bin"
            hadoop_bin.mkdir(parents=True, exist_ok=True)
            os.environ['HADOOP_HOME'] = str(hadoop_home)
            print(f"📁 HADOOP_HOME set to: {hadoop_home}")
        elif skip_hadoop:
            print(f"⏭️  Skipping Hadoop setup (running without native libs)")
        else:
            print(f"🐳 Running in Docker container")
        
        # Cassandra host: 'cassandra' in Docker, 'localhost' on Windows
        cassandra_host = 'cassandra' if is_docker else 'localhost'
        
        builder = SparkSession.builder \
            .appName("LoL_Batch_ETL") \
            .config("spark.cassandra.connection.host", cassandra_host) \
            .config("spark.cassandra.connection.port", "9042") \
            .config("spark.sql.extensions", "com.datastax.spark.connector.CassandraSparkExtensions") \
            .config("spark.sql.warehouse.dir", "file:///tmp/spark-warehouse") \
            .config("spark.ui.port", "4042") \
            .master("local[*]")
        
        # Add Cassandra connector package (needed for both Windows and Docker)
        builder = builder.config("spark.jars.packages", 
                                 "com.datastax.spark:spark-cassandra-connector_2.12:3.4.0")
        
        spark = builder.getOrCreate()
        
        # Suppress Hadoop warnings
        spark.sparkContext.setLogLevel("ERROR")
        
        print(f"✅ Spark session created: {spark.version}")
        return spark
    
    def read_from_hdfs(self, date_str: str = None) -> DataFrame:
        """Read Parquet files from HDFS"""
        if date_str is None:
            date_str = datetime.now().strftime('%Y/%m/%d')
        
        import platform
        
        hdfs_path = f"/data/lol_matches/{date_str}"
        print(f"📖 Reading from HDFS: {hdfs_path}")
        
        is_docker = platform.system() == 'Linux'
        
        if is_docker:
            # Running in Docker: Read directly from HDFS
            hdfs_url = f"hdfs://namenode:9000{hdfs_path}"
            print(f"  Reading from: {hdfs_url}")
            df = self.spark.read.parquet(hdfs_url)
            record_count = df.count()
            print(f"✅ Loaded {record_count} records from HDFS")
            return df
        else:
            # Running on Windows: Copy files locally
            import tempfile
            import os
            import shutil
            
            temp_dir = tempfile.mkdtemp(prefix='hdfs_data_')
            
            try:
                # List files in HDFS using docker exec
                result = subprocess.run(
                    ['docker', 'exec', 'namenode', 'hadoop', 'fs', '-ls', hdfs_path],
                    capture_output=True, text=True, check=True
                )
                
                # Parse parquet files
                parquet_files = []
                for line in result.stdout.split('\n'):
                    if '.parquet' in line:
                        parts = line.split()
                        if parts:
                            parquet_files.append(parts[-1])
                
                if not parquet_files:
                    raise FileNotFoundError(f"No parquet files found in {hdfs_path}")
                
                print(f"  Found {len(parquet_files)} parquet file(s)")
                
                # Copy each file from HDFS container to local
                for hdfs_file_path in parquet_files:
                    filename = os.path.basename(hdfs_file_path)
                    container_temp = f"/tmp/{filename}"
                    local_path = os.path.join(temp_dir, filename)
                    
                    # Remove existing temp file in container (if exists)
                    subprocess.run(
                        ['docker', 'exec', 'namenode', 'rm', '-f', container_temp],
                        capture_output=True
                    )
                    
                    # Copy from HDFS to container /tmp
                    subprocess.run(
                        ['docker', 'exec', 'namenode', 'hadoop', 'fs', '-copyToLocal', 
                         hdfs_file_path, container_temp],
                        check=True, capture_output=True
                    )
                    
                    # Copy from container to Windows
                    subprocess.run(
                        ['docker', 'cp', f'namenode:{container_temp}', local_path],
                        check=True, capture_output=True
                    )
                    
                    print(f"  ✓ Copied: {filename}")
                
                # Read local parquet files with Spark
                df = self.spark.read.parquet(f"{temp_dir}/*.parquet")
                record_count = df.count()
                print(f"✅ Loaded {record_count} records from HDFS")
                
                return df
                
            except subprocess.CalledProcessError as e:
                print(f"❌ Error accessing HDFS: {e}")
                print(f"   stdout: {e.stdout if hasattr(e, 'stdout') else 'N/A'}")
                print(f"   stderr: {e.stderr if hasattr(e, 'stderr') else 'N/A'}")
                raise
            finally:
                # Cleanup temp directory
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir, ignore_errors=True)
    
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
        from pyspark.sql.functions import current_timestamp, sum as spark_sum
        
        print(f"💾 Writing to Cassandra: {keyspace}.{table_name}")
        
        if table_name == "player_performance":
            # Write player-level data directly
            df_to_write = df.select(
                col('match_id'),
                col('summoner_name'),
                col('champion_name'),
                col('position'),
                col('team_id'),
                col('win'),
                col('kills'),
                col('deaths'),
                col('assists'),
                col('kda'),
                col('gold_earned'),
                col('total_damage'),
                col('cs'),
                col('vision_score'),
                col('match_timestamp'),
                col('match_duration'),
                col('match_date')
            )
            
        elif table_name == "match_summary":
            # Aggregate to match level
            df_to_write = df.groupBy('match_id', 'match_timestamp', 'match_duration', 'match_date') \
                .agg(
                    # Blue team (team_id = 100)
                    spark_sum(when(col('team_id') == 100, col('kills')).otherwise(0)).alias('blue_kills'),
                    spark_sum(when(col('team_id') == 100, col('deaths')).otherwise(0)).alias('blue_deaths'),
                    spark_sum(when(col('team_id') == 100, col('assists')).otherwise(0)).alias('blue_assists'),
                    spark_sum(when(col('team_id') == 100, col('gold_earned')).otherwise(0)).alias('blue_gold'),
                    spark_sum(when(col('team_id') == 100, col('total_damage')).otherwise(0)).alias('blue_damage'),
                    # Red team (team_id = 200)
                    spark_sum(when(col('team_id') == 200, col('kills')).otherwise(0)).alias('red_kills'),
                    spark_sum(when(col('team_id') == 200, col('deaths')).otherwise(0)).alias('red_deaths'),
                    spark_sum(when(col('team_id') == 200, col('assists')).otherwise(0)).alias('red_assists'),
                    spark_sum(when(col('team_id') == 200, col('gold_earned')).otherwise(0)).alias('red_gold'),
                    spark_sum(when(col('team_id') == 200, col('total_damage')).otherwise(0)).alias('red_damage'),
                    # Determine winner (check if any blue team player won)
                    spark_sum(when((col('team_id') == 100) & (col('win') == True), 1).otherwise(0)).alias('blue_wins'),
                    count('*').alias('total_players')
                ) \
                .withColumn('blue_team_win', col('blue_wins') > 0) \
                .withColumn('created_at', current_timestamp()) \
                .select(
                    'match_id', 'match_timestamp', 'match_duration', 'match_date',
                    'blue_team_win',
                    'blue_kills', 'blue_deaths', 'blue_assists', 'blue_gold', 'blue_damage',
                    'red_kills', 'red_deaths', 'red_assists', 'red_gold', 'red_damage',
                    'total_players', 'created_at'
                )
        else:
            df_to_write = df
        
        # Write to Cassandra
        df_to_write.write \
            .format("org.apache.spark.sql.cassandra") \
            .mode("append") \
            .options(table=table_name, keyspace=keyspace) \
            .save()
        
        print(f"✅ Written {df_to_write.count()} records to {table_name}")
    
    def run_etl(self, date_str: str = None):
        """Run complete ETL pipeline"""
        if date_str is None:
            date_str = datetime.now().strftime('%Y/%m/%d')
        
        print("\n" + "="*50)
        print("🚀 Starting PySpark ETL Pipeline")
        print("="*50 + "\n")
        
        # Step 1: Read from HDFS
        df_raw = self.read_from_hdfs(date_str)
        
        # Step 2: Clean data
        df_clean = self.clean_data(df_raw)

        print(df_clean.show(5))
        
        # Step 3: Feature engineering
        df_features = self.feature_engineering(df_clean)
        
        # Step 4: Write to player_performance table (player-level data)
        print("\n📊 Writing player-level data...")
        self.write_to_cassandra(df_features, 'player_performance')
        
        # Step 5: Write to match_summary table (aggregated match data)
        print("\n📊 Writing match-level data...")
        self.write_to_cassandra(df_features, 'match_summary')
        
        print("\n" + "="*50)
        print("✅ ETL Pipeline Completed Successfully!")
        print("   - player_performance: Player stats per match")
        print("   - match_summary: Aggregated team stats")
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
    parser.add_argument('--config', default=None,
                       help='Path to configuration file. Default: auto-detect')
    
    args = parser.parse_args()
    
    # Create and run ETL (config_path=None will auto-detect)
    etl = PySparkETL(config_path=args.config)
    
    try:
        etl.run_etl(date_str=args.date)
    finally:
        etl.close()


if __name__ == '__main__':
    main()
