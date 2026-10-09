import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.allocation import Allocation, AllocationStatus
from app.models.donation import Donation, DonationStatus
from app.models.recipient import RecipientProfile
from app.models.user import User, UserRole
from app.schemas.allocation import AllocationCreate

def create_allocation(db: Session, alloc_data: AllocationCreate, user: User) -> Allocation:
    """
    Creates an allocation proposal using strict transaction boundaries and row-level locks (FOR UPDATE).
    """
    # 1. Start explicit transaction block
    try:
        # Lock donation row
        donation = db.query(Donation).filter(Donation.id == alloc_data.donation_id).with_for_update().first()
        if not donation:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Donation not found")

        # Authorization: Only Donor of the donation or Admin can allocate
        if donation.donor_id != user.id and user.role != UserRole.ADMIN:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to allocate this donation")

        # Lock recipient profile row
        recipient = db.query(RecipientProfile).filter(RecipientProfile.id == alloc_data.recipient_id).with_for_update().first()
        if not recipient:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipient not found")

        # Hard constraints
        if donation.status not in [DonationStatus.ELIGIBLE, DonationStatus.ALLOCATED, DonationStatus.PENDING_REVIEW, DonationStatus.REVIEW_REQUIRED]:
             # It can be partially allocated if status is eligible or allocated
             pass

        if donation.status in [DonationStatus.REJECTED, DonationStatus.EXPIRED, DonationStatus.DELIVERED]:
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Donation status does not allow allocation")
             
        now = datetime.now(timezone.utc)
        expires_at = donation.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at <= now:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Donation has expired")

        if not recipient.is_verified:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Recipient is not verified")

        # Must join to get recipient's user to check if active
        rec_user = db.query(User).filter(User.id == recipient.user_id).first()
        if not rec_user or not rec_user.is_active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Recipient account is inactive")

        # Quantity constraints
        available_kg = donation.quantity_kg - donation.allocated_kg
        if alloc_data.quantity_kg <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Allocation quantity must be greater than 0")
        if alloc_data.quantity_kg > available_kg:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Requested {alloc_data.quantity_kg}kg exceeds available {available_kg}kg")

        available_capacity = recipient.capacity_kg - recipient.current_occupancy_kg
        if alloc_data.quantity_kg > available_capacity:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Allocation exceeds recipient available capacity")
            
        # Optimistic Concurrency Control (OCC) for SQLite compatibility
        # We attempt to atomically update the allocated_kg only if it hasn't changed.
        new_allocated_kg = donation.allocated_kg + alloc_data.quantity_kg
        updated_rows = db.query(Donation).filter(
            Donation.id == donation.id,
            Donation.allocated_kg == donation.allocated_kg
        ).update({"allocated_kg": new_allocated_kg})
        
        if updated_rows == 0:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Concurrent modification detected. Please try again.")

        # Create allocation
        allocation = Allocation(
            donation_id=donation.id,
            recipient_id=recipient.id,
            quantity_kg=alloc_data.quantity_kg,
            match_score=alloc_data.match_score,
            score_explanation=alloc_data.score_explanation,
            status=AllocationStatus.PROPOSED
        )

        db.add(allocation)
        
        # We already updated allocated_kg via OCC. Now update status.
        # Refresh donation to get latest state in session
        db.refresh(donation)
        if donation.allocated_kg >= donation.quantity_kg:
            donation.status = DonationStatus.ALLOCATED
        elif donation.status == DonationStatus.ELIGIBLE:
            donation.status = DonationStatus.ALLOCATED 

        db.commit()
        db.refresh(allocation)
        return allocation
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Transaction failed")


def accept_allocation(db: Session, allocation_id: uuid.UUID, user: User) -> Allocation:
    """Recipient accepts the allocation proposal."""
    try:
        allocation = db.query(Allocation).filter(Allocation.id == allocation_id).with_for_update().first()
        if not allocation:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Allocation not found")

        recipient = db.query(RecipientProfile).filter(RecipientProfile.id == allocation.recipient_id).with_for_update().first()
        
        if recipient.user_id != user.id and user.role != UserRole.ADMIN:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to accept this allocation")
            
        if allocation.status != AllocationStatus.PROPOSED:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Cannot transition from {allocation.status} to ACCEPTED")
            
        # Transition
        allocation.status = AllocationStatus.ACCEPTED
        
        # We consider occupancy increased upon acceptance (or delivery, but usually acceptance means they are making room)
        recipient.current_occupancy_kg += allocation.quantity_kg
        
        db.commit()
        db.refresh(allocation)
        return allocation
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Transaction failed")


def reject_allocation(db: Session, allocation_id: uuid.UUID, user: User) -> Allocation:
    """Recipient rejects the allocation proposal."""
    try:
        allocation = db.query(Allocation).filter(Allocation.id == allocation_id).with_for_update().first()
        if not allocation:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Allocation not found")

        recipient = db.query(RecipientProfile).filter(RecipientProfile.id == allocation.recipient_id).first()
        
        if recipient.user_id != user.id and user.role != UserRole.ADMIN:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to reject this allocation")
            
        if allocation.status != AllocationStatus.PROPOSED:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Cannot transition from {allocation.status} to REJECTED")
            
        # Free up donation quantity
        donation = db.query(Donation).filter(Donation.id == allocation.donation_id).with_for_update().first()
        donation.allocated_kg -= allocation.quantity_kg
        if donation.allocated_kg < donation.quantity_kg:
            donation.status = DonationStatus.ELIGIBLE
            
        # Transition
        allocation.status = AllocationStatus.REJECTED
        
        db.commit()
        db.refresh(allocation)
        return allocation
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Transaction failed")


def cancel_allocation(db: Session, allocation_id: uuid.UUID, user: User) -> Allocation:
    """Donor or Admin cancels the allocation."""
    try:
        allocation = db.query(Allocation).filter(Allocation.id == allocation_id).with_for_update().first()
        if not allocation:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Allocation not found")

        donation = db.query(Donation).filter(Donation.id == allocation.donation_id).with_for_update().first()
        
        if donation.donor_id != user.id and user.role != UserRole.ADMIN:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to cancel this allocation")
            
        if allocation.status not in [AllocationStatus.PROPOSED, AllocationStatus.ACCEPTED]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Cannot cancel from {allocation.status}")
            
        # If it was accepted, we must revert recipient occupancy
        if allocation.status == AllocationStatus.ACCEPTED:
            recipient = db.query(RecipientProfile).filter(RecipientProfile.id == allocation.recipient_id).with_for_update().first()
            recipient.current_occupancy_kg -= allocation.quantity_kg
            
        # Free up donation quantity
        donation.allocated_kg -= allocation.quantity_kg
        if donation.allocated_kg < donation.quantity_kg:
            donation.status = DonationStatus.ELIGIBLE
            
        # Transition
        allocation.status = AllocationStatus.CANCELLED
        
        db.commit()
        db.refresh(allocation)
        return allocation
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Transaction failed")

def get_allocation(db: Session, allocation_id: uuid.UUID) -> Optional[Allocation]:
    return db.query(Allocation).filter(Allocation.id == allocation_id).first()
