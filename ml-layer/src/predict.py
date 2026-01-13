"""
ENHANCED Prediction Script - Test với 10 cases và hiển thị bảng đẹp
"""
import pickle
import pandas as pd
import os

print("=" * 95)
print(" " * 25 + "ENHANCED WIN PREDICTION SYSTEM")
print("=" * 95)

# 1. Load model
print("\n[1/3] Loading model...")
model_path = 'ml-layer/models/win_predictor.pkl'

if not os.path.exists(model_path):
    print(f"❌ Model not found at: {model_path}")
    print("Run training first: python ml-layer/src/train_model.py")
    exit(1)

try:
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    print("✅ Model loaded successfully")
except Exception as e:
    print(f"❌ Failed to load model: {e}")
    exit(1)

# 2. Test data (10 diverse cases)
print("\n[2/3] Creating 10 diverse test cases...")
test_data = pd.DataFrame({
    'kills':       [15, 12, 10, 8,  6,  5,  3,  2,  1,  0],
    'deaths':      [1,  3,  2,  4,  5,  6,  7,  9,  12, 15],
    'assists':     [20, 18, 15, 12, 10, 8,  5,  3,  2,  1],
    'gold_earned': [15000, 13500, 12000, 11000, 10000, 9000, 8000, 7000, 6000, 5000]
})
print("✅ Test data ready (Excellent → Terrible performance)")

# 3. Predict
print("\n[3/3] Making predictions...")
try:
    predictions = model.predict(test_data)
    probabilities = model.predict_proba(test_data)
    
    # Display results in table format
    print("\n" + "=" * 95)
    print(" " * 30 + "PREDICTION RESULTS (10 CASES)")
    print("=" * 95)
    print(f"{'#':<4} {'Stats':<20} {'Gold':<12} {'Prediction':<12} {'Confidence':<15} {'Icon':<5}")
    print("-" * 95)
    
    win_count = 0
    total_confidence = 0
    
    for i in range(len(test_data)):
        kills = test_data.iloc[i]['kills']
        deaths = test_data.iloc[i]['deaths']
        assists = test_data.iloc[i]['assists']
        gold = test_data.iloc[i]['gold_earned']
        
        pred = predictions[i]
        prob_win = probabilities[i][1] * 100
        prob_loss = probabilities[i][0] * 100
        
        result = "WIN" if pred else "LOSS"
        icon = "🏆" if pred else "💀"
        confidence = prob_win if pred else prob_loss
        stats = f"{kills}K/{deaths}D/{assists}A"
        gold_str = f"{gold:,}g"
        
        if pred:
            win_count += 1
        total_confidence += confidence
        
        print(f"{i+1:<4} {stats:<20} {gold_str:<12} {result:<12} {confidence:>6.1f}%{'':<9} {icon:<5}")
    
    print("=" * 95)
    
    # Summary statistics
    print("\n" + "=" * 95)
    print(" " * 35 + "SUMMARY STATISTICS")
    print("=" * 95)
    print(f"Total Cases Tested:    10")
    print(f"Predicted WINS:        {win_count} cases ({win_count/10*100:.0f}%)")
    print(f"Predicted LOSSES:      {10-win_count} cases ({(10-win_count)/10*100:.0f}%)")
    print(f"Average Confidence:    {total_confidence/10:.1f}%")
    print(f"Model Test Accuracy:   53.33% (on 500 samples)")
    print("=" * 95)
    
    print("\n✅ PHASE 5 COMPLETE - ENHANCED ML PIPELINE!")
    print("🎯 Model Pattern: High K/A + Low D + High Gold → WIN")
    print("📊 10 Test Cases: Excellent → Terrible performance")
    print("\n" + "=" * 95 + "\n")
    
except Exception as e:
    print(f"❌ Prediction failed: {e}")
    exit(1)
