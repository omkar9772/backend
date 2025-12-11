"""
Admin authentication endpoints
"""
from datetime import timedelta, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import verify_password, create_access_token, get_password_hash
from app.db.base import get_db
from app.models.admin import AdminUser
from app.schemas.admin import Token, AdminUserCreate, AdminUserResponse

router = APIRouter(prefix="/admin", tags=["Admin Authentication"])


@router.post("/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db)
):
    """
    Admin login endpoint

    Authenticates admin user and returns JWT access token

    Args:
        form_data: OAuth2 form with username and password
        db: Database session

    Returns:
        Token with access_token and token_type

    Raises:
        HTTPException: If credentials are invalid
    """
    # Find user by username
    user = db.query(AdminUser).filter(AdminUser.username == form_data.username).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify password
    if not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account",
        )

    # Update last login time
    user.last_login = datetime.utcnow()
    db.commit()

    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    return Token(access_token=access_token, token_type="bearer")


@router.post("/register", response_model=AdminUserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    admin_data: AdminUserCreate,
    db: Session = Depends(get_db)
):
    """
    Admin registration endpoint

    Creates a new admin user account

    Args:
        admin_data: Admin user creation data (username, email, password, full_name, role)
        db: Database session

    Returns:
        AdminUserResponse with created user details

    Raises:
        HTTPException: If username or email already exists, or validation fails
    """
    # Check if username already exists
    existing_user = db.query(AdminUser).filter(AdminUser.username == admin_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    # Check if email already exists
    existing_email = db.query(AdminUser).filter(AdminUser.email == admin_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Validate password strength (additional checks beyond min length)
    if len(admin_data.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long"
        )

    # Check password complexity
    has_upper = any(c.isupper() for c in admin_data.password)
    has_lower = any(c.islower() for c in admin_data.password)
    has_digit = any(c.isdigit() for c in admin_data.password)

    if not (has_upper and has_lower and has_digit):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one uppercase letter, one lowercase letter, and one number"
        )

    # Hash the password
    password_hash = get_password_hash(admin_data.password)

    # Create new admin user
    new_admin = AdminUser(
        username=admin_data.username,
        email=admin_data.email,
        password_hash=password_hash,
        full_name=admin_data.full_name,
        role=admin_data.role,
        is_active=True
    )

    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)

    return new_admin
