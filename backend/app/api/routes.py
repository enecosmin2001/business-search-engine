"""
API Routes for Business Search Engine
Handles search requests and task status checks
"""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.celery_app.tasks import process_company_search
from app.models.schemas import (
    ErrorResponse,
    SearchRequest,
    TaskResponse,
    TaskStatus,
    TaskStatusResponse,
)

router = APIRouter()

_logger = logging.getLogger(__name__)


@router.post(
    "/search",
    response_model=TaskResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        202: {"description": "Search task created successfully"},
        400: {"model": ErrorResponse, "description": "Invalid request"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="Search for company information",
    description="Submit a company search query. Returns a task ID for tracking progress.",
)
async def search_company(request: SearchRequest) -> TaskResponse:
    """
    Create a new company search task.

    This endpoint queues a background task that will:
    1. Search for the company using web scraping
    2. Extract relevant information
    3. Process data with LLM
    4. Return structured company information

    Args:
        request: Search request with company query and options

    Returns:
        TaskResponse with task_id for tracking progress

    Raises:
        HTTPException: If task creation fails
    """
    try:
        _logger.info(f"Received search request for: {request.query}")

        # Create Celery task
        task = process_company_search.apply_async(  # type: ignore
            kwargs={
                "query": request.query,
                "include_website": request.include_website,
                "include_linkedin": request.include_linkedin,
                "timeout": request.timeout,
            }
        )

        _logger.info(f"Created task {task.id} for query: {request.query}")

        return TaskResponse(
            task_id=task.id,
            status=TaskStatus.PENDING,
            message=f"Search task created for '{request.query}'",
        )

    except Exception as e:
        _logger.error(f"Failed to create search task: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create search task: {str(e)}",
        ) from e


@router.get(
    "/status/{task_id}",
    response_model=TaskStatusResponse,
    responses={
        200: {"description": "Task status retrieved successfully"},
        404: {"model": ErrorResponse, "description": "Task not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="Get task status",
    description="Check the status and result of a search task.",
)
async def get_task_status(task_id: str) -> TaskStatusResponse:
    """
    Get the status of a search task.

    Args:
        task_id: Unique task identifier from the search endpoint

    Returns:
        TaskStatusResponse with current status and result (if completed)

    Raises:
        HTTPException: If task is not found or status check fails
    """
    try:
        from app.celery_app.celery_config import celery_app

        # Get task result
        task_result = celery_app.AsyncResult(task_id)

        if not task_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found",
            )

        # Map Celery state to our TaskStatus
        state_mapping = {
            "PENDING": TaskStatus.PENDING,
            "STARTED": TaskStatus.STARTED,
            "SUCCESS": TaskStatus.COMPLETED,
            "FAILURE": TaskStatus.FAILED,
            "RETRY": TaskStatus.STARTED,
            "REVOKED": TaskStatus.FAILED,
        }

        task_status = state_mapping.get(task_result.state, TaskStatus.PENDING)

        # Build response based on task state
        response_data: dict[str, Any] = {
            "task_id": task_id,
            "status": task_status,
            "progress": 0,
            "created_at": (
                task_result.date_done or task_result.info.get("created_at")
                if task_result.info
                else None
            ),
        }

        # Handle different task states
        if task_result.state == "PENDING":
            response_data.update(
                {
                    "progress": 0,
                    "message": "Task is queued and waiting to start",
                }
            )

        elif task_result.state == "STARTED":
            info = task_result.info or {}
            response_data.update(
                {
                    "progress": info.get("progress", 10),
                    "message": info.get("message", "Task is running"),
                    "started_at": info.get("started_at"),
                }
            )

        elif task_result.state == "SUCCESS":
            result = task_result.result
            response_data.update(
                {
                    "progress": 100,
                    "message": "Task completed successfully",
                    "result": result.get("company_info") if isinstance(result, dict) else result,
                    "completed_at": task_result.date_done,
                    "duration_seconds": (
                        result.get("duration_seconds") if isinstance(result, dict) else None
                    ),
                }
            )

        elif task_result.state == "FAILURE":
            error = str(task_result.info) if task_result.info else "Unknown error"
            response_data.update(
                {
                    "progress": 0,
                    "message": "Task failed",
                    "error": error,
                    "completed_at": task_result.date_done,
                }
            )

        return TaskStatusResponse(**response_data)

    except HTTPException:
        raise
    except Exception as e:
        _logger.error(f"Failed to get task status for {task_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task status: {str(e)}",
        ) from e


@router.delete(
    "/task/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        204: {"description": "Task cancelled successfully"},
        404: {"model": ErrorResponse, "description": "Task not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="Cancel a task",
    description="Cancel a running or pending task.",
)
async def cancel_task(task_id: str) -> None:
    """
    Cancel a search task.

    Args:
        task_id: Unique task identifier to cancel

    Raises:
        HTTPException: If task cancellation fails
    """
    try:
        from app.celery_app.celery_config import celery_app

        task_result = celery_app.AsyncResult(task_id)

        if not task_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found",
            )

        # Revoke the task
        task_result.revoke(terminate=True)

        _logger.info(f"Task {task_id} cancelled successfully")

    except HTTPException:
        raise
    except Exception as e:
        _logger.error(f"Failed to cancel task {task_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel task: {str(e)}",
        ) from e
