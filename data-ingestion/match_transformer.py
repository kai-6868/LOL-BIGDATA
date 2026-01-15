"""
Match Data Transformer
Transform Riot API response to our schema
"""

from typing import List, Dict
from datetime import datetime


class MatchTransformer:
    """Transform Riot API match data to our schema"""
    
    def transform_match(self, match_data: Dict) -> List[Dict]:
        """Transform match data to player records"""
        if not match_data or 'info' not in match_data:
            return []
        
        info = match_data['info']
        match_id = match_data['metadata']['matchId']
        
        records = []
        for p in info['participants']:
            record = {
                'match_id': match_id,
                'match_timestamp': info['gameCreation'] // 1000,
                'match_duration': info['gameDuration'],
                'summoner_name': p['summonerName'],
                'champion_name': p['championName'],
                'position': p.get('teamPosition', 'UNKNOWN')[:3],
                'team_id': p['teamId'],
                'win': p['win'],
                'kills': p['kills'],
                'deaths': p['deaths'],
                'assists': p['assists'],
                'kda': round((p['kills'] + p['assists']) / max(p['deaths'], 1), 2),
                'gold_earned': p['goldEarned'],
                'total_damage': p['totalDamageDealtToChampions'],
                'cs': p['totalMinionsKilled'] + p['neutralMinionsKilled'],
                'vision_score': p['visionScore'],
                'kafka_offset': 0,
                'kafka_partition': 0,
                'ingestion_timestamp': datetime.now().isoformat(),
                'match_date': datetime.fromtimestamp(info['gameCreation'] // 1000).strftime('%Y-%m-%d')
            }
            records.append(record)
        
        return records
