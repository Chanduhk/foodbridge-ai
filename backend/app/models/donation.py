import enum
import uuid
from datetime import datetime
from typing import Any
from sqlalchemy import String, Boolean, Float, Text, DateTime, Enum as SQLEnum, ForeignKey, func, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid
from app.database import Base


class DonorType(str, enum.Enum):
    HOUSEHOLD = "household"
    RESTAURANT = "restaurant"
    HOTEL = "hotel"
    CATERER = "caterer"
    WEDDING_EVENT = "wedding_event"
    INSTITUTIONAL_CANTEEN = "institutional_canteen"
    OTHER = "other"


class StorageType(str, enum.Enum):
    AMBIENT = "ambient"
    REFRIGERATED = "refrigerated"
    FROZEN = "frozen"


class DonationStatus(str, enum.Enum):
    PENDING_REVIEW = "pending_review"
    ELIGIBLE = "eligible"
    REVIEW_REQUIRED = "review_required"
    ALLOCATED = "allocated"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    EXPIRED = "expired"
    REJECTED = "rejected"


class Donation(Base):
    __tablename__ = "donations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    donor_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    donor_type: Mapped[DonorType] = mapped_column(
        SQLEnum(DonorType, name="donor_type", native_enum=False),
        default=DonorType.OTHER,
        nullable=False
    )
    food_type: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    quantity_kg: Mapped[float] = mapped_column(Float, nullable=False)
    allocated_kg: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    prepared_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    storage_type: Mapped[StorageType] = mapped_column(
        SQLEnum(StorageType, name="storage_type", native_enum=False),
        default=StorageType.AMBIENT,
        nullable=False
    )
    requires_vehicle: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    pickup_address: Mapped[str] = mapped_column(String(500), nullable=False)
    pickup_instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[DonationStatus] = mapped_column(
        SQLEnum(DonationStatus, name="donation_status", native_enum=False),
        default=DonationStatus.PENDING_REVIEW,
        nullable=False
    )
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    eligibility_result: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    donor = relationship("User", back_populates="donations")
    allocations = relationship("Allocation", back_populates="donation", cascade="all, delete-orphan")
