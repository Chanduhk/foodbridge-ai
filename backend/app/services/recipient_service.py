import uuid
from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.recipient import RecipientProfile, RecipientDemand, DemandStatus
from app.models.user import User, UserRole
from app.schemas.recipient import (
    RecipientProfileCreate,
    RecipientProfileUpdate,
    RecipientDemandCreate,
    RecipientDemandUpdate
)

# --- Recipient Profile Services ---

def create_recipient_profile(db: Session, profile_data: RecipientProfileCreate, user: User) -> RecipientProfile:
    existing = db.query(RecipientProfile).filter(RecipientProfile.user_id == user.id).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Recipient profile already exists for this user")
        
    profile = RecipientProfile(
        user_id=user.id,
        organization_name=profile_data.organization_name,
        organization_type=profile_data.organization_type,
        license_number=profile_data.license_number,
        is_verified=False, # Must be verified by admin
        capacity_kg=profile_data.capacity_kg,
        operating_hours=profile_data.operating_hours,
        dietary_restrictions=profile_data.dietary_restrictions,
        food_categories_accepted=profile_data.food_categories_accepted,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile

def get_recipient_profile(db: Session, user_id: uuid.UUID) -> Optional[RecipientProfile]:
    return db.query(RecipientProfile).filter(RecipientProfile.user_id == user_id).first()

def update_recipient_profile(db: Session, update_data: RecipientProfileUpdate, user: User) -> RecipientProfile:
    profile = get_recipient_profile(db, user.id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipient profile not found")
        
    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(profile, key, value)
        
    db.commit()
    db.refresh(profile)
    return profile

def verify_recipient(db: Session, user_id: uuid.UUID, admin_user: User) -> RecipientProfile:
    if admin_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can verify recipients")
        
    profile = get_recipient_profile(db, user_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipient profile not found")
        
    profile.is_verified = True
    profile.verified_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(profile)
    return profile

# --- Recipient Demand Services ---

def create_demand(db: Session, demand_data: RecipientDemandCreate, user: User) -> RecipientDemand:
    profile = get_recipient_profile(db, user.id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Recipient profile required to create demand")
        
    demand = RecipientDemand(
        recipient_id=profile.id,
        food_category=demand_data.food_category,
        quantity_requested=demand_data.quantity_requested,
        unit=demand_data.unit,
        priority=demand_data.priority,
        needed_by=demand_data.needed_by,
        dietary_requirements=demand_data.dietary_requirements,
        status=DemandStatus.OPEN
    )
    db.add(demand)
    db.commit()
    db.refresh(demand)
    return demand

def list_recipient_demands(db: Session, user: User) -> List[RecipientDemand]:
    profile = get_recipient_profile(db, user.id)
    if not profile:
        return []
    return db.query(RecipientDemand).filter(RecipientDemand.recipient_id == profile.id).all()

def update_demand(db: Session, demand_id: uuid.UUID, update_data: RecipientDemandUpdate, user: User) -> RecipientDemand:
    demand = db.query(RecipientDemand).filter(RecipientDemand.id == demand_id).first()
    if not demand:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Demand not found")
        
    profile = get_recipient_profile(db, user.id)
    if not profile or demand.recipient_id != profile.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to modify this demand")
        
    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(demand, key, value)
        
    db.commit()
    db.refresh(demand)
    return demand
