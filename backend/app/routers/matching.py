import uuid
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.schemas.recipient import MatchListResponse
from app.services.matching_agent import matching_agent
from app.services.donation_service import get_donation
from app.models.recipient import RecipientProfile, RecipientDemand
from app.middleware.auth import CurrentUser, require_roles
from app.models.user import UserRole

router = APIRouter(prefix="/matching", tags=["Matching"])

@router.post(
    "/{donation_id}",
    response_model=MatchListResponse,
    summary="Run intelligent recipient matching for a donation",
    dependencies=[Depends(require_roles(UserRole.DONOR, UserRole.ADMIN))],
)
def run_matching(
    donation_id: uuid.UUID,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """
    Run the two-stage Intelligent Recipient Matching Agent.
    Finds feasible verified recipient candidates and ranks them based on configured weights.
    Does NOT reserve or allocate any quantities.
    """
    donation = get_donation(db, donation_id)
    if not donation:
        raise HTTPException(status_code=404, detail="Donation not found")
        
    if donation.donor_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to match this donation")
        
    # Fetch all recipient profiles (with user relationship for location/active checks)
    profiles = db.query(RecipientProfile).options(joinedload(RecipientProfile.user)).all()
    
    # Fetch all demands
    demands = db.query(RecipientDemand).all()
    
    # Run the matching agent
    matches = matching_agent.match(donation, profiles, demands)
    
    return MatchListResponse(
        donation_id=donation.id,
        matches=matches
    )
