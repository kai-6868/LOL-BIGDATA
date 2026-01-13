"""
SIMPLE ML Training - Phase 5 Proof-of-Concept
Chỉ cần train được và save model là đủ
"""
from cassandra.cluster import Cluster
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
import pickle
import os

print("=" * 60)
print("PHASE 5: SIMPLE ML TRAINING")
print("=" * 60)

# 1. Connect to Cassandra
print("\n[1/5] Connecting to Cassandra...")
try:
    cluster = Cluster(['localhost'])
    session = cluster.connect('lol_data')
    print("✅ Connected")
except Exception as e:
    print(f"❌ Failed to connect: {e}")
    print("Tip: Check if Cassandra is running: docker ps | findstr cassandra")
    exit(1)

# 2. Load data (LẤY 500 RECORDS - tối đa available)
print("\n[2/5] Loading data...")
try:
    query = "SELECT kills, deaths, assists, gold_earned, win FROM match_participants LIMIT 500"
    rows = session.execute(query)
    df = pd.DataFrame(rows)
    print(f"✅ Loaded {len(df)} records")
    print(f"   Columns: {list(df.columns)}")
    
    if len(df) == 0:
        print("❌ No data found! Run Phase 4 first to populate Cassandra")
        cluster.shutdown()
        exit(1)
except Exception as e:
    print(f"❌ Failed to load data: {e}")
    cluster.shutdown()
    exit(1)

# 3. Prepare features (ĐƠN GIẢN - chỉ 4 features)
print("\n[3/5] Preparing features...")
X = df[['kills', 'deaths', 'assists', 'gold_earned']]
y = df['win']

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
print(f"✅ Train: {len(X_train)}, Test: {len(X_test)}")

# 4. Train model (SIMPLE - Logistic Regression)
print("\n[4/5] Training model...")
model = LogisticRegression(max_iter=1000)
model.fit(X_train, y_train)

# Test accuracy
accuracy = model.score(X_test, y_test)
print(f"✅ Model trained!")
print(f"   Accuracy: {accuracy:.2%}")

if accuracy > 0.50:
    print(f"   ✅ Good! (Better than random 50%)")
else:
    print(f"   ⚠️  Low accuracy, but OK for demo")

# Show some predictions
print("\n   Sample predictions:")
predictions = model.predict(X_test[:5])
actuals = y_test.iloc[:5].values
for i in range(min(5, len(X_test))):
    pred_label = "WIN" if predictions[i] else "LOSS"
    actual_label = "WIN" if actuals[i] else "LOSS"
    match = "✅" if predictions[i] == actuals[i] else "❌"
    print(f"   {match} Predicted: {pred_label}, Actual: {actual_label}")

# 5. Save model
print("\n[5/5] Saving model...")
model_dir = 'ml-layer/models'
os.makedirs(model_dir, exist_ok=True)
model_path = os.path.join(model_dir, 'win_predictor.pkl')

with open(model_path, 'wb') as f:
    pickle.dump(model, f)
print(f"✅ Model saved to: {model_path}")

# Cleanup
cluster.shutdown()

print("\n" + "=" * 60)
print("✅ PHASE 5 TRAINING COMPLETE!")
print("=" * 60)
print("\nNext: Run prediction script")
print("python ml-layer/src/predict.py")
print("=" * 60)
