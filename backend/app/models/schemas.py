"""
Pydantic Models for Request/Response Schemas
"""

from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, HttpUrl

# ============================================
# Enums
# ============================================


class TaskStatus(str, Enum):
    """Task status enumeration."""

    PENDING = "pending"
    STARTED = "started"
    SCRAPING = "scraping"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class LLMProvider(str, Enum):
    """LLM provider enumeration."""

    OLLAMA = "ollama"
    OPENAI = "openai"
    GROQ = "groq"


# ============================================
# Request Models
# ============================================


class SearchRequest(BaseModel):
    """Request model for company search."""

    query: str = Field(
        ...,
        min_length=2,
        max_length=200,
        description="Company name or business details to search for",
        examples=["Google Inc.", "Tesla Motors", "OpenAI"],
    )

    include_website: bool = Field(
        default=True,
        description="Whether to scrape company website",
    )

    include_linkedin: bool = Field(
        default=False,
        description="Whether to include LinkedIn data (may be slower)",
    )

    timeout: int | None = Field(
        default=None,
        ge=10,
        le=1000,
        description="Custom timeout in seconds (10-300)",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "query": "Google Inc.",
                    "include_website": True,
                    "include_linkedin": False,
                    "timeout": 60,
                }
            ]
        }
    }


# ============================================
# Response Models
# ============================================


class CompanyInfo(BaseModel):
    """Company information extracted from scraping and LLM processing."""

    legal_name: str | None = Field(
        default=None,
        description="Official legal name of the company",
    )

    marketing_name: str | None = Field(
        default=None,
        description="Common marketing or short name",
    )

    website: HttpUrl | None = Field(
        default=None,
        description="Company website URL",
    )

    linkedin_url: HttpUrl | None = Field(
        default=None,
        description="LinkedIn company page URL",
    )

    facebook_url: HttpUrl | None = Field(
        default=None,
        description="Facebook company page URL",
    )

    employee_count: int | None = Field(
        default=None,
        ge=0,
        description="Approximate number of employees",
    )

    employee_range: str | None = Field(
        default=None,
        description="Employee range (e.g., '1-10', '10-50', '50-200')",
    )

    industry: str | None = Field(
        default=None,
        description="Primary industry or sector",
    )

    founded_year: int | None = Field(
        default=None,
        ge=1800,
        le=2025,
        description="Year the company was founded",
    )

    headquarters: str | None = Field(
        default=None,
        description="Headquarters location (city, country)",
    )

    full_address: str | None = Field(
        default=None,
        description="Full address including street, city, state, country, postal code",
    )

    street_address: str | None = Field(
        default=None,
        description="Street address only",
    )

    city: str | None = Field(
        default=None,
        description="City of headquarters",
    )

    state: str | None = Field(
        default=None,
        description="State/province of headquarters",
    )

    country: str | None = Field(
        default=None,
        description="Country of headquarters",
    )

    postal_code: str | None = Field(
        default=None,
        description="Postal code if available",
    )

    seo_description: str | None = Field(
        default=None,
        description="Short SEO description of the company",
    )

    description: str | None = Field(
        default=None,
        max_length=1000,
        description="Brief company description",
    )

    confidence_score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Confidence score of the extracted data (0-1)",
    )

    additional_data: dict[str, Any] | None = Field(
        default=None,
        description="Any additional extracted data",
    )

    sources: list[HttpUrl] = Field(
        default_factory=list,
        description="List of URLs where information was found",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "legal_name": "Argyle Systems Inc.",
                    "marketing_name": "Argyle",
                    "website": "https://argyle.com",
                    "linkedin_url": "https://www.linkedin.com/company/argylesystems",
                    "facebook_url": None,
                    "employee_count": 51,
                    "employee_range": "51-200",
                    "industry": "Financial Services / Financial Software",
                    "founded_year": None,
                    "headquarters": "New York, USA",
                    "full_address": "Remote First / Headquarters in New York, NY, USA",
                    "street_address": None,
                    "city": "New York",
                    "state": "New York (NY)",
                    "country": "United States (USA)",
                    "postal_code": None,
                    "seo_description": "Argyle is a payroll connectivity platform that provides direct-source, consumer-permissioned income and employment verifications to automate financial services workflows.",
                    "description": "Argyle is a payroll connectivity platform that allows businesses to easily access workforce data to verify income and employment, monitor cash-on-hand, and assess credibility. It is used for applications in mortgage, personal lending, tenant screening, and the gig economy.",
                    "confidence_score": 0.9,
                    "sources": [
                        "https://argyle.com",
                        "https://www.linkedin.com/company/argylesystems",
                    ],
                }
            ]
        }
    }


class TaskResponse(BaseModel):
    """Response model when a search task is created."""

    task_id: str = Field(
        ...,
        description="Unique task identifier",
    )

    status: TaskStatus = Field(
        ...,
        description="Current task status",
    )

    message: str = Field(
        ...,
        description="Human-readable status message",
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Task creation timestamp",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "task_id": "abc123def456",
                    "status": "pending",
                    "message": "Search task created successfully",
                    "created_at": "2024-01-15T10:30:00Z",
                }
            ]
        }
    }


class TaskStatusResponse(BaseModel):
    """Response model for task status check."""

    task_id: str = Field(
        ...,
        description="Unique task identifier",
    )

    status: TaskStatus = Field(
        ...,
        description="Current task status",
    )

    progress: int = Field(
        default=0,
        ge=0,
        le=100,
        description="Task progress percentage (0-100)",
    )

    message: str | None = Field(
        default=None,
        description="Current status message",
    )

    result: CompanyInfo | None = Field(
        default=None,
        description="Company information (available when status is 'completed')",
    )

    error: str | None = Field(
        default=None,
        description="Error message (if status is 'failed')",
    )

    created_at: datetime | None = Field(
        ...,
        description="Task creation timestamp",
    )

    started_at: datetime | None = Field(
        default=None,
        description="Task start timestamp",
    )

    completed_at: datetime | None = Field(
        default=None,
        description="Task completion timestamp",
    )

    duration_seconds: float | None = Field(
        default=None,
        description="Task duration in seconds",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "task_id": "abc123def456",
                    "status": "completed",
                    "progress": 100,
                    "message": "Company information extracted successfully",
                    "result": {
                        "legal_name": "Google LLC",
                        "marketing_name": "Google",
                        "website": "https://www.google.com",
                    },
                    "created_at": "2024-01-15T10:30:00Z",
                    "started_at": "2024-01-15T10:30:01Z",
                    "completed_at": "2024-01-15T10:30:45Z",
                    "duration_seconds": 44.5,
                }
            ]
        }
    }


class ErrorResponse(BaseModel):
    """Standard error response model."""

    error: str = Field(
        ...,
        description="Error type or category",
    )

    detail: str = Field(
        ...,
        description="Detailed error message",
    )

    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Error timestamp",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "error": "ValidationError",
                    "detail": "Query must be at least 2 characters long",
                    "timestamp": "2024-01-15T10:30:00Z",
                }
            ]
        }
    }


# ============================================
# WebSocket Models
# ============================================


class WebSocketMessage(BaseModel):
    """WebSocket message model for real-time updates."""

    type: str = Field(
        ...,
        description="Message type (e.g., 'status_update', 'progress', 'result')",
    )

    task_id: str = Field(
        ...,
        description="Associated task ID",
    )

    data: dict[str, Any] = Field(
        ...,
        description="Message payload",
    )

    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Message timestamp",
    )
