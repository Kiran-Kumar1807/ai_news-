"""Categories route."""
from __future__ import annotations

from fastapi import APIRouter

from backend.core.categories import CATEGORIES
from backend.schemas.common import CategoriesResponse

router = APIRouter(tags=["categories"])


@router.get("/categories", response_model=CategoriesResponse)
def list_categories() -> CategoriesResponse:
    """Return the list of supported news categories."""
    return CategoriesResponse(categories=CATEGORIES)
