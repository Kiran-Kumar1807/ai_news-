"""User and preference persistence logic."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.core.categories import CATEGORIES
from backend.models import Niche, User, UserPreference
from backend.services.security import hash_password, verify_password


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email.lower()))


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def create_user(db: Session, email: str, password: str, full_name: str | None) -> User:
    """Persist a new user with a hashed password."""
    user = User(
        email=email.lower(),
        password_hash=hash_password(password),
        full_name=full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    """Return the user if the email/password pair is valid, else ``None``."""
    user = get_user_by_email(db, email)
    if user is None:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def ensure_niches(db: Session) -> None:
    """Make sure every canonical category exists as a niche row."""
    existing = {n.niche_name for n in db.scalars(select(Niche)).all()}
    created = False
    for name in CATEGORIES:
        if name not in existing:
            db.add(Niche(niche_name=name))
            created = True
    if created:
        db.commit()


def get_user_interests(db: Session, user_id: int) -> list[str]:
    """Return the list of niche names a user is subscribed to."""
    rows = db.execute(
        select(Niche.niche_name)
        .join(UserPreference, UserPreference.niche_id == Niche.id)
        .where(UserPreference.user_id == user_id)
        .order_by(Niche.niche_name)
    ).all()
    return [r[0] for r in rows]


def set_user_interests(db: Session, user_id: int, interests: list[str]) -> list[str]:
    """Replace a user's interests with the provided list of category names.

    Unknown category names are ignored. Returns the persisted interest names.
    """
    ensure_niches(db)
    valid = [i for i in interests if i in set(CATEGORIES)]

    niche_ids = {
        name: nid
        for name, nid in db.execute(
            select(Niche.niche_name, Niche.id).where(Niche.niche_name.in_(valid))
        ).all()
    }

    # Clear existing preferences and re-add the selected ones.
    db.query(UserPreference).filter(UserPreference.user_id == user_id).delete()
    for name in valid:
        db.add(UserPreference(user_id=user_id, niche_id=niche_ids[name]))
    db.commit()
    return get_user_interests(db, user_id)
