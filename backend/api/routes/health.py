"""Health / monitoring route."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.scheduler_state import scheduler_status
from backend.schemas.common import HealthComponent, HealthResponse
from ingestion import gemini_client

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(db: Session = Depends(get_db)) -> HealthResponse:
    """Report the health of the database, Gemini API and scheduler."""
    components: list[HealthComponent] = []

    # Database
    try:
        db.execute(text("SELECT 1"))
        components.append(HealthComponent(name="database", status="ok"))
    except Exception as exc:  # pragma: no cover - depends on DB availability
        components.append(
            HealthComponent(name="database", status="error", detail=str(exc))
        )

    # Gemini
    if gemini_client.is_available():
        components.append(HealthComponent(name="gemini", status="ok"))
    else:
        components.append(
            HealthComponent(
                name="gemini",
                status="disabled",
                detail="No API key configured; using heuristic fallbacks.",
            )
        )

    # Scheduler
    running = scheduler_status()
    components.append(
        HealthComponent(
            name="scheduler",
            status="ok" if running else "stopped",
        )
    )

    overall = "ok" if all(c.status in ("ok", "disabled") for c in components) else "degraded"
    return HealthResponse(status=overall, components=components)
