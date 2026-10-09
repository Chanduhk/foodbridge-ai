import enum
import uuid
from datetime import datetime
from typing import List, Any
from sqlalchemy import String, Boolean, Float, Integer, Text, DateTime, Enum as SQLEnum, ForeignKey, func, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid
from app.database import Base


class OrgType(str, enum.Enum):
    FOOD_BANK = "food_bank"
    SHELTER = "shelter"
    NGO = "ngo"
    COMMUNITY_KITCHEN = "community_kitchen"
    OTHER = "other"


class DemandStatus(str, enum.Enum):
    OPEN = "open"
    PARTIALLY_FULFILLED = "partially_fulfilled"
    FULFILLED = "fulfilled"
    CANCELLED = "cancelled"


class RecipientProfile(Base):
    __tablename__ = "recipient_profiles"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )
    organization_name: Mapped[str] = mapped_column(String(255), nullable=False)
    organization_type: Mapped[OrgType] = mapped_column(
        SQLEnum(OrgType, name="org_type", native_enum=False),
        default=OrgType.NGO,
        nullable=False
    )
    license_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    capacity_kg: Mapped[float] = mapped_column(Float, default=100.0, nullable=False)
    current_occupancy_kg: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    operating_hours: Mapped[str | None] = mapped_column(String(255), nullable=True)
    dietary_restrictions: Mapped[str | None] = mapped_column(Text, nullable=True)
    food_categories_accepted: Mapped[Any] = mapped_column(JSON, default=list, nullable=False)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="recipient_profile")
    demands = relationship("RecipientDemand", back_populates="recipient", cascade="all, delete-orphan")
    allocations = relationship("Allocation", back_populates="recipient")


class RecipientDemand(Base):
    __tablename__ = "recipient_demand"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recipient_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("recipient_profiles.id", ondelete="CASCADE"),
        nullable=False
    )
    food_category: Mapped[str] = mapped_column(String(100), nullable=False)
    quantity_requested: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(20), default="kg", nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    needed_by: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[DemandStatus] = mapped_column(
        SQLEnum(DemandStatus, name="demand_status", native_enum=False),
        default=DemandStatus.OPEN,
        nullable=False
    )
    dietary_requirements: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    recipient = relationship("RecipientProfile", back_populates="demands")
