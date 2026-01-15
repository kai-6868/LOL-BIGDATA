# Real Match Data Producer - README

## 📁 Files

### **Main Files:**
- `real_match_producer.py` - Main producer script
- `run_real_producer.ps1` - Simple wrapper to run producer
- `api_keys.txt` - Your Riot API keys (one per line)

### **Documentation:**
- `REAL_PRODUCER_QUICKSTART.md` - Quick start guide
- `REAL_DATA_CRAWLER_GUIDE.md` - Detailed documentation

---

## 🚀 Quick Start

### **1. Get API Keys**
Visit https://developer.riotgames.com/ and get your API key(s)

### **2. Add Keys**
Edit `api_keys.txt`:
```
RGAPI-your-first-key
RGAPI-your-second-key
```

### **3. Run**
```powershell
.\run_real_producer.ps1
```

Done! ✅

---

## 📊 Features

- ✅ **Multi-key rotation** - Use multiple API keys for higher throughput
- ✅ **Multi-region** - Rotate through NA, EUW, KR, BR for global data
- ✅ **Auto rate limiting** - Respects API limits automatically
- ✅ **Continuous collection** - Runs indefinitely until stopped
- ✅ **Kafka integration** - Publishes to `lol-matches` topic

---

## ⚙️ Configuration

Edit `real_match_producer.py` if needed:

### **Change regions (line 55):**
```python
regions = ['na1', 'euw1', 'kr', 'br1']  # Default
```

### **Change batch settings (line 321):**
```python
producer.run_continuous(
    batch_size=10,  # Matches per batch
    delay=30        # Seconds between batches
)
```

---

## 📈 Performance

| API Keys | Throughput | Records/Hour |
|----------|-----------|--------------|
| 1 | ~20 req/s | ~7,200 |
| 3 | ~60 req/s | ~21,600 |
| 5 | ~100 req/s | ~36,000 |

---

## 🛑 Stop Producer

Press `Ctrl+C` to stop gracefully.

---

## 📚 More Info

See `REAL_PRODUCER_QUICKSTART.md` for detailed guide.
