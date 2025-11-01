"""
Celery Tasks
Background tasks for company search and data processing
"""

import logging
import time
from datetime import UTC, datetime
from typing import Any

from celery import Task

from app.celery_app.celery_config import celery_app
from app.config import settings

_logger = logging.getLogger(__name__)


class CallbackTask(Task):
    """
    Custom Celery task with callbacks for progress tracking.
    """

    def on_failure(
        self,
        exc: Exception,
        task_id: str,
        args: tuple,  # type: ignore
        kwargs: dict,  # type: ignore
        einfo: Any,
    ) -> None:
        """Called when task fails."""
        _logger.error(f"Task {task_id} failed: {exc}")
        super().on_failure(exc, task_id, args, kwargs, einfo)

    def on_success(
        self,
        retval: Any,
        task_id: str,
        args: tuple,  # type: ignore
        kwargs: dict,  # type: ignore
    ) -> None:
        """Called when task succeeds."""
        _logger.info(f"Task {task_id} completed successfully")
        super().on_success(retval, task_id, args, kwargs)


@celery_app.task(  # type: ignore
    bind=True,
    base=CallbackTask,
    name="process_company_search",
    queue="scraping",
    max_retries=3,
)
def process_company_search(
    self: Task,
    query: str,
    include_website: bool = True,
    include_linkedin: bool = False,
    timeout: int | None = None,
) -> dict[str, Any]:
    """
    Main task to process company search request.

    Workflow:
    1. Update status to 'started'
    2. Scrape web for company information
    3. Update status to 'processing'
    4. Send data to LLM for extraction
    5. Update status to 'completed'
    6. Return structured result

    Args:
        self: Celery task instance
        query: Company name or search query
        include_website: Whether to scrape company website
        include_linkedin: Whether to include LinkedIn data
        timeout: Custom timeout for the task

    Returns:
        Dictionary with company_info and metadata

    Raises:
        Exception: If task fails at any step
    """
    task_id = self.request.id
    start_time = time.time()
    created_at = datetime.now(UTC)

    _logger.info(f"Starting company search task {task_id} for query: {query}")

    try:
        # Update task state: STARTED (10% progress)
        self.update_state(
            state="PROGRESS",
            meta={
                "status": "started",
                "progress": 10,
                "message": f"Starting search for '{query}'",
                "started_at": created_at.isoformat(),
            },
        )

        # Step 1: Web Scraping (20-60% progress)
        _logger.info(f"Task {task_id}: Starting web scraping phase")
        self.update_state(
            state="PROGRESS",
            meta={
                "status": "scraping",
                "progress": 20,
                "message": "Scraping web for company information",
                "started_at": created_at.isoformat(),
            },
        )

        # Import here to avoid circular imports
        from app.scraper.nodriver_scraper import CompanyScraper

        scraped_data = CompanyScraper.scrape(
            query=query,
            timeout=timeout or settings.SCRAPER_TIMEOUT,
        )

        _logger.info(f"Task {task_id}: Web scraping completed")
        self.update_state(
            state="PROGRESS",
            meta={
                "status": "scraping",
                "progress": 60,
                "message": "Web scraping completed, preparing data",
                "started_at": created_at.isoformat(),
            },
        )

        # Step 2: LLM Processing (70-90% progress)
        _logger.info(f"Task {task_id}: Starting LLM processing phase")
        self.update_state(
            state="PROGRESS",
            meta={
                "status": "processing",
                "progress": 70,
                "message": "Processing data with AI",
                "started_at": created_at.isoformat(),
            },
        )

        # Import here to avoid circular imports
        from app.llm.processor import process_with_llm

        company_info = process_with_llm(
            scraped_data=scraped_data,
            query=query,
        )

        _logger.info(f"Task {task_id}: LLM processing completed")
        self.update_state(
            state="PROGRESS",
            meta={
                "status": "processing",
                "progress": 90,
                "message": "Finalizing results",
                "started_at": created_at.isoformat(),
            },
        )

        # Step 3: Finalize and return results
        duration = time.time() - start_time

        result = {
            "company_info": company_info.model_dump(mode="json"),
            "query": query,
            "duration_seconds": round(duration, 2),
            "created_at": created_at.isoformat(),
            "completed_at": datetime.now(UTC).isoformat(),
        }

        _logger.info(f"Task {task_id} completed successfully in {duration:.2f}s for query: {query}")

        return result

    except Exception as e:
        duration = time.time() - start_time
        _logger.error(
            f"Task {task_id} failed after {duration:.2f}s: {e}",
            exc_info=True,
        )

        # Update state to FAILURE with error details
        self.update_state(
            state="FAILURE",
            meta={
                "status": "failed",
                "progress": 0,
                "message": f"Task failed: {str(e)}",
                "error": str(e),
                "error_type": type(e).__name__,
                "started_at": created_at.isoformat(),
                "failed_at": datetime.now(UTC).isoformat(),
                "duration_seconds": round(duration, 2),
                "exc_type": type(e).__name__,
                "exc_message": e.__str__(),
            },
        )

        # Re-raise the exception for Celery to handle retries
        raise


@celery_app.task(name="cleanup_expired_tasks", queue="default")  # type: ignore
def cleanup_expired_tasks() -> dict[str, Any]:
    """
    Periodic task to clean up expired task results.

    This should be scheduled with Celery Beat:
    celery -A app.celery_app.celery_config beat

    Returns:
        Dictionary with cleanup statistics
    """
    _logger.info("Running cleanup task for expired results")

    # This is a placeholder - actual implementation would depend on
    # how you're storing task results (Redis, database, etc.)

    cleaned_count = 0

    # Example cleanup logic:
    # - Query all task IDs from Redis
    # - Check if they're older than TASK_RESULT_EXPIRES
    # - Delete expired ones

    _logger.info(f"Cleanup completed. Removed {cleaned_count} expired task results")

    return {
        "cleaned_count": cleaned_count,
        "timestamp": datetime.now(UTC).isoformat(),
    }


# Periodic task schedule (Celery Beat)
celery_app.conf.beat_schedule = {
    "cleanup-expired-tasks": {
        "task": "cleanup_expired_tasks",
        "schedule": 3600.0,  # Run every hour
    },
}
