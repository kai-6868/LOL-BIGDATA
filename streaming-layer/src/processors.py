"""
Data Processing Functions for Spark Streaming
Calculate real-time metrics from match data
"""

from pyspark.sql import DataFrame
from pyspark.sql.functions import (
    col, when, round as spark_round,
    sum as spark_sum, avg, count
)
from typing import Dict, Any, List
import json


def parse_match_data(rdd):
    """
    Parse JSON match data from Kafka
    
    Args:
        rdd: RDD containing Kafka messages
        
    Returns:
        List of participant records
    """
    def extract_participants(message):
        """Extract all participants from a match"""
        try:
            match = json.loads(message)
            participants = []
            
            for participant in match.get('info', {}).get('participants', []):
                participants.append({
                    'match_id': match['metadata']['matchId'],
                    'timestamp': match['info']['gameCreation'],
                    'game_duration': match['info']['gameDuration'],
                    'participant_id': str(participant['participantId']),
                    'summoner_name': participant['summonerName'],
                    'champion_name': participant['championName'],
                    'team_id': participant['teamId'],
                    'position': participant['teamPosition'],
                    'win': participant['win'],
                    'kills': participant['kills'],
                    'deaths': participant['deaths'],
                    'assists': participant['assists'],
                    'total_damage_dealt': participant['totalDamageDealtToChampions'],
                    'gold_earned': participant['goldEarned'],
                    'cs': participant['totalMinionsKilled'] + participant.get('neutralMinionsKilled', 0),
                    'vision_score': participant['visionScore']
                })
            
            return participants
        except Exception as e:
            print(f"Error parsing match: {e}")
            return []
    
    # Flat map to extract all participants
    return rdd.flatMap(extract_participants)


def calculate_derived_metrics(df: DataFrame) -> DataFrame:
    """
    Calculate derived metrics (KDA, per-minute stats)
    
    Args:
        df: DataFrame with participant data
        
    Returns:
        DataFrame with added metrics
    """
    # Calculate KDA
    df = df.withColumn(
        'kda',
        spark_round(
            when(col('deaths') == 0, col('kills') + col('assists'))
            .otherwise((col('kills') + col('assists')) / col('deaths')),
            2
        )
    )
    
    # Calculate per-minute metrics
    df = df.withColumn(
        'gold_per_minute',
        spark_round(col('gold_earned') / (col('game_duration') / 60), 2)
    )
    
    df = df.withColumn(
        'damage_per_minute',
        spark_round(col('total_damage_dealt') / (col('game_duration') / 60), 2)
    )
    
    df = df.withColumn(
        'cs_per_minute',
        spark_round(col('cs') / (col('game_duration') / 60), 2)
    )
    
    return df


def calculate_champion_stats(df: DataFrame) -> DataFrame:
    """
    Calculate champion-level statistics
    
    Args:
        df: DataFrame with participant data
        
    Returns:
        DataFrame with champion aggregations
    """
    champion_stats = df.groupBy('champion_name').agg(
        count('*').alias('games_played'),
        spark_sum(when(col('win'), 1).otherwise(0)).alias('wins'),
        avg('kills').alias('avg_kills'),
        avg('deaths').alias('avg_deaths'),
        avg('assists').alias('avg_assists'),
        avg('kda').alias('avg_kda'),
        avg('gold_per_minute').alias('avg_gpm'),
        avg('damage_per_minute').alias('avg_dpm'),
        avg('cs_per_minute').alias('avg_cspm')
    )
    
    # Calculate win rate
    champion_stats = champion_stats.withColumn(
        'win_rate',
        spark_round((col('wins') / col('games_played')) * 100, 2)
    )
    
    return champion_stats


def calculate_position_stats(df: DataFrame) -> DataFrame:
    """
    Calculate position-level statistics
    
    Args:
        df: DataFrame with participant data
        
    Returns:
        DataFrame with position aggregations
    """
    position_stats = df.groupBy('position').agg(
        count('*').alias('games_played'),
        avg('kills').alias('avg_kills'),
        avg('deaths').alias('avg_deaths'),
        avg('assists').alias('avg_assists'),
        avg('gold_per_minute').alias('avg_gpm'),
        avg('damage_per_minute').alias('avg_dpm')
    )
    
    return position_stats


def convert_to_dict(row) -> Dict[str, Any]:
    """
    Convert Spark Row to dictionary
    
    Args:
        row: Spark Row object
        
    Returns:
        Dictionary representation
    """
    return row.asDict()


def prepare_for_elasticsearch(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Prepare documents for Elasticsearch indexing
    
    Args:
        rows: List of row dictionaries
        
    Returns:
        List of prepared documents
    """
    documents = []
    for row in rows:
        # Ensure all required fields exist
        doc = {
            'match_id': row.get('match_id', ''),
            'timestamp': row.get('timestamp', 0),
            'game_duration': row.get('game_duration', 0),
            'participant_id': row.get('participant_id', ''),
            'summoner_name': row.get('summoner_name', ''),
            'champion_name': row.get('champion_name', ''),
            'team_id': row.get('team_id', 0),
            'position': row.get('position', ''),
            'win': row.get('win', False),
            'kills': row.get('kills', 0),
            'deaths': row.get('deaths', 0),
            'assists': row.get('assists', 0),
            'kda': row.get('kda', 0.0),
            'total_damage_dealt': row.get('total_damage_dealt', 0),
            'gold_earned': row.get('gold_earned', 0),
            'cs': row.get('cs', 0),
            'vision_score': row.get('vision_score', 0),
            'gold_per_minute': row.get('gold_per_minute', 0.0),
            'damage_per_minute': row.get('damage_per_minute', 0.0),
            'cs_per_minute': row.get('cs_per_minute', 0.0)
        }
        documents.append(doc)
    
    return documents
