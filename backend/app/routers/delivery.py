import uuid
from typing import List
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.delivery import DeliveryCreate, DeliveryUpdate, DeliveryResponse, LogisticsRecommendation
from app.services import delivery_service
from app.services.logistics_agent import logistics_agent
from app.services.allocation_service import get_allocation
from app.middleware.auth import CurrentUser, require_roles
from app.models.user import UserRole
from app.models.delivery import DeliveryStatus

router = APIRouter(prefix="/deliveries", tags=["Deliveries"])

@router.post(
    "",
    response_model=DeliveryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a delivery task for an accepted allocation",
)
def create_delivery(
    delivery_data: DeliveryCreate,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    return delivery_service.create_delivery(db, delivery_data, current_user)

@router.get(
    "",
    response_model=List[DeliveryResponse],
    summary="List available deliveries for volunteers",
    dependencies=[Depends(require_roles(UserRole.VOLUNTEER, UserRole.ADMIN))],
)
def list_deliveries(
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    return delivery_service.list_deliveries(db)

@router.get(
    "/{delivery_id}",
    response_model=DeliveryResponse,
    summary="Retrieve a delivery",
)
def get_delivery(
    delivery_id: uuid.UUID,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    delivery = delivery_service.get_delivery(db, delivery_id)
    if not delivery:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delivery not found")
    return delivery

@router.post(
    "/{delivery_id}/claim",
    response_model=DeliveryResponse,
    summary="Volunteer claims a delivery",
    dependencies=[Depends(require_roles(UserRole.VOLUNTEER, UserRole.ADMIN))],
)
def claim_delivery(
    delivery_id: uuid.UUID,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    return delivery_service.claim_delivery(db, delivery_id, current_user)

@router.patch(
    "/{delivery_id}/status",
    response_model=DeliveryResponse,
    summary="Update delivery status",
)
def update_delivery_status(
    delivery_id: uuid.UUID,
    status_update: DeliveryUpdate,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    if not status_update.status:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Status must be provided")
    return delivery_service.update_delivery_status(db, delivery_id, status_update.status, current_user)

@router.get(
    "/allocation/{allocation_id}/recommend",
    response_model=LogisticsRecommendation,
    summary="Get logistics recommendation for an allocation",
    dependencies=[Depends(require_roles(UserRole.DONOR, UserRole.ADMIN))],
)
def recommend_logistics(
    allocation_id: uuid.UUID,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    allocation = get_allocation(db, allocation_id)
    if not allocation:
        raise HTTPException(status_code=404, detail="Allocation not found")
        
    return logistics_agent.evaluate_feasibility(db, allocation)
