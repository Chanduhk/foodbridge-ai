import uuid
from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field, field_validator
from app.models.donation import DonorType, StorageType, DonationStatus


class EligibilityCheck(BaseModel):
    rule: str
    passed: bool
    reason: str


class EligibilityResult(BaseModel):
    eligible: Optional[bool]
    status: DonationStatus
    checks: List[EligibilityCheck]
    requires_human_review: bool


class DonationCreate(BaseModel):
    donor_type: DonorType = Field(default=DonorType.OTHER)
    food_type: str = Field(..., min_length=2, max_length=100, examples=["Cooked rice", "Fresh vegetables"])
    description: str = Field(..., min_length=5, examples=["Surplus cooked rice from wedding"])
    quantity_kg: float = Field(..., gt=0, examples=[5.5])
    prepared_at: Optional[datetime] = None
    expires_at: datetime
    storage_type: StorageType = Field(default=StorageType.AMBIENT)
    requires_vehicle: bool = Field(default=False)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    pickup_address: str = Field(..., min_length=5, max_length=500)
    pickup_instructions: Optional[str] = None

    @field_validator("expires_at")
    @classmethod
    def check_expiration(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("Expiration date must include timezone info")
        return v

class DonationUpdate(BaseModel):
    food_type: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = Field(None, min_length=5)
    quantity_kg: Optional[float] = Field(None, gt=0)
    expires_at: Optional[datetime] = None
    storage_type: Optional[StorageType] = None
    requires_vehicle: Optional[bool] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    pickup_address: Optional[str] = Field(None, min_length=5, max_length=500)
    pickup_instructions: Optional[str] = None

    @field_validator("expires_at")
    @classmethod
    def check_expiration(cls, v: Optional[datetime]) -> Optional[datetime]:
        if v and v.tzinfo is None:
            raise ValueError("Expiration date must include timezone info")
        return v

class DonationResponse(BaseModel):
    id: uuid.UUID
    donor_id: uuid.UUID
    donor_type: DonorType
    food_type: str
    description: str
    quantity_kg: float
    allocated_kg: float
    prepared_at: Optional[datetime] = None
    expires_at: datetime
    storage_type: StorageType
    requires_vehicle: bool
    latitude: float
    longitude: float
    pickup_address: str
    pickup_instructions: Optional[str] = None
    status: DonationStatus
    rejection_reason: Optional[str] = None
    eligibility_result: Optional[dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DonationListResponse(BaseModel):
    donations: List[DonationResponse]
    total: int
