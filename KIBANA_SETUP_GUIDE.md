# Kibana Dashboard Setup Guide - Phase 3

**Objective**: Create real-time dashboard to visualize LoL match data streaming from Spark → Elasticsearch

**Prerequisites**:

- ✅ Phase 3 Streaming pipeline running
- ✅ Elasticsearch with documents (29,915+)
- ✅ Kibana accessible at http://localhost:5601

---

## 📋 Quick Start (15 Minutes)

### Step 1: Access Kibana

```powershell
# Open Kibana in browser
Start-Process "http://localhost:5601"

# Expected: Kibana welcome page
```

**First time?** Kibana may take 30-60 seconds to initialize.

---

### Step 2: Create Index Pattern

#### 2.1 Navigate to Index Patterns

1. Click **☰ (Menu)** in top-left corner
2. Go to **Management** → **Stack Management**
3. Under **Kibana**, click **Index Patterns**
4. Click **Create index pattern** button

#### 2.2 Define Index Pattern

**Index pattern name**:

```
lol_matches_stream*
```

**Why the asterisk (\*)?** Allows matching future indices with similar names (e.g., `lol_matches_stream_2026`)

**Expected**: Kibana shows "Success! Your index pattern matches X indices"

#### 2.3 Configure Time Field

**Select time field**: `timestamp`

**Field format**: `epoch_millis` (Unix timestamp in milliseconds)

**Why important?** Enables time-based filtering and visualizations

Click **Create index pattern** button.

---

### Step 3: Explore Data

#### 3.1 Navigate to Discover

1. Click **☰ (Menu)** → **Analytics** → **Discover**
2. Verify index pattern shows: `lol_matches_stream*`
3. Set time range: **Last 15 minutes** (top-right corner)

#### 3.2 Verify Data Fields

You should see fields like:

- `timestamp` - Match timestamp
- `match_id` - Unique match identifier
- `summoner_name` - Player name
- `champion_name` - Champion played
- `position` - Lane position
- `win` - Win/Loss (boolean)
- `kills`, `deaths`, `assists` - KDA stats
- `kda` - Calculated KDA ratio
- `gold_per_minute` - GPM metric
- `damage_per_minute` - DPM metric
- `cs_per_minute` - CSPM metric

#### 3.3 Test Live Updates

1. Click **🔄 Refresh** button (top-right)
2. Set **Refresh interval** to **5 seconds**
3. Watch document count increase in real-time

**Expected**: New documents appear every 5-10 seconds (190-200 docs/10sec)

---

## 📊 Step 4: Create Visualizations

### Visualization 1: Document Count Over Time

**Type**: Line chart showing data ingestion rate

**Steps**:

1. Go to **☰ → Visualize Library** → **Create visualization**
2. Select **Lens** (recommended for beginners)
3. Select index pattern: `lol_matches_stream*`

**Configuration**:

- **X-axis**: `timestamp` (date histogram)
  - Interval: `Auto` or `1 minute`
- **Y-axis**: `Count` (document count)

**Customization**:

- Title: "Match Data Ingestion Rate"
- Y-axis label: "Documents per Minute"
- Chart type: Area or Line

**Save**: Click **Save** → Name: "Ingestion Rate"

---

### Visualization 2: Win Rate by Champion

**Type**: Pie chart showing champion performance

**Steps**:

1. Create new visualization → Select **Lens**
2. Select index pattern: `lol_matches_stream*`

**Configuration**:

- **Slice by**: `champion_name.keyword` (Terms aggregation)
  - Size: Top 10 champions
- **Metric**: `win` (Average)
  - Formula: `average(win) * 100` (converts to percentage)

**Alternative (Manual Filter)**:

- **Slice by**: `champion_name.keyword`
- **Metric**: Count
- **Filter**: Add two series:
  - Wins: Filter `win:true`
  - Total games: No filter
  - Calculate win rate: `(Wins / Total) * 100`

**Customization**:

- Title: "Champion Win Rates"
- Show percentages
- Legend position: Right

**Save**: Name: "Champion Win Rates"

---

### Visualization 3: Average KDA by Position

**Type**: Bar chart comparing lane performance

**Steps**:

1. Create new visualization → Select **Lens**
2. Select index pattern: `lol_matches_stream*`

**Configuration**:

- **X-axis**: `position.keyword` (Terms)
  - Order: Top, Support, Jungle, Mid, ADC
- **Y-axis**: `kda` (Average)

**Customization**:

- Title: "Average KDA by Position"
- Y-axis label: "KDA Ratio"
- Color: Gradient (low to high)
- Show data labels

**Save**: Name: "KDA by Position"

---

### Visualization 4: Gold Per Minute Distribution

**Type**: Histogram showing GPM spread

**Steps**:

1. Create new visualization → Select **Lens**
2. Select index pattern: `lol_matches_stream*`

**Configuration**:

- **X-axis**: `gold_per_minute` (Histogram)
  - Interval: 50 (or Auto)
  - Min: 0, Max: 1000
- **Y-axis**: Count

**Customization**:

- Title: "Gold Per Minute Distribution"
- X-axis label: "Gold per Minute"
- Y-axis label: "Player Count"
- Color: Single color or gradient

**Save**: Name: "GPM Distribution"

---

### Visualization 5: Damage Per Minute by Champion

**Type**: Horizontal bar chart (Top 15 champions)

**Steps**:

1. Create visualization → Select **Lens**

**Configuration**:

- **Y-axis**: `champion_name.keyword` (Terms, Top 15)
- **X-axis**: `damage_per_minute` (Average)
- **Sort**: By metric (descending)

**Customization**:

- Title: "Top 15 Champions by Damage Output"
- Show data labels

**Save**: Name: "DPM by Champion"

---

## 🎨 Step 5: Build Dashboard

### 5.1 Create Dashboard

1. Go to **☰ → Dashboard**
2. Click **Create dashboard**
3. Click **Add from library**

### 5.2 Add Visualizations

Select all saved visualizations:

- ✅ Ingestion Rate
- ✅ Champion Win Rates
- ✅ KDA by Position
- ✅ GPM Distribution
- ✅ DPM by Champion

### 5.3 Arrange Layout

**Recommended Layout** (2-column grid):

```
┌─────────────────────────────────────────────────┐
│  Ingestion Rate (full width)                    │
├───────────────────────┬─────────────────────────┤
│ Champion Win Rates    │ KDA by Position         │
├───────────────────────┼─────────────────────────┤
│ GPM Distribution      │ DPM by Champion         │
└───────────────────────┴─────────────────────────┘
```

**Tips**:

- Drag to resize panels
- Use **Grid** snap for alignment
- **Ingestion Rate** at top (shows pipeline health)

### 5.4 Configure Auto-Refresh

**Top-right corner**:

1. Click **🕒 Time picker**
2. Set range: **Last 15 minutes** or **Last 1 hour**
3. Click **🔄 Refresh**
4. Select interval: **5 seconds** or **10 seconds**

**Expected**: Dashboard updates automatically, showing live data changes

### 5.5 Save Dashboard

1. Click **Save** button (top-right)
2. **Title**: "LoL Match Analytics - Real-Time"
3. **Description**: "Live streaming data from Kafka → Spark → Elasticsearch"
4. ✅ **Store time with dashboard** (checked)
5. Click **Save**

---

## 🔍 Step 6: Verify Live Updates

### 6.1 Watch Data Flow

With auto-refresh enabled (5-10 seconds), observe:

1. **Ingestion Rate**: Line chart should show continuous data points
2. **Champion Win Rates**: Percentages adjust as more games are played
3. **KDA by Position**: Averages update with new matches
4. **GPM Distribution**: Histogram bars grow
5. **DPM by Champion**: Rankings may change

### 6.2 Check Document Count

**Top-right corner** shows:

```
Hits: 29,915+ (increasing)
```

**Expected growth**: ~190-200 documents every 10 seconds

### 6.3 Test Time Range Filters

1. Change time range to **Last 5 minutes**
   - Dashboard should show fewer documents
2. Change to **Last 1 hour**
   - Dashboard shows more historical data
3. Return to **Last 15 minutes** for real-time focus

---

## 📈 Step 7: Advanced Features (Optional)

### 7.1 Add Filters

**Dashboard-level filters**:

1. Click **Add filter** button
2. Examples:
   - `position.keyword is ADC` - Only ADC players
   - `win is true` - Only winning games
   - `kda > 3.0` - High-performance games

### 7.2 Create Markdown Panel

Add text annotations:

1. Click **Add panel** → **Markdown**
2. Content example:

```markdown
## LoL Match Analytics Dashboard

**Data Source**: Kafka → Spark Streaming → Elasticsearch

**Update Frequency**: Real-time (5-second refresh)

**Metrics**:

- Win rates by champion
- KDA performance by position
- Gold and damage efficiency
```

### 7.3 Add Controls

**Interactive filters**:

1. Click **Add panel** → **Controls**
2. Add controls for:
   - Position (dropdown)
   - Champion (dropdown)
   - Win (toggle)

**Users can filter dashboard interactively!**

---

## ✅ Verification Checklist

After completing setup, verify:

- [x] **Kibana accessible** at http://localhost:5601
- [x] **Index pattern created**: `lol_matches_stream*`
- [x] **Discover shows data**: 29,915+ documents visible
- [x] **5 visualizations created**:
  - [x] Ingestion Rate (line chart)
  - [x] Champion Win Rates (pie chart)
  - [x] KDA by Position (bar chart)
  - [x] GPM Distribution (histogram)
  - [x] DPM by Champion (horizontal bar)
- [x] **Dashboard created**: "LoL Match Analytics - Real-Time"
- [x] **Auto-refresh enabled**: 5-10 second interval
- [x] **Live updates working**: Document count increases
- [x] **Time filter working**: Can adjust time range
- [x] **Dashboard saved**: Can reload and see same view

---

## 🎯 Phase 3 Completion Criteria

✅ **Phase 3 is complete when**:

1. Spark Streaming job running stable ✅
2. Elasticsearch indexing (29,915+ docs) ✅
3. Kibana dashboard showing live data ✅
4. Can see real-time updates every 5-10 seconds ✅

**Command to verify**:

```powershell
# Check Spark UI
Start-Process "http://localhost:4040"

# Check Elasticsearch count
Invoke-WebRequest "http://localhost:9200/lol_matches_stream/_count?pretty"

# Check Kibana dashboard
Start-Process "http://localhost:5601/app/dashboards"
```

**Expected**: All 3 UIs accessible, data flowing and updating

---

## 🚨 Troubleshooting

### Issue: No Data in Kibana Discover

**Check**:

```powershell
# Verify Elasticsearch has documents
curl "http://localhost:9200/lol_matches_stream/_count?pretty"
```

**If count is 0**: Spark job not running or not indexing

- Restart Spark job: `.\submit_spark_job.ps1`
- Check logs: `docker logs spark-master --tail 50`

**If count > 0 but Kibana shows nothing**:

- Check time range (top-right) - expand to "Last 24 hours"
- Verify index pattern matches: `lol_matches_stream*`
- Refresh index pattern: Management → Index Patterns → 🔄 Refresh

---

### Issue: Visualizations Show "No Results"

**Common causes**:

1. **Time range too narrow**: Expand to Last 1 hour
2. **Filters too restrictive**: Remove dashboard filters
3. **Field not available**: Check field name in Discover
4. **Data type mismatch**: Ensure using `.keyword` for text fields

**Fix**:

- Go to Discover first to verify fields exist
- Check field types (string vs keyword vs number)
- Recreate visualization with correct field names

---

### Issue: Dashboard Not Auto-Refreshing

**Steps**:

1. Click **🔄 Refresh** button (top-right)
2. Ensure refresh interval is set (e.g., "5 seconds")
3. Check browser console for errors (F12)
4. Reload page (Ctrl+F5)

**If still not working**:

- Kibana may be under heavy load
- Increase refresh interval to 10 or 30 seconds
- Check Elasticsearch cluster health

---

### Issue: Kibana Slow or Unresponsive

**Optimization**:

1. Reduce time range (Last 15 min instead of Last 24 hours)
2. Decrease refresh interval (30 sec instead of 5 sec)
3. Simplify visualizations (fewer aggregations)
4. Close unused browser tabs

**Check Elasticsearch**:

```powershell
# Check cluster health
curl "http://localhost:9200/_cluster/health?pretty"

# Should be green or yellow, not red
```

---

## 📚 Next Steps

After Phase 3 completion with Kibana:

1. **Export Dashboard**: Save dashboard JSON for backup
2. **Create More Dashboards**:
   - Champion-specific analysis
   - Position meta trends
   - Time-of-day patterns
3. **Set Up Alerts** (Phase 6):
   - Win rate drops below threshold
   - Data ingestion stops
4. **Proceed to Phase 4**: Batch Layer (HDFS + Cassandra)

---

## 📖 Resources

- [Kibana User Guide](https://www.elastic.co/guide/en/kibana/current/index.html)
- [Lens Documentation](https://www.elastic.co/guide/en/kibana/current/lens.html)
- [Dashboard Best Practices](https://www.elastic.co/guide/en/kibana/current/dashboard.html)

---

**Created**: January 13, 2026  
**Phase**: 3.7 - Kibana Dashboard Setup  
**Status**: 🔄 In Progress → ✅ Complete after following guide
