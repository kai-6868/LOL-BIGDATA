-- Create Keyspace
CREATE KEYSPACE IF NOT EXISTS lol_data
WITH REPLICATION = {
    'class': 'SimpleStrategy',
    'replication_factor': 1
};

USE lol_data;

-- Main Table: Match Participants (Historical Data)
CREATE TABLE IF NOT EXISTS match_participants (
    match_date date,
    match_id text,
    participant_id text,
    match_timestamp bigint,
    match_duration int,
    summoner_name text,
    champion_name text,
    position text,
    team_id int,
    win boolean,
    kills int,
    deaths int,
    assists int,
    kda decimal,
    kda_calculated decimal,
    gold_earned int,
    gold_per_minute decimal,
    total_damage int,
    damage_per_minute decimal,
    cs int,
    cs_per_minute decimal,
    vision_score int,
    kill_participation decimal,
    match_hour int,
    match_day_of_week int,
    is_weekend boolean,
    kafka_offset bigint,
    kafka_partition int,
    ingestion_timestamp timestamp,
    PRIMARY KEY ((match_date, match_id), participant_id)
) WITH CLUSTERING ORDER BY (participant_id ASC)
  AND comment = 'Historical match participant data from batch layer';

-- Champion Statistics (Aggregated)
CREATE TABLE IF NOT EXISTS champion_stats (
    champion_name text PRIMARY KEY,
    games_played bigint,
    win_rate decimal,
    avg_kills decimal,
    avg_deaths decimal,
    avg_assists decimal,
    avg_kda decimal,
    avg_gpm decimal,
    avg_dpm decimal,
    last_updated timestamp
) WITH comment = 'Aggregated champion performance statistics';

-- Position Statistics (Aggregated)
CREATE TABLE IF NOT EXISTS position_stats (
    position text PRIMARY KEY,
    games_played bigint,
    win_rate decimal,
    avg_kda decimal,
    avg_gpm decimal,
    last_updated timestamp
) WITH comment = 'Aggregated position performance statistics';

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_participant_champion 
ON match_participants (champion_name);

CREATE INDEX IF NOT EXISTS idx_participant_position 
ON match_participants (position);

CREATE INDEX IF NOT EXISTS idx_participant_summoner 
ON match_participants (summoner_name);
