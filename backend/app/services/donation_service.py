import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.donation import Donation, DonationStatus
from app.models.user import User
from app.schemas.donation import DonationCreate, DonationUpdate, EligibilityResult
from app.services.eligibility_agent import eligibility_agent

def create_donation(db: Session, donation_data: DonationCreate, donor: User) -> Donation:
    """Create a new donation for the authenticated donor."""
    db_donation = Donation(
        donor_id=donor.id,
        donor_type=donation_data.donor_type,
        food_type=donation_data.food_type,
        description=donation_data.description,
        quantity_kg=donation_data.quantity_kg,
        prepared_at=donation_data.prepared_at,
        expires_at=donation_data.expires_at,
        storage_type=donation_data.storage_type,
        requires_vehicle=donation_data.requires_vehicle,
        latitude=donation_data.latitude,
        longitude=donation_data.longitude,
        pickup_address=donation_data.pickup_address,
        pickup_instructions=donation_data.pickup_instructions,
        status=DonationStatus.PENDING_REVIEW,
    )
    db.add(db_donation)
    db.commit()
    db.refresh(db_donation)
    return db_donation


def get_donation(db: Session, donation_id: uuid.UUID) -> Optional[Donation]:
    return db.query(Donation).filter(Donation.id == donation_id).first()


def list_donor_donations(db: Session, donor_id: uuid.UUID) -> List[Donation]:
    return db.query(Donation).filter(Donation.donor_id == donor_id).all()


def update_donation(db: Session, donation_id: uuid.UUID, update_data: DonationUpdate, donor: User) -> Donation:
    """Update a donation. Only permitted if status is PENDING_REVIEW or REVIEW_REQUIRED."""
    donation = get_donation(db, donation_id)
    if not donation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Donation not found")
        
    if donation.donor_id != donor.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to modify this donation")
        
    if donation.status not in [DonationStatus.PENDING_REVIEW, DonationStatus.REVIEW_REQUIRED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Donation cannot be updated in its current status"
        )

    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(donation, key, value)
        
    # Reset status back to pending if changed
    donation.status = DonationStatus.PENDING_REVIEW
    donation.eligibility_result = None
    
    db.commit()
    db.refresh(donation)
    return donation


def run_eligibility_screening(db: Session, donation_id: uuid.UUID, user: User) -> Donation:
    """Run the eligibility and safety screening agent on the donation."""
    donation = get_donation(db, donation_id)
    if not donation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Donation not found")
        
    if donation.donor_id != user.id:
        # Depending on requirements, maybe admin could also run it. But for now, owner only.
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to screen this donation")

    if donation.status not in [DonationStatus.PENDING_REVIEW, DonationStatus.REVIEW_REQUIRED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Screening can only be run on pending or review-required donations"
        )
        
    result: EligibilityResult = eligibility_agent.evaluate(donation)
    
    donation.status = result.status
    donation.eligibility_result = result.model_dump()
    
    if result.status == DonationStatus.REJECTED:
        rejection_reasons = [check.reason for check in result.checks if not check.passed]
        donation.rejection_reason = "; ".join(rejection_reasons)
        
    db.commit()
    db.refresh(donation)
    return donation
