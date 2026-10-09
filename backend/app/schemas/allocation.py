import uuid
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field
from app.models.allocation import AllocationStatus

class AllocationCreate(BaseModel):
    donation_id: uuid.UUID
    recipient_id: uuid.UUID
    quantity_kg: float = Field(..., gt=0)
    match_score: Optional[float] = None
    score_explanation: Optional[dict[str, Any]] = None

class AllocationResponse(BaseModel):
    id: uuid.UUID
    donation_id: uuid.UUID
    recipient_id: uuid.UUID
    quantity_kg: float
    match_score: Optional[float] = None
    score_explanation: Optional[dict[str, Any]] = None
    status: AllocationStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
