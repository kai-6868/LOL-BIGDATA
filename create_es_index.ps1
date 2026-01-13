# # create_es_index.ps1
# # Create Elasticsearch Index for LoL Streaming Data

# $indexName = "lol_stream"
# $elasticsearchUrl = "http://localhost:9200/$indexName"

# $indexConfig = @{
#     settings = @{
#         number_of_shards = 3
#         number_of_replicas = 1
#     }
#     mappings = @{
#         properties = @{
#             match_id = @{ type = "keyword" }
#             timestamp = @{ type = "date" }
#             window_start = @{ type = "date" }
#             window_end = @{ type = "date" }
#             champion = @{ type = "keyword" }
#             total_matches = @{ type = "integer" }
#             total_wins = @{ type = "integer" }
#             win_rate = @{ type = "float" }
#             avg_kills = @{ type = "float" }
#             avg_deaths = @{ type = "float" }
#             avg_assists = @{ type = "float" }
#             avg_gold = @{ type = "float" }
#             avg_damage = @{ type = "float" }
#         }
#     }
# } | ConvertTo-Json -Depth 10

# Write-Host "Creating Elasticsearch index: $indexName" -ForegroundColor Cyan

# try {
#     $response = Invoke-RestMethod -Method Put -Uri $elasticsearchUrl -Body $indexConfig -ContentType "application/json"
#     Write-Host "✅ Index created successfully!" -ForegroundColor Green
#     Write-Host ($response | ConvertTo-Json -Depth 5)
# } catch {
#     Write-Host "❌ Error creating index: $($_.Exception.Message)" -ForegroundColor Red
#     Write-Host "Response: $($_.Exception.Response)" -ForegroundColor Yellow
# }

# # Verify index
# Write-Host "`nVerifying index..." -ForegroundColor Cyan
# try {
#     $verify = Invoke-RestMethod -Method Get -Uri $elasticsearchUrl
#     Write-Host "✅ Index verification successful!" -ForegroundColor Green
#     Write-Host ($verify | ConvertTo-Json -Depth 5)
# } catch {
#     Write-Host "❌ Could not verify index" -ForegroundColor Red
# }
