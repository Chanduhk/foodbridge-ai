import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.delivery import Delivery, DeliveryStatus
from app.models.allocation import Allocation, AllocationStatus
from app.models.donation import DonationStatus
from app.models.user import User, UserRole
from app.schemas.delivery import DeliveryCreate, DeliveryUpdate

def create_delivery(db: Session, delivery_data: DeliveryCreate, user: User) -> Delivery:
    """
    Creates a delivery from an ACCEPTED allocation.
    """
    try:
        allocation = db.query(Allocation).filter(Allocation.id == delivery_data.allocation_id).with_for_update().first()
        if not allocation:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Allocation not found")

        # Authorization: Donor or Recipient of the allocation, or Admin
        is_donor = allocation.donation.donor_id == user.id
        is_recipient = allocation.recipient.user_id == user.id
        if not (is_donor or is_recipient or user.role == UserRole.ADMIN):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to create delivery for this allocation")

        # Validation constraints
        if allocation.status != AllocationStatus.ACCEPTED:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Cannot create delivery for allocation in status {allocation.status}")
            
        donation = allocation.donation
        now = datetime.now(timezone.utc)
        expires_at = donation.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at <= now or donation.status in [DonationStatus.EXPIRED, DonationStatus.REJECTED]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Donation is no longer valid or has expired")

        # Check if delivery already exists
        existing = db.query(Delivery).filter(Delivery.allocation_id == allocation.id).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Delivery already exists for this allocation")

        delivery = Delivery(
            allocation_id=allocation.id,
            scheduled_pickup=delivery_data.scheduled_pickup,
            status=DeliveryStatus.SCHEDULED,
            notes=delivery_data.notes,
            distance_km=delivery_data.distance_km,
            estimated_duration_min=delivery_data.estimated_duration_min
        )

        db.add(delivery)
        db.commit()
        db.refresh(delivery)
        return delivery
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Delivery creation failed")


def claim_delivery(db: Session, delivery_id: uuid.UUID, user: User) -> Delivery:
    """
    Volunteer claims a scheduled delivery. Prevents concurrent claiming via Optimistic Concurrency Control.
    """
    try:
        # Standard check
        delivery = db.query(Delivery).filter(Delivery.id == delivery_id).first()
        if not delivery:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delivery not found")

        if user.role != UserRole.VOLUNTEER and user.role != UserRole.ADMIN:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only volunteers can claim deliveries")
            
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Volunteer account is inactive")

        if delivery.status != DeliveryStatus.SCHEDULED:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Delivery is {delivery.status} and cannot be claimed")
            
        if delivery.volunteer_id is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Delivery is already claimed")

        # OCC atomic update for claiming
        updated_rows = db.query(Delivery).filter(
            Delivery.id == delivery_id,
            Delivery.status == DeliveryStatus.SCHEDULED,
            Delivery.volunteer_id == None
        ).update({
            "status": DeliveryStatus.CLAIMED,
            "volunteer_id": user.id
        })
        
        if updated_rows == 0:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Delivery was claimed by another volunteer or status changed")

        db.commit()
        db.refresh(delivery)
        return delivery
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Transaction failed")


def update_delivery_status(db: Session, delivery_id: uuid.UUID, new_status: DeliveryStatus, user: User) -> Delivery:
    """
    Enforces valid state machine transitions.
    SCHEDULED -> CLAIMED (handled by claim_delivery)
    CLAIMED -> PICKED_UP
    PICKED_UP -> IN_TRANSIT
    IN_TRANSIT -> DELIVERED
    * -> FAILED
    * -> CANCELLED
    """
    try:
        delivery = db.query(Delivery).filter(Delivery.id == delivery_id).with_for_update().first()
        if not delivery:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delivery not found")

        # Authorization: Must be the assigned volunteer, or admin, or donor/recipient (for cancels only)
        if user.role == UserRole.VOLUNTEER and delivery.volunteer_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized for this delivery")
            
        current = delivery.status
        valid_transitions = {
            DeliveryStatus.SCHEDULED: [DeliveryStatus.CANCELLED, DeliveryStatus.FAILED], # Claiming goes through claim_delivery
            DeliveryStatus.CLAIMED: [DeliveryStatus.PICKED_UP, DeliveryStatus.CANCELLED, DeliveryStatus.FAILED],
            DeliveryStatus.PICKED_UP: [DeliveryStatus.IN_TRANSIT, DeliveryStatus.FAILED],
            DeliveryStatus.IN_TRANSIT: [DeliveryStatus.DELIVERED, DeliveryStatus.FAILED],
            DeliveryStatus.DELIVERED: [],
            DeliveryStatus.FAILED: [],
            DeliveryStatus.CANCELLED: []
        }
        
        if new_status not in valid_transitions.get(current, []):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid transition from {current} to {new_status}")
            
        delivery.status = new_status
        now = datetime.now(timezone.utc)
        
        if new_status == DeliveryStatus.PICKED_UP:
            delivery.actual_pickup = now
            
        if new_status == DeliveryStatus.DELIVERED:
            delivery.actual_delivery = now
            # Synchronize allocation
            delivery.allocation.status = AllocationStatus.COMPLETED
            
        # We leave reverting allocation logic out of failed/cancelled for now unless explicitly needed, 
        # but typically a failed delivery means the allocation is failed/re-queued.
        
        db.commit()
        db.refresh(delivery)
        return delivery
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Transaction failed")


def get_delivery(db: Session, delivery_id: uuid.UUID) -> Optional[Delivery]:
    return db.query(Delivery).filter(Delivery.id == delivery_id).first()

def list_deliveries(db: Session) -> List[Delivery]:
    return db.query(Delivery).all()
