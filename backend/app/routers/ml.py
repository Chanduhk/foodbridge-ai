from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.middleware.auth import CurrentUser
from app.models.user import User, UserRole
from app.schemas.ml import DemandForecastRequest, DemandForecastResponse
from app.ml.demand_prediction import get_model_metadata, SYNTHETIC_DATA_FILE
import pandas as pd
import numpy as np
import joblib
import os
from sklearn.ensemble import RandomForestRegressor
from app.ml.demand_prediction import generate_synthetic_data, feature_engineering

router = APIRouter()

# Global model cache
_model = None
_model_meta = None

def load_or_train_model():
    global _model, _model_meta
    meta = get_model_metadata()
    
    if not meta:
        from app.ml.demand_prediction import train_and_evaluate
        meta = train_and_evaluate()
        
    _model_meta = meta
    
    # We train on the fly here if model isn't persisted (simplified for M8)
    # In production, we would load a pickled model
    if not os.path.exists(SYNTHETIC_DATA_FILE):
        generate_synthetic_data()
        
    df = pd.read_csv(SYNTHETIC_DATA_FILE)
    df['date'] = pd.to_datetime(df['date'])
    df_features = feature_engineering(df)
    
    # Exclude non-feature columns
    drop_cols = ['date', 'target_demand_kg']
    X_train = df_features.drop(columns=drop_cols)
    y_train = df_features['target_demand_kg']
    
    _model = RandomForestRegressor(n_estimators=100, random_state=42)
    _model.fit(X_train, y_train)
    
    return _model, _model_meta

@router.post("/demand-forecast", response_model=DemandForecastResponse)
def get_demand_forecast(
    request: DemandForecastRequest,
    current_user: CurrentUser
):
    if current_user.role not in [UserRole.ADMIN, UserRole.RECIPIENT]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access demand forecasting"
        )
        
    global _model, _model_meta
    if _model is None:
        load_or_train_model()
        
    # Prepare input feature vector
    # This requires identical dummy columns to the training set
    df = pd.read_csv(SYNTHETIC_DATA_FILE)
    df_features = feature_engineering(df)
    drop_cols = ['date', 'target_demand_kg']
    training_cols = df_features.drop(columns=drop_cols).columns
    
    target_date = pd.to_datetime(request.target_date)
    day_of_week = target_date.weekday()
    
    input_data = {col: 0 for col in training_cols}
    input_data['day_of_week'] = day_of_week
    
    recipient_col = f"recipient_{request.recipient_id}"
    if recipient_col in input_data:
        input_data[recipient_col] = 1
        
    category_col = f"category_{request.category}"
    if category_col in input_data:
        input_data[category_col] = 1
        
    input_df = pd.DataFrame([input_data])
    
    # Predict
    predicted_demand = _model.predict(input_df)[0]
    
    return DemandForecastResponse(
        recipient_id=request.recipient_id,
        category=request.category,
        target_date=request.target_date,
        predicted_demand_kg=round(predicted_demand, 2),
        is_synthetic_data=_model_meta["is_synthetic_data"],
        model_version=_model_meta["model_version"]
    )
