import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.recipient import (
    RecipientProfileCreate,
    RecipientProfileUpdate,
    RecipientProfileResponse,
    RecipientDemandCreate,
    RecipientDemandUpdate,
    RecipientDemandResponse
)
from app.services import recipient_service
from app.middleware.auth import CurrentUser, require_roles
from app.models.user import UserRole

router = APIRouter(prefix="/recipients", tags=["Recipients"])


# --- Recipient Profile Endpoints ---

@router.post(
    "/profile",
    response_model=RecipientProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a recipient profile",
    dependencies=[Depends(require_roles(UserRole.RECIPIENT))],
)
def create_profile(
    profile_data: RecipientProfileCreate,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    return recipient_service.create_recipient_profile(db, profile_data, current_user)

@router.get(
    "/profile",
    response_model=RecipientProfileResponse,
    summary="Get current user's recipient profile",
    dependencies=[Depends(require_roles(UserRole.RECIPIENT))],
)
def get_profile(
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    profile = recipient_service.get_recipient_profile(db, current_user.id)
    if not profile:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

@router.patch(
    "/profile",
    response_model=RecipientProfileResponse,
    summary="Update current user's recipient profile",
    dependencies=[Depends(require_roles(UserRole.RECIPIENT))],
)
def update_profile(
    update_data: RecipientProfileUpdate,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    return recipient_service.update_recipient_profile(db, update_data, current_user)

@router.post(
    "/{user_id}/verify",
    response_model=RecipientProfileResponse,
    summary="Verify a recipient (Admin only)",
    dependencies=[Depends(require_roles(UserRole.ADMIN))],
)
def verify_recipient_profile(
    user_id: uuid.UUID,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    return recipient_service.verify_recipient(db, user_id, current_user)

# --- Recipient Demand Endpoints ---

@router.post(
    "/demands",
    response_model=RecipientDemandResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a recipient demand",
    dependencies=[Depends(require_roles(UserRole.RECIPIENT))],
)
def create_demand(
    demand_data: RecipientDemandCreate,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    return recipient_service.create_demand(db, demand_data, current_user)

@router.get(
    "/demands",
    response_model=List[RecipientDemandResponse],
    summary="List current user's recipient demands",
    dependencies=[Depends(require_roles(UserRole.RECIPIENT))],
)
def list_demands(
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    return recipient_service.list_recipient_demands(db, current_user)

@router.patch(
    "/demands/{demand_id}",
    response_model=RecipientDemandResponse,
    summary="Update a recipient demand",
    dependencies=[Depends(require_roles(UserRole.RECIPIENT))],
)
def update_demand(
    demand_id: uuid.UUID,
    update_data: RecipientDemandUpdate,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    return recipient_service.update_demand(db, demand_id, update_data, current_user)
