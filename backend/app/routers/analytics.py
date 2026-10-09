from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.middleware.auth import CurrentUser
from app.models.user import User
from app.models.donation import Donation
from app.models.recipient import RecipientDemand, RecipientProfile, DemandStatus
from app.models.allocation import Allocation, AllocationStatus
from app.models.delivery import Delivery, DeliveryStatus
from app.schemas.ml import AnalyticsResponse

router = APIRouter()

@router.get("/metrics", response_model=AnalyticsResponse)
def get_analytics(
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    # Calculate real backend metrics based on project operations
    
    # Total food rescued (Allocations that are ACCEPTED or Deliveries that are completed)
    rescued_allocations = db.query(func.sum(Allocation.quantity_kg)).filter(
        Allocation.status == AllocationStatus.ACCEPTED
    ).scalar() or 0.0

    # Deliveries completed
    completed_deliveries = db.query(func.count(Delivery.id)).filter(
        Delivery.status == DeliveryStatus.DELIVERED
    ).scalar() or 0
    
    # Active recipient profiles
    active_recipients = db.query(func.count(RecipientProfile.id)).filter(
        RecipientProfile.is_verified == True
    ).scalar() or 0
    
    # Unmet demand
    total_demand = db.query(func.sum(RecipientDemand.quantity_requested)).filter(
        RecipientDemand.status != DemandStatus.FULFILLED
    ).scalar() or 0.0
    
    return AnalyticsResponse(
        total_food_rescued_kg=float(rescued_allocations),
        total_deliveries_completed=completed_deliveries,
        active_recipients=active_recipients,
        unmet_demand_kg=float(total_demand)
    )
