"""
Demand Prediction and Analytics Module for FoodBridge AI.
"""

import os
import json
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

logger = logging.getLogger(__name__)

# Paths for persisting models and synthetic data
ML_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_META_FILE = os.path.join(ML_DIR, "model_meta.json")
SYNTHETIC_DATA_FILE = os.path.join(ML_DIR, "synthetic_demand_data.csv")

def generate_synthetic_data(days=120, records_per_day=5):
    """
    Generate synthetic development data since insufficient real data exists.
    DO NOT USE IN PRODUCTION AS REAL PERFORMANCE.
    """
    logger.warning("Generating synthetic data. NOT representative of real-world performance.")
    
    np.random.seed(42)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    
    data = []
    
    # Simulate 5 recipient organizations
    recipients = [f"Recipient_{i}" for i in range(1, 6)]
    categories = ["Produce", "Dairy", "Bakery", "Meat", "Non-perishable"]
    
    for current_date in dates:
        for _ in range(records_per_day):
            recipient = np.random.choice(recipients)
            category = np.random.choice(categories)
            
            # Base demand depends on category and day of week
            base_demand = {
                "Produce": 50,
                "Dairy": 20,
                "Bakery": 30,
                "Meat": 15,
                "Non-perishable": 100
            }[category]
            
            # Weekend surge
            day_of_week = current_date.weekday()
            weekend_multiplier = 1.5 if day_of_week >= 5 else 1.0
            
            # Random noise
            noise = np.random.normal(0, 5)
            
            target_demand = max(5, int(base_demand * weekend_multiplier + noise))
            
            data.append({
                "date": current_date,
                "recipient": recipient,
                "category": category,
                "day_of_week": day_of_week,
                "target_demand_kg": target_demand
            })
            
    df = pd.DataFrame(data)
    df.to_csv(SYNTHETIC_DATA_FILE, index=False)
    return df

def feature_engineering(df):
    """Extract features without future leakage."""
    # Convert categorical variables
    df_encoded = pd.get_dummies(df, columns=['recipient', 'category'])
    return df_encoded

def train_and_evaluate():
    """
    Train Baseline and Random Forest models using time-based splitting.
    """
    # Load or generate data
    if not os.path.exists(SYNTHETIC_DATA_FILE):
        df = generate_synthetic_data()
    else:
        df = pd.read_csv(SYNTHETIC_DATA_FILE)
        df['date'] = pd.to_datetime(df['date'])
        
    df = df.sort_values('date').reset_index(drop=True)
    
    # 1. Feature Engineering
    df_features = feature_engineering(df)
    
    # 2. Time-Based Split (Last 30 days as test)
    test_cutoff = df['date'].max() - timedelta(days=30)
    
    train_df = df_features[df_features['date'] <= test_cutoff]
    test_df = df_features[df_features['date'] > test_cutoff]
    
    # Exclude non-feature columns
    drop_cols = ['date', 'target_demand_kg']
    X_train = train_df.drop(columns=drop_cols)
    y_train = train_df['target_demand_kg']
    
    X_test = test_df.drop(columns=drop_cols)
    y_test = test_df['target_demand_kg']
    
    # 3. Baseline Model (Historical Average per category)
    # Re-calculate averages on TRAIN set only to prevent data leakage
    # We'll compute the mean for each category using the original train dataframe
    train_original = df[df['date'] <= test_cutoff]
    category_means = train_original.groupby('category')['target_demand_kg'].mean().to_dict()
    
    # Predict using baseline
    test_original = df[df['date'] > test_cutoff]
    y_pred_baseline = test_original['category'].map(category_means).fillna(train_original['target_demand_kg'].mean())
    
    baseline_mae = mean_absolute_error(y_test, y_pred_baseline)
    baseline_rmse = np.sqrt(mean_squared_error(y_test, y_pred_baseline))
    
    # 4. ML Model (Random Forest)
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    y_pred_rf = model.predict(X_test)
    
    rf_mae = mean_absolute_error(y_test, y_pred_rf)
    rf_rmse = np.sqrt(mean_squared_error(y_test, y_pred_rf))
    
    # 5. Save Model Metadata
    meta = {
        "model_version": "1.0",
        "training_date": datetime.now().isoformat(),
        "is_synthetic_data": True,
        "training_records": len(train_df),
        "test_records": len(test_df),
        "train_period": f"{train_df['date'].min().date()} to {train_df['date'].max().date()}",
        "test_period": f"{test_df['date'].min().date()} to {test_df['date'].max().date()}",
        "features": list(X_train.columns),
        "metrics": {
            "baseline": {
                "mae": round(baseline_mae, 2),
                "rmse": round(baseline_rmse, 2)
            },
            "random_forest": {
                "mae": round(rf_mae, 2),
                "rmse": round(rf_rmse, 2)
            }
        }
    }
    
    with open(MODEL_META_FILE, 'w') as f:
        json.dump(meta, f, indent=4)
        
    return meta

def get_model_metadata():
    """Retrieve saved model metadata."""
    if not os.path.exists(MODEL_META_FILE):
        return None
    with open(MODEL_META_FILE, 'r') as f:
        return json.load(f)

if __name__ == "__main__":
    print("Running Demand Prediction Pipeline...")
    results = train_and_evaluate()
    print("\n--- Model Evaluation Results ---")
    print(json.dumps(results, indent=2))
