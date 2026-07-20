"""APScheduler configuration wiring hourly ingestion and the daily digest."""
from __future__ import annotations

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from backend.config import settings
from backend.logging_config import get_logger
from backend.scheduler_state import set_scheduler
from ingestion.ingest import run_ingestion
from scheduler.daily_digest import send_daily_digests

logger = get_logger("scheduler")


def _hourly_job() -> None:
    logger.info("Hourly ingestion job started")
    run_ingestion()


def _daily_job() -> None:
    logger.info("Daily digest job started")
    send_daily_digests()


def create_scheduler() -> BackgroundScheduler:
    """Create and configure (but do not start) the background scheduler."""
    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(
        _hourly_job,
        trigger=IntervalTrigger(minutes=settings.ingest_interval_minutes),
        id="hourly_ingestion",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    scheduler.add_job(
        _daily_job,
        trigger=CronTrigger(hour=settings.digest_hour, minute=0),
        id="daily_digest",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    return scheduler


def start_scheduler() -> BackgroundScheduler:
    """Create, start and register the background scheduler."""
    scheduler = create_scheduler()
    scheduler.start()
    set_scheduler(scheduler)
    logger.info("Scheduler started")
    return scheduler


def shutdown_scheduler(scheduler: BackgroundScheduler) -> None:
    scheduler.shutdown(wait=False)
    set_scheduler(None)
    logger.info("Scheduler stopped")
