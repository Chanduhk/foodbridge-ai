"""Pydantic schemas for user registration, login, and profile responses."""
import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator
from app.models.user import UserRole


# --- Registration ---

class UserRegister(BaseModel):
    """Schema for user registration requests."""
    email: str = Field(..., min_length=5, max_length=255, examples=["donor@example.com"])
    password: str = Field(..., min_length=8, max_length=128, examples=["SecurePass123!"])
    full_name: str = Field(..., min_length=2, max_length=255, examples=["Alice Chef"])
    role: UserRole = Field(default=UserRole.DONOR, examples=["donor"])
    phone: Optional[str] = Field(None, max_length=50, examples=["+1234567890"])
    latitude: Optional[float] = Field(None, ge=-90, le=90, examples=[40.7128])
    longitude: Optional[float] = Field(None, ge=-180, le=180, examples=[-74.0060])
    address: Optional[str] = Field(None, max_length=500, examples=["123 Bakery Lane, NYC"])

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        """Basic email format validation."""
        v = v.strip().lower()
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Invalid email format")
        return v

    @field_validator("role")
    @classmethod
    def prevent_admin_self_registration(cls, v: UserRole) -> UserRole:
        """Users cannot register themselves as admin."""
        if v == UserRole.ADMIN:
            raise ValueError("Cannot self-register as admin")
        return v

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Enforce minimum password complexity."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


# --- Login ---

class UserLogin(BaseModel):
    """Schema for login requests."""
    email: str = Field(..., min_length=5, max_length=255, examples=["donor@example.com"])
    password: str = Field(..., min_length=1, max_length=128, examples=["SecurePass123!"])

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()


# --- Token Response ---

class Token(BaseModel):
    """JWT access token response."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Decoded JWT token payload."""
    user_id: uuid.UUID
    role: UserRole


# --- User Response (no password hash) ---

class UserResponse(BaseModel):
    """Safe user representation for API responses. Never includes password."""
    id: uuid.UUID
    email: str
    full_name: str
    role: UserRole
    phone: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    """Paginated list of users for admin views."""
    users: list[UserResponse]
    total: int
