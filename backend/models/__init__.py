"""ORM models package.

Importing this package registers all models on the shared ``Base.metadata``.
"""
from backend.models.article import Article
from backend.models.niche import Niche
from backend.models.preference import UserPreference
from backend.models.user import User

__all__ = ["Article", "Niche", "UserPreference", "User"]
