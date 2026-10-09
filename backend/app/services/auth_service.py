"""Authentication service: registration and login business logic."""
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User, UserRole
from app.schemas.user import UserRegister, UserLogin, Token, UserResponse
from app.utils.security import hash_password, verify_password, create_access_token


def register_user(db: Session, user_data: UserRegister) -> User:
    """Register a new user.

    - Normalizes email to lowercase.
    - Checks for duplicate email.
    - Hashes password with bcrypt.
    - Prevents self-registration as admin.
    - Returns the created User ORM object.
    """
    # Duplicate email check
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )

    # Admin self-registration is already blocked by schema validation,
    # but we enforce it at the service layer as well for defense in depth.
    if user_data.role == UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot self-register as admin",
        )

    user = User(
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        full_name=user_data.full_name,
        role=user_data.role,
        phone=user_data.phone,
        latitude=user_data.latitude,
        longitude=user_data.longitude,
        address=user_data.address,
    )

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, login_data: UserLogin) -> Token:
    """Authenticate a user by email and password, returning a JWT token.

    Raises 401 if credentials are invalid.
    Raises 403 if account is deactivated.
    """
    user = db.query(User).filter(User.email == login_data.email).first()

    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )

    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role.value}
    )

    return Token(access_token=access_token, token_type="bearer")
