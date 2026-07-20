"""User profile and preferences routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.api.deps import get_current_user
from backend.database.session import get_db
from backend.models import User
from backend.schemas.preference import PreferenceResponse, PreferenceUpdate
from backend.schemas.user import UserProfile
from backend.services.user_service import get_user_interests, set_user_interests

router = APIRouter(tags=["profile"])


@router.get("/profile", response_model=UserProfile)
def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserProfile:
    """Return the authenticated user's profile and selected interests."""
    interests = get_user_interests(db, current_user.id)
    profile = UserProfile.model_validate(current_user)
    profile.interests = interests
    return profile


@router.post("/preferences", response_model=PreferenceResponse)
def update_preferences(
    payload: PreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PreferenceResponse:
    """Replace the authenticated user's selected interests."""
    interests = set_user_interests(db, current_user.id, payload.interests)
    return PreferenceResponse(interests=interests)
