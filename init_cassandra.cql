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

-- Create Secondary Indexes for Query Performance
CREATE INDEX IF NOT EXISTS idx_champion ON match_participants (champion);
CREATE INDEX IF NOT EXISTS idx_timestamp ON match_participants (timestamp);
CREATE INDEX IF NOT EXISTS idx_role ON match_participants (role);

-- Verify Schema
DESCRIBE TABLE match_participants;
