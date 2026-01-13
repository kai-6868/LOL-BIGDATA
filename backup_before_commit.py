"""
Backup Script - Lưu trữ dữ liệu quan trọng trước khi commit

Tạo backup của:
- ML models
- Checkpoints
- Logs
- Configuration
"""

import os
import shutil
from datetime import datetime
import json

BACKUP_DIR = "backups"
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

def create_backup():
    """Tạo backup folder với timestamp"""
    backup_path = os.path.join(BACKUP_DIR, f"backup_{TIMESTAMP}")
    os.makedirs(backup_path, exist_ok=True)
    print(f"✅ Created backup directory: {backup_path}")
    return backup_path

def backup_ml_models(backup_path):
    """Backup ML models"""
    source = "ml-layer/models"
    if os.path.exists(source):
        dest = os.path.join(backup_path, "ml-models")
        shutil.copytree(source, dest, dirs_exist_ok=True)
        print(f"✅ Backed up ML models: {dest}")
        
        # Count files
        count = len([f for f in os.listdir(dest) if f.endswith('.pkl')])
        print(f"   - {count} model file(s) saved")
    else:
        print(f"⚠️ ML models directory not found: {source}")

def backup_checkpoints(backup_path):
    """Backup Spark checkpoints metadata"""
    source = "checkpoints"
    if os.path.exists(source):
        dest = os.path.join(backup_path, "checkpoints")
        
        # Chỉ backup metadata files (không backup toàn bộ - quá lớn)
        os.makedirs(dest, exist_ok=True)
        
        for root, dirs, files in os.walk(source):
            for file in files:
                if file in ['metadata', 'offsets']:
                    src_file = os.path.join(root, file)
                    rel_path = os.path.relpath(root, source)
                    dest_dir = os.path.join(dest, rel_path)
                    os.makedirs(dest_dir, exist_ok=True)
                    shutil.copy2(src_file, dest_dir)
        
        print(f"✅ Backed up checkpoint metadata: {dest}")
    else:
        print(f"⚠️ Checkpoints directory not found: {source}")

def backup_configs(backup_path):
    """Backup configuration files"""
    config_files = [
        "docker-compose.yml",
        "requirements.txt",
        "data-generator/config/config.yaml",
        "streaming-layer/config/spark_config.yaml",
        "batch-layer/config/batch_config.yaml",
        "batch-layer/config/cassandra_schema.cql"
    ]
    
    dest = os.path.join(backup_path, "configs")
    os.makedirs(dest, exist_ok=True)
    
    for config in config_files:
        if os.path.exists(config):
            dest_file = os.path.join(dest, os.path.basename(config))
            shutil.copy2(config, dest_file)
            print(f"✅ Backed up: {config}")
    
    print(f"✅ Configuration files backed up to: {dest}")

def save_system_state(backup_path):
    """Save system state information"""
    state = {
        "timestamp": TIMESTAMP,
        "phases_completed": [
            "Phase 1: Infrastructure",
            "Phase 2: Data Ingestion",
            "Phase 3: Speed Layer (Streaming)",
            "Phase 4: Batch Layer",
            "Phase 5: ML Layer"
        ],
        "architecture": "Lambda Architecture",
        "components": {
            "kafka": "localhost:29092",
            "spark": "localhost:4040",
            "elasticsearch": "localhost:9200",
            "kibana": "localhost:5601",
            "cassandra": "localhost:9042",
            "hdfs": "localhost:9870"
        },
        "ml_model": {
            "type": "LogisticRegression",
            "features": ["kills", "deaths", "assists", "gold_earned"],
            "accuracy": "53.33%",
            "training_samples": 500,
            "test_cases": 10
        }
    }
    
    state_file = os.path.join(backup_path, "system_state.json")
    with open(state_file, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
    
    print(f"✅ System state saved: {state_file}")

def create_restore_instructions(backup_path):
    """Tạo hướng dẫn restore"""
    instructions = """# RESTORE INSTRUCTIONS

## Để restore backup này:

### 1. Restore ML Models
```bash
# Copy models từ backup
cp -r backups/backup_{timestamp}/ml-models/* ml-layer/models/
```

### 2. Restore Configurations
```bash
# Không cần - configs đã có trong Git
```

### 3. Retrain Model (nếu cần)
```bash
# Generate new data và train lại
python data-generator/src/generator.py --mode continuous
python batch-layer/src/batch_consumer.py --batches 1
docker exec spark-master spark-submit ... (xem PHASE4_GUIDE.md)
python ml-layer/src/train_model.py
```

### 4. Restart Services
```bash
# Start all Docker services
docker compose up -d

# Verify services
docker compose ps

# Start data generator
python data-generator/src/generator.py --mode continuous

# Submit Spark streaming job
.\\submit_spark_job.ps1
```

### 5. Verify System
```bash
# Verify Elasticsearch
curl http://localhost:9200/_cat/health

# Verify Kibana
curl http://localhost:5601/api/status

# Verify Cassandra
docker exec cassandra cqlsh -e "DESCRIBE KEYSPACES;"

# Test ML predictions
python ml-layer/src/predict.py
```

## System State
- Xem system_state.json để biết cấu hình gốc
- Phases completed: Phase 1-5
- ML model: LogisticRegression với 4 features
- Accuracy: 53.33% trên 500 samples

## Notes
- Data files KHÔNG được backup (quá lớn)
- Có thể generate lại data từ data-generator
- Checkpoints có thể recreate khi restart Spark
- Logs không quan trọng - sẽ tạo mới khi chạy
"""
    
    restore_file = os.path.join(backup_path, "RESTORE.md")
    with open(restore_file, 'w', encoding='utf-8') as f:
        f.write(instructions.replace("{timestamp}", TIMESTAMP))
    
    print(f"✅ Restore instructions created: {restore_file}")

def main():
    """Main backup process"""
    print("\n" + "="*70)
    print("  BACKUP SCRIPT - Lưu trữ dữ liệu quan trọng")
    print("="*70 + "\n")
    
    # Create backup directory
    backup_path = create_backup()
    
    # Backup components
    backup_ml_models(backup_path)
    backup_checkpoints(backup_path)
    backup_configs(backup_path)
    save_system_state(backup_path)
    create_restore_instructions(backup_path)
    
    print("\n" + "="*70)
    print("✅ BACKUP COMPLETED SUCCESSFULLY!")
    print("="*70)
    print(f"\nBackup location: {backup_path}")
    print("\nBạn có thể an tâm commit và push Git.")
    print("Các file lớn (data, logs, checkpoints) đã được gitignore.\n")

if __name__ == "__main__":
    main()
