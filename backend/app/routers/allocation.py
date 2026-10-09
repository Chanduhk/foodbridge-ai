import uuid
from typing import List
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.allocation import AllocationCreate, AllocationResponse
from app.services import allocation_service
from app.middleware.auth import CurrentUser, require_roles
from app.models.user import UserRole
from app.models.allocation import Allocation

router = APIRouter(prefix="/allocations", tags=["Allocations"])

@router.post(
    "",
    response_model=AllocationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an allocation proposal",
    dependencies=[Depends(require_roles(UserRole.DONOR, UserRole.ADMIN))],
)
def create_allocation(
    alloc_data: AllocationCreate,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """
    Create a new allocation proposal. Reserves the quantity on the donation.
    Enforces strict concurrency safety via DB row locks.
    """
    return allocation_service.create_allocation(db, alloc_data, current_user)


@router.get(
    "/{allocation_id}",
    response_model=AllocationResponse,
    summary="Retrieve an allocation",
)
def get_allocation(
    allocation_id: uuid.UUID,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Retrieve a specific allocation."""
    allocation = allocation_service.get_allocation(db, allocation_id)
    if not allocation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Allocation not found")
        
    # Simple check - full proper ownership check would verify donor or recipient matching
    return allocation


@router.post(
    "/{allocation_id}/accept",
    response_model=AllocationResponse,
    summary="Recipient accepts the allocation",
    dependencies=[Depends(require_roles(UserRole.RECIPIENT, UserRole.ADMIN))],
)
def accept_allocation(
    allocation_id: uuid.UUID,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Recipient accepts the proposed allocation."""
    return allocation_service.accept_allocation(db, allocation_id, current_user)


@router.post(
    "/{allocation_id}/reject",
    response_model=AllocationResponse,
    summary="Recipient rejects the allocation",
    dependencies=[Depends(require_roles(UserRole.RECIPIENT, UserRole.ADMIN))],
)
def reject_allocation(
    allocation_id: uuid.UUID,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Recipient rejects the proposed allocation."""
    return allocation_service.reject_allocation(db, allocation_id, current_user)


@router.post(
    "/{allocation_id}/cancel",
    response_model=AllocationResponse,
    summary="Donor cancels the allocation",
    dependencies=[Depends(require_roles(UserRole.DONOR, UserRole.ADMIN))],
)
def cancel_allocation(
    allocation_id: uuid.UUID,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Donor or Admin cancels the allocation."""
    return allocation_service.cancel_allocation(db, allocation_id, current_user)
