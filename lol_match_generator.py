"""
LoL Match Data Generator
Tạo fake match data với format giống Riot API để test Big Data pipeline
Bypass việc crawl từ op.gg (do CSS changes)
"""
from kafka import KafkaProducer
import json
import random
import time
from datetime import datetime

# Config
BOOTSTRAP_SERVERS = ['localhost:9092', 'localhost:9093', 'localhost:9094']  # Kafka cluster
TOPIC_NAME = 'lol_matches'  # Dùng topic cố định cho streaming
INTERVAL_SECONDS = 0.5  # Sinh 1 match mỗi 0.5 giây

# Champion pool (ví dụ)
CHAMPIONS = [
    "Ahri", "Yasuo", "Zed", "Jinx", "Thresh", "Lee Sin", "Vayne", "Lux",
    "Ezreal", "Katarina", "Master Yi", "Darius", "Garen", "Annie", "Ashe",
    "Miss Fortune", "Lucian", "Jhin", "Kai'Sa", "Xayah", "Rakan", "Blitzcrank",
    "Leona", "Nautilus", "Morgana", "Janna", "Soraka", "Sona", "Nami",
    "Braum", "Alistar", "Taric", "Bard", "Pyke", "Yuumi", "Senna"
]

POSITIONS = ["TOP", "JUNGLE", "MIDDLE", "BOTTOM", "UTILITY"]
SUMMONER_NAMES = [
    "Faker", "Dopa", "TheShy", "Rookie", "Uzi", "Caps", "Perkz", "Rekkles",
    "Doublelift", "Bjergsen", "Sneaky", "Impact", "CoreJJ", "Jensen", "Licorice",
    "Player1", "Player2", "Player3", "Player4", "Player5", "Player6", "Player7"
]

def generate_participant(participant_id, team_id, position):
    """Generate một participant (player) trong match"""
    champion = random.choice(CHAMPIONS)
    summoner = random.choice(SUMMONER_NAMES) + str(random.randint(1, 999))
    
    # Stats ngẫu nhiên nhưng hợp lý
    kills = random.randint(0, 20)
    deaths = random.randint(0, 15)
    assists = random.randint(0, 25)
    win = team_id == 100 if random.random() > 0.5 else False
    
    return {
        "participantId": participant_id,
        "puuid": f"puuid_{participant_id}_{random.randint(10000, 99999)}",
        "summonerName": summoner,
        "championId": random.randint(1, 200),
        "championName": champion,
        "teamId": team_id,
        "teamPosition": position,
        "role": "SOLO" if position in ["TOP", "MIDDLE"] else "DUO",
        "lane": position,
        "win": win,
        "kills": kills,
        "deaths": deaths,
        "assists": assists,
        "champLevel": random.randint(10, 18),
        "goldEarned": random.randint(8000, 20000),
        "totalDamageDealtToChampions": random.randint(10000, 50000),
        "totalMinionsKilled": random.randint(100, 350),
        "visionScore": random.randint(10, 80),
        "item0": random.randint(1000, 4000),
        "item1": random.randint(1000, 4000),
        "item2": random.randint(1000, 4000),
        "summoner1Id": random.choice([4, 11, 12, 14]),
        "summoner2Id": random.choice([4, 11, 12, 14])
    }

def generate_match():
    """Generate một match hoàn chỉnh với 10 players"""
    match_id = f"SEA_{random.randint(1000000000, 9999999999)}"
    game_duration = random.randint(1200, 2400)  # 20-40 phút
    game_creation = int(datetime.now().timestamp() * 1000)
    
    # Generate 10 participants (5 mỗi team)
    participants = []
    for i in range(10):
        team_id = 100 if i < 5 else 200
        position = POSITIONS[i % 5]
        participants.append(generate_participant(i + 1, team_id, position))
    
    # Determine winner
    team_100_wins = random.random() > 0.5
    for p in participants:
        p["win"] = (p["teamId"] == 100) if team_100_wins else (p["teamId"] == 200)
    
    # Teams data
    teams = [
        {
            "teamId": 100,
            "win": team_100_wins,
            "objectives": {
                "baron": {"first": team_100_wins, "kills": random.randint(0, 2)},
                "dragon": {"first": team_100_wins, "kills": random.randint(1, 4)},
                "tower": {"first": team_100_wins, "kills": random.randint(3, 11)}
            },
            "bans": []
        },
        {
            "teamId": 200,
            "win": not team_100_wins,
            "objectives": {
                "baron": {"first": not team_100_wins, "kills": random.randint(0, 2)},
                "dragon": {"first": not team_100_wins, "kills": random.randint(1, 4)},
                "tower": {"first": not team_100_wins, "kills": random.randint(3, 11)}
            },
            "bans": []
        }
    ]
    
    # Full match structure (giống Riot API format)
    match_data = {
        "metadata": {
            "matchId": match_id,
            "dataVersion": "2",
            "participants": [p["puuid"] for p in participants]
        },
        "info": {
            "gameCreation": game_creation,
            "gameDuration": game_duration,
            "gameMode": "CLASSIC",
            "gameType": "MATCHED_GAME",
            "queueId": 420,  # Ranked Solo/Duo
            "platformId": "SEA",
            "gameVersion": "13.24.123.4567",
            "participants": participants,
            "teams": teams
        }
    }
    
    return match_data

def main():
    print(f"[LoL Match Generator] Starting CONTINUOUS mode...")
    print(f"  Target Topic: {TOPIC_NAME}")
    print(f"  Interval: {INTERVAL_SECONDS} seconds per match")
    print(f"  Mode: INFINITE (Press Ctrl+C to stop)")
    
    # Kafka Producer
    producer = KafkaProducer(
        bootstrap_servers=BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    
    print(f"[OK] Connected to Kafka")
    print(f"[Generating] Sending matches continuously...")
    print(f"{'='*60}\n")
    
    match_count = 0
    try:
        while True:  # Vòng lặp vô hạn
            match_data = generate_match()
            match_id = match_data['metadata']['matchId']
            
            # Send to Kafka
            producer.send(TOPIC_NAME, match_data)
            producer.flush()
            
            match_count += 1
            timestamp = datetime.now().strftime('%H:%M:%S')
            print(f"[{timestamp}] Sent Match #{match_count}: {match_id}")
            
            # Delay trước khi sinh match tiếp theo
            time.sleep(INTERVAL_SECONDS)
            # Delay trước khi sinh match tiếp theo
            time.sleep(INTERVAL_SECONDS)
        
    except KeyboardInterrupt:
        print(f"\n{'='*60}")
        print(f"[Stopped] Generated {match_count} matches total")
        print(f"  Topic: {TOPIC_NAME}")
        print(f"{'='*60}")
    except Exception as e:
        print(f"\n[ERROR] {e}")
    finally:
        producer.close()

if __name__ == "__main__":
    main()
