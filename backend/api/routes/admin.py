"""Admin / operations routes (manual ingestion trigger)."""
from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException, status

from backend.config import settings
from backend.schemas.common import IngestResultResponse
from ingestion.ingest import run_ingestion

router = APIRouter(prefix="/admin", tags=["admin"])


def _require_admin(token: str | None) -> None:
    """Authorize an admin request via the ``X-Admin-Token`` header."""
    if not settings.admin_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin endpoints are disabled (set ADMIN_TOKEN to enable).",
        )
    if token != settings.admin_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin token.",
        )


@router.post("/ingest", response_model=IngestResultResponse)
def trigger_ingest(
    x_admin_token: str | None = Header(default=None),
) -> IngestResultResponse:
    """Run one ingestion pass synchronously and return the counts.

    Useful to populate a fresh deployment on demand and to surface any errors
    directly in the response instead of only in the background logs.
    """
    _require_admin(x_admin_token)
    result = run_ingestion()
    return IngestResultResponse(
        fetched=result.fetched,
        stored=result.stored,
        duplicates=result.duplicates,
    )
