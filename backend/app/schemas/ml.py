from pydantic import BaseModel
from typing import Dict, Any, List

class DemandForecastRequest(BaseModel):
    recipient_id: str
    category: str
    target_date: str

class DemandForecastResponse(BaseModel):
    recipient_id: str
    category: str
    target_date: str
    predicted_demand_kg: float
    is_synthetic_data: bool
    model_version: str
    warning: str = "This prediction is advisory decision support only and must not bypass eligibility checks."

class AnalyticsResponse(BaseModel):
    total_food_rescued_kg: float
    total_deliveries_completed: int
    active_recipients: int
    unmet_demand_kg: float
