"""
LLM Processor
Processes scraped data using local or cloud LLM to extract structured information
"""

import logging
from typing import Any

from app.models.schemas import CompanyInfo

_logger = logging.getLogger(__name__)


def process_with_llm(
    scraped_data: dict[str, Any],
    query: str,
) -> CompanyInfo:
    """
    Process scraped data with LLM to extract structured company information.

    This is the main entry point called by the Celery task.

    Args:
        scraped_data: Dictionary with scraped data from web sources
        query: Original search query

    Returns:
        CompanyInfo model with extracted data
    """
    _logger.info(f"Processing scraped data with LLM for query: {query}")

    # Return minimal valid CompanyInfo
    return CompanyInfo(
        marketing_name=query,
        confidence_score=0.0,
    )
