-- init_cassandra.cql
-- Cassandra Schema for Real LoL Match Data

-- Create Keyspace
CREATE KEYSPACE IF NOT EXISTS lol_data
WITH replication = {
  'class': 'SimpleStrategy',
  'replication_factor': 1
};

USE lol_data;

-- Table 1: Player Performance (per player per match)
CREATE TABLE IF NOT EXISTS player_performance (
  match_id TEXT,
  summoner_name TEXT,
  champion_name TEXT,
  position TEXT,
  team_id INT,
  win BOOLEAN,
  kills INT,
  deaths INT,
  assists INT,
  kda DOUBLE,
  gold_earned INT,
  total_damage INT,
  cs INT,
  vision_score INT,
  match_timestamp BIGINT,
  match_duration INT,
  match_date TEXT,
  PRIMARY KEY ((match_id), summoner_name)
) WITH CLUSTERING ORDER BY (summoner_name ASC);

CREATE INDEX IF NOT EXISTS idx_player_champion ON player_performance (champion_name);
CREATE INDEX IF NOT EXISTS idx_player_position ON player_performance (position);
CREATE INDEX IF NOT EXISTS idx_player_date ON player_performance (match_date);

-- Table 2: Match Summary (aggregated per match)
CREATE TABLE IF NOT EXISTS match_summary (
  match_id TEXT PRIMARY KEY,
  match_timestamp BIGINT,
  match_duration INT,
  match_date TEXT,
  blue_team_win BOOLEAN,
  blue_kills INT,
  blue_deaths INT,
  blue_assists INT,
  blue_gold BIGINT,
  blue_damage BIGINT,
  red_kills INT,
  red_deaths INT,
  red_assists INT,
  red_gold BIGINT,
  red_damage BIGINT,
  total_players INT,
  created_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_summary_date ON match_summary (match_date);
CREATE INDEX IF NOT EXISTS idx_summary_timestamp ON match_summary (created_at);

-- Verify Schema
DESCRIBE TABLE player_performance;
DESCRIBE TABLE match_summary;
