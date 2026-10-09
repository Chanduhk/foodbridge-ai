"""Authentication API endpoints: register, login, and current-user retrieval."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.user import UserRegister, UserLogin, Token, UserResponse
from app.services.auth_service import register_user, authenticate_user
from app.middleware.auth import CurrentUser, require_roles
from app.models.user import UserRole

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register a new donor, recipient, or volunteer account.

    - Validates email format and password strength.
    - Prevents self-registration as admin.
    - Returns the created user profile (never includes password hash).
    """
    user = register_user(db, user_data)
    return user


@router.post(
    "/login",
    response_model=Token,
    summary="Login and obtain JWT access token",
)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    """Authenticate with email and password.

    Returns a JWT bearer token on success.
    """
    return authenticate_user(db, login_data)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current authenticated user",
)
def get_me(current_user: CurrentUser):
    """Return the profile of the currently authenticated user.

    Requires a valid JWT bearer token.
    """
    return current_user


@router.get(
    "/admin-check",
    response_model=UserResponse,
    summary="Admin-only endpoint for RBAC verification",
    dependencies=[Depends(require_roles(UserRole.ADMIN))],
)
def admin_only(current_user: CurrentUser):
    """Admin-only endpoint to verify RBAC is working.

    Returns 403 for non-admin users.
    """
    return current_user
