import uuid
from typing import List
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.donation import DonationCreate, DonationUpdate, DonationResponse, EligibilityResult
from app.services import donation_service
from app.middleware.auth import CurrentUser, require_roles
from app.models.user import UserRole

router = APIRouter(prefix="/donations", tags=["Donations"])


@router.post(
    "",
    response_model=DonationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new donation",
    dependencies=[Depends(require_roles(UserRole.DONOR, UserRole.ADMIN))],
)
def create_donation(
    donation_data: DonationCreate,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """
    Create a new donation. Only users with DONOR or ADMIN roles can create donations.
    The donation is associated with the authenticated user.
    """
    return donation_service.create_donation(db, donation_data, current_user)


@router.get(
    "",
    response_model=List[DonationResponse],
    summary="List donations for the current user",
    dependencies=[Depends(require_roles(UserRole.DONOR, UserRole.ADMIN))],
)
def list_my_donations(
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """
    Retrieve all donations submitted by the currently authenticated user.
    """
    return donation_service.list_donor_donations(db, current_user.id)


@router.get(
    "/{donation_id}",
    response_model=DonationResponse,
    summary="Retrieve a specific donation",
)
def get_donation(
    donation_id: uuid.UUID,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """
    Retrieve a specific donation. The user must be the owner of the donation
    (or an admin, though here we just check existence and ownership).
    """
    donation = donation_service.get_donation(db, donation_id)
    if not donation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Donation not found")
        
    if donation.donor_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this donation")
        
    return donation


@router.patch(
    "/{donation_id}",
    response_model=DonationResponse,
    summary="Update a donation",
    dependencies=[Depends(require_roles(UserRole.DONOR, UserRole.ADMIN))],
)
def update_donation(
    donation_id: uuid.UUID,
    update_data: DonationUpdate,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """
    Update permitted information on an existing donation.
    Only permitted if the donation status is PENDING_REVIEW or REVIEW_REQUIRED.
    """
    return donation_service.update_donation(db, donation_id, update_data, current_user)


@router.post(
    "/{donation_id}/screen",
    response_model=DonationResponse,
    summary="Run food eligibility and safety screening",
    dependencies=[Depends(require_roles(UserRole.DONOR, UserRole.ADMIN))],
)
def screen_donation(
    donation_id: uuid.UUID,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """
    Run the rule-based Food Eligibility and Safety Screening Agent on the donation.
    Evaluates quantity, deadline, and mandatory fields to provide decision support.
    Status will transition to ELIGIBLE, REVIEW_REQUIRED, or REJECTED.
    """
    return donation_service.run_eligibility_screening(db, donation_id, current_user)
