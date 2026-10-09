import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
from app.models.recipient import OrgType, DemandStatus

# --- Recipient Profile Schemas ---

class RecipientProfileCreate(BaseModel):
    organization_name: str = Field(..., min_length=2, max_length=255)
    organization_type: OrgType = Field(default=OrgType.NGO)
    license_number: Optional[str] = Field(None, max_length=100)
    capacity_kg: float = Field(default=100.0, ge=0)
    operating_hours: Optional[str] = Field(None, max_length=255)
    dietary_restrictions: Optional[str] = None
    food_categories_accepted: List[str] = Field(default_factory=list)

class RecipientProfileUpdate(BaseModel):
    organization_name: Optional[str] = Field(None, min_length=2, max_length=255)
    organization_type: Optional[OrgType] = None
    license_number: Optional[str] = Field(None, max_length=100)
    capacity_kg: Optional[float] = Field(None, ge=0)
    operating_hours: Optional[str] = Field(None, max_length=255)
    dietary_restrictions: Optional[str] = None
    food_categories_accepted: Optional[List[str]] = None

class RecipientProfileResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    organization_name: str
    organization_type: OrgType
    license_number: Optional[str] = None
    is_verified: bool
    capacity_kg: float
    current_occupancy_kg: float
    operating_hours: Optional[str] = None
    dietary_restrictions: Optional[str] = None
    food_categories_accepted: List[str]
    verified_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

# --- Recipient Demand Schemas ---

class RecipientDemandCreate(BaseModel):
    food_category: str = Field(..., min_length=2, max_length=100)
    quantity_requested: float = Field(..., gt=0)
    unit: str = Field(default="kg", max_length=20)
    priority: int = Field(default=1, ge=1, le=5)
    needed_by: datetime
    dietary_requirements: Optional[str] = None

    @field_validator("needed_by")
    @classmethod
    def check_needed_by(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("needed_by date must include timezone info")
        return v

class RecipientDemandUpdate(BaseModel):
    quantity_requested: Optional[float] = Field(None, gt=0)
    priority: Optional[int] = Field(None, ge=1, le=5)
    needed_by: Optional[datetime] = None
    dietary_requirements: Optional[str] = None
    status: Optional[DemandStatus] = None

    @field_validator("needed_by")
    @classmethod
    def check_needed_by(cls, v: Optional[datetime]) -> Optional[datetime]:
        if v and v.tzinfo is None:
            raise ValueError("needed_by date must include timezone info")
        return v

class RecipientDemandResponse(BaseModel):
    id: uuid.UUID
    recipient_id: uuid.UUID
    food_category: str
    quantity_requested: float
    unit: str
    priority: int
    needed_by: datetime
    status: DemandStatus
    dietary_requirements: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

# --- Matching Schemas ---

class MatchResult(BaseModel):
    recipient_id: uuid.UUID
    match_score: float
    factor_scores: Dict[str, float]
    recommended_quantity_kg: float
    explanation: str
    warnings: List[str]

class MatchListResponse(BaseModel):
    donation_id: uuid.UUID
    matches: List[MatchResult]
