import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from app.models.delivery import DeliveryStatus

class DeliveryCreate(BaseModel):
    allocation_id: uuid.UUID
    scheduled_pickup: Optional[datetime] = None
    notes: Optional[str] = None
    distance_km: Optional[float] = None
    estimated_duration_min: Optional[int] = None

class DeliveryUpdate(BaseModel):
    status: Optional[DeliveryStatus] = None
    notes: Optional[str] = None
    actual_pickup: Optional[datetime] = None
    actual_delivery: Optional[datetime] = None

class DeliveryResponse(BaseModel):
    id: uuid.UUID
    allocation_id: uuid.UUID
    volunteer_id: Optional[uuid.UUID] = None
    scheduled_pickup: Optional[datetime] = None
    actual_pickup: Optional[datetime] = None
    actual_delivery: Optional[datetime] = None
    status: DeliveryStatus
    notes: Optional[str] = None
    distance_km: Optional[float] = None
    estimated_duration_min: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

class LogisticsRecommendation(BaseModel):
    allocation_id: uuid.UUID
    recommended_volunteer_ids: list[uuid.UUID]
    distance_km: float
    estimated_duration_min: int
    recommendation_notes: str
