"""Shared FastAPI dependencies (authentication)."""
from __future__ import annotations

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.models import User
from backend.services.security import decode_access_token
from backend.services.user_service import get_user_by_id

_bearer = HTTPBearer(auto_error=True)

_credentials_error = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    """Resolve the authenticated user from a Bearer JWT."""
    token = credentials.credentials
    try:
        payload = decode_access_token(token)
    except jwt.PyJWTError as exc:
        raise _credentials_error from exc

    subject = payload.get("sub")
    if subject is None:
        raise _credentials_error

    try:
        user_id = int(subject)
    except (TypeError, ValueError) as exc:
        raise _credentials_error from exc

    user = get_user_by_id(db, user_id)
    if user is None:
        raise _credentials_error
    return user
