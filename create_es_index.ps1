# Create Elasticsearch Index for LoL Streaming Data
# This creates the index that Spark will write to

$indexName = "lol_matches_stream"
$elasticsearchUrl = "http://localhost:9200/$indexName"

Write-Host "===========================================================" -ForegroundColor Cyan
Write-Host "  Creating Elasticsearch Index: $indexName" -ForegroundColor Cyan
Write-Host "===========================================================" -ForegroundColor Cyan
Write-Host ""

# Delete existing index if exists
Write-Host "Checking for existing index..." -ForegroundColor Yellow
try {
    Invoke-RestMethod -Method Delete -Uri $elasticsearchUrl -ErrorAction SilentlyContinue
    Write-Host "  ✓ Deleted existing index" -ForegroundColor Green
} catch {
    Write-Host "  ℹ No existing index to delete" -ForegroundColor Cyan
}

# Index configuration
$indexConfig = @{
    settings = @{
        number_of_shards = 3
        number_of_replicas = 1
        refresh_interval = "5s"
    }
    mappings = @{
        properties = @{
            # Match metadata
            match_id = @{ type = "keyword" }
            game_creation = @{ type = "date" }
            game_duration = @{ type = "integer" }
            "@timestamp" = @{ type = "date" }
            
            # Participant data
            participant_id = @{ type = "integer" }
            summoner_name = @{ 
                type = "text"
                fields = @{
                    keyword = @{ type = "keyword" }
                }
            }
            champion_name = @{ 
                type = "text"
                fields = @{
                    keyword = @{ type = "keyword" }
                }
            }
            team_id = @{ type = "integer" }
            team_position = @{ type = "keyword" }
            win = @{ type = "boolean" }
            
            # Stats
            kills = @{ type = "integer" }
            deaths = @{ type = "integer" }
            assists = @{ type = "integer" }
            kda = @{ type = "float" }
            total_damage_dealt = @{ type = "long" }
            gold_earned = @{ type = "integer" }
            cs = @{ type = "integer" }
            vision_score = @{ type = "integer" }
            
            # Calculated metrics
            damage_per_minute = @{ type = "float" }
            cs_per_minute = @{ type = "float" }
        }
    }
} | ConvertTo-Json -Depth 10

Write-Host ""
Write-Host "Creating index with mapping..." -ForegroundColor Yellow

try {
    $response = Invoke-RestMethod -Method Put -Uri $elasticsearchUrl -Body $indexConfig -ContentType "application/json"
    Write-Host ""
    Write-Host "===========================================================" -ForegroundColor Cyan
    Write-Host "  ✅ Index created successfully!" -ForegroundColor Green
    Write-Host "===========================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Index: $indexName" -ForegroundColor Cyan
    Write-Host "Shards: 3" -ForegroundColor Cyan
    Write-Host "Replicas: 1" -ForegroundColor Cyan
    Write-Host ""
} catch {
    Write-Host ""
    Write-Host "===========================================================" -ForegroundColor Red
    Write-Host "  ❌ Error creating index" -ForegroundColor Red
    Write-Host "===========================================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Troubleshooting:" -ForegroundColor Yellow
    Write-Host "  1. Check Elasticsearch is running: docker ps | Select-String elasticsearch"
    Write-Host "  2. Check Elasticsearch health: curl http://localhost:9200/_cluster/health"
    Write-Host "  3. Check Elasticsearch logs: docker logs elasticsearch --tail 50"
    Write-Host ""
    exit 1
}

# Verify index
Write-Host "Verifying index..." -ForegroundColor Yellow
try {
    $verify = Invoke-RestMethod -Method Get -Uri $elasticsearchUrl
    Write-Host "  ✓ Index verified successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Index details:" -ForegroundColor Cyan
    Write-Host "  Mappings: $($verify.$indexName.mappings.properties.Count) fields"
    Write-Host "  Settings: Configured"
    Write-Host ""
} catch {
    Write-Host "  ❌ Could not verify index" -ForegroundColor Red
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Yellow
    Write-Host ""
}

Write-Host "===========================================================" -ForegroundColor Cyan
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Start data generator: python lol_match_generator.py"
Write-Host "  2. Start Spark streaming: .\start_spark_streaming.ps1"
Write-Host "  3. Check data: curl http://localhost:9200/$indexName/_count"
Write-Host "===========================================================" -ForegroundColor Cyan
Write-Host ""
