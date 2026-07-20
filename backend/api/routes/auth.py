"""Authentication routes: register and login."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.logging_config import get_logger
from backend.schemas.auth import Token, UserLogin, UserRegister
from backend.schemas.user import UserPublic
from backend.services.security import create_access_token
from backend.services.user_service import (
    authenticate_user,
    create_user,
    get_user_by_email,
)

router = APIRouter(tags=["auth"])
logger = get_logger("api")


@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: Session = Depends(get_db)) -> UserPublic:
    """Register a new user account."""
    if get_user_by_email(db, payload.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists.",
        )
    user = create_user(db, payload.email, payload.password, payload.full_name)
    logger.info("User registered", extra={"ctx_user_id": user.id})
    return UserPublic.model_validate(user)


@router.post("/login", response_model=Token)
def login(payload: UserLogin, db: Session = Depends(get_db)) -> Token:
    """Authenticate a user and return a JWT access token."""
    user = authenticate_user(db, payload.email, payload.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
        )
    token = create_access_token(user.id)
    logger.info("User logged in", extra={"ctx_user_id": user.id})
    return Token(access_token=token)
