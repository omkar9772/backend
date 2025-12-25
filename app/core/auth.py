"""
Authentication helpers for regular users
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.models.user import User
from app.core.security import decode_access_token

# OAuth2 scheme for user authentication
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


async def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme_optional),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get the current authenticated user from JWT token (optional - returns None if not authenticated)

    Args:
        token: JWT access token from request header (optional)
        db: Database session

    Returns:
        User object if authenticated, None otherwise
    """
    if not token:
        return None

    # Decode token
    payload = decode_access_token(token)
    if payload is None:
        return None

    user_id: Optional[str] = payload.get("sub")
    if user_id is None:
        return None

    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()
    if user is None or not user.is_active:
        return None

    return user


async def get_current_user(
    token: str = Depends(OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")),
    db: Session = Depends(get_db)
) -> User:
    """
    Get the current authenticated user from JWT token (required)

    Args:
        token: JWT access token from request header
        db: Database session

    Returns:
        User object

    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Decode token
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    user_id: Optional[str] = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )

    return user
