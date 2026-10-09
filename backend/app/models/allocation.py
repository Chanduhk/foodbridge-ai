import enum
import uuid
from datetime import datetime
from typing import Any
from sqlalchemy import Float, DateTime, Enum as SQLEnum, ForeignKey, func, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid
from app.database import Base


class AllocationStatus(str, enum.Enum):
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class Allocation(Base):
    __tablename__ = "allocations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    donation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("donations.id", ondelete="CASCADE"),
        nullable=False
    )
    recipient_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("recipient_profiles.id", ondelete="CASCADE"),
        nullable=False
    )
    quantity_kg: Mapped[float] = mapped_column(Float, nullable=False)
    match_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    score_explanation: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    status: Mapped[AllocationStatus] = mapped_column(
        SQLEnum(AllocationStatus, name="allocation_status", native_enum=False),
        default=AllocationStatus.PROPOSED,
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    donation = relationship("Donation", back_populates="allocations")
    recipient = relationship("RecipientProfile", back_populates="allocations")
    delivery = relationship("Delivery", back_populates="allocation", uselist=False, cascade="all, delete-orphan")
