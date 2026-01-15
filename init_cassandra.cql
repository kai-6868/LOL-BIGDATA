-- init_cassandra.cql
-- Cassandra Schema Initialization for LoL Match Data

-- Create Keyspace
CREATE KEYSPACE IF NOT EXISTS lol_data
WITH replication = {
  'class': 'SimpleStrategy',
  'replication_factor': 1
};

-- Use Keyspace
USE lol_data;

-- Create Table for Match Participants
CREATE TABLE IF NOT EXISTS match_participants (
  match_id UUID,
  player_id INT,
  champion TEXT,
  role TEXT,
  team INT,
  kills INT,
  deaths INT,
  assists INT,
  gold_earned INT,
  damage_dealt INT,
  cs INT,
  vision_score INT,
  win BOOLEAN,
  timestamp TIMESTAMP,
  PRIMARY KEY ((match_id), player_id)
) WITH CLUSTERING ORDER BY (player_id ASC);

CREATE INDEX IF NOT EXISTS idx_champion ON match_participants (champion);
CREATE INDEX IF NOT EXISTS idx_timestamp ON match_participants (timestamp);
CREATE INDEX IF NOT EXISTS idx_role ON match_participants (role);

-- Create Table for Match Stats (aggregated match-level data)
CREATE TABLE IF NOT EXISTS match_stats (
  match_id TEXT PRIMARY KEY,
  game_duration INT,
  game_mode TEXT,
  game_version TEXT,
  blue_team_win BOOLEAN,
  blue_kills INT,
  blue_deaths INT,
  blue_assists INT,
  blue_gold INT,
  blue_towers INT,
  blue_dragons INT,
  blue_barons INT,
  red_kills INT,
  red_deaths INT,
  red_assists INT,
  red_gold INT,
  red_towers INT,
  red_dragons INT,
  red_barons INT,
  created_at TIMESTAMP
);

-- Create Index on match_stats
CREATE INDEX IF NOT EXISTS idx_match_mode ON match_stats (game_mode);
CREATE INDEX IF NOT EXISTS idx_match_created ON match_stats (created_at);

-- Verify Schema
DESCRIBE TABLE match_participants;
DESCRIBE TABLE match_stats;
