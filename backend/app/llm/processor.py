"""
LLM Processor
Processes scraped data using local or cloud LLM to extract structured information.
"""

import json
import logging
from typing import Any

from app.config import settings
from app.models.schemas import CompanyInfo

_logger = logging.getLogger(__name__)


class LLMProcessor:
    """
    LLM processor for extracting structured company information.
    """

    def __init__(
        self,
        provider: str = "ollama",
        model: str = "llama3.2",
        base_url: str | None = None,
    ) -> None:
        """
        Initialize LLM processor.

        Args:
            provider: LLM provider (ollama, openai, groq)
            model: Model name
            base_url: Base URL for the LLM API
        """
        self.provider = provider
        self.model = model
        self.base_url = base_url or settings.LLM_BASE_URL

    def clean_markdown(self, markdown: str) -> str:
        """
        Clean and preprocess markdown content.
        """
        cleaned = markdown.replace("\n\n", "\n").strip()

        # Extract only the relevant content if markers exist
        start_marker = "What is the legal_business_name"
        end_marker = "AI responses may include mistakes"
        start_idx = cleaned.find(start_marker)
        end_idx = cleaned.rfind(end_marker)
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            cleaned = cleaned[start_idx + len(start_marker) : end_idx].strip()

        return cleaned

    def create_extraction_prompt(self, query: str, markdown: str) -> str:
        """
        Create a prompt for the LLM to extract company information.
        """
        cleaned_markdown = self.clean_markdown(markdown)
        max_context_length = 8000
        if len(cleaned_markdown) > max_context_length:
            cleaned_markdown = cleaned_markdown[:max_context_length] + "\n\n[Content truncated...]"

        prompt = f"""You are a business information extraction assistant. Your task is to extract structured company information from the provided web content.

        Search Query: {query}

        Web Content:
        {cleaned_markdown}

        Extract the following information about the company and return it as a JSON object.

        CRITICAL INSTRUCTIONS FOR EACH FIELD:

        1. legal_name: The official registered business name (e.g., "Argyle Systems Inc.")
        2. marketing_name: The common brand name or DBA (e.g., "Argyle")
        3. website: Full URL starting with https:// (e.g., "https://argyle.com")
        4. linkedin_url: LinkedIn company page URL (e.g., "https://www.linkedin.com/company/argylesystems")
        5. facebook_url: Facebook page URL or null if not found
        6. employee_count: INTEGER ONLY - extract the exact number of employees. If no numeric data, use null
        7. employee_range: STRING ONLY - the exact range as text (e.g., "51-200", "201-500", "1000+"). If not found, use null
        8. industry: Primary business sector (e.g., "Financial Services / Financial Software")
        9. founded_year: 4-digit integer year (e.g., 2018) or null
        10. headquarters: City and country (e.g., "New York, USA")
        11. full_address: Complete address with all available components
        12. street_address: Street number and name only, or null
        13. city: City name only (e.g., "New York")
        14. state: State/province (e.g., "New York" or "NY")
        15. country: Country name (e.g., "United States" or "USA")
        16. postal_code: Postal/ZIP code or null
        17. seo_description: One-sentence company description from SEO meta
        18. description: Detailed 2-3 sentence description of what the company does
        19. confidence_score: Float 0.0-1.0 based on data completeness

        PARSING RULES:
        - Never put ranges in employee_count field - it must be an integer or null
        - Never put integers in employee_range field - it must be a string range or null
        - If address says "N/A" or "Remote First", set those specific fields to null
        - Extract city/state/country even if full street address is unavailable

        CONFIDENCE SCORE GUIDELINES:
        - 0.9-1.0: All major fields present with verified data
        - 0.7-0.9: Most fields present, minor fields missing
        - 0.5-0.7: Several important fields missing or uncertain
        - 0.3-0.5: Only basic information available
        - 0.0-0.3: Very limited or unreliable data

        Return ONLY valid JSON with this exact structure:
        {{
            "legal_name": "string or null",
            "marketing_name": "string or null",
            "website": "string or null",
            "linkedin_url": "string or null",
            "facebook_url": "string or null",
            "employee_count": integer or null,
            "employee_range": "string or null",
            "industry": "string or null",
            "founded_year": integer or null,
            "headquarters": "string or null",
            "full_address": "string or null",
            "street_address": "string or null",
            "city": "string or null",
            "state": "string or null",
            "country": "string or null",
            "postal_code": "string or null",
            "seo_description": "string or null",
            "description": "string or null",
            "confidence_score": float
        }}

        JSON Response:"""
        return prompt

    def extract_with_ollama(self, prompt: str) -> dict[str, object]:
        """
        Extract information using Ollama.
        """
        try:
            from ollama import Client

            client = Client(host=self.base_url)
            _logger.info(f"Calling Ollama model '{self.model}' at {self.base_url}")

            response = client.generate(
                model=self.model,
                prompt=prompt,
                options={
                    "temperature": settings.LLM_TEMPERATURE,
                    "num_predict": settings.LLM_MAX_TOKENS,
                },
            )

            response_text = response.get("response", "")

            _logger.debug(f"Ollama raw response (first 500 chars): {response_text[:500]}")
            return self.parse_json_response(response_text)

        except Exception as e:
            _logger.error(f"Ollama extraction failed: {e}", exc_info=True)
            raise RuntimeError(f"Ollama extraction failed: {e}") from e

    def parse_json_response(self, response_text: str) -> dict[str, object]:
        """
        Parse JSON from LLM response text.
        """
        try:
            text = response_text.strip()

            # Remove markdown fences (```json ... ```)
            if text.startswith("```"):
                text = text.strip("`")
                if "json" in text.lower():
                    text = text[text.lower().find("json") + 4 :]
                text = text.replace("```", "").strip()

            # Attempt to extract JSON object boundaries
            start_idx = text.find("{")
            end_idx = text.rfind("}") + 1

            if start_idx != -1 and end_idx > start_idx:
                json_str = text[start_idx:end_idx]
                return json.loads(json_str)

            return json.loads(text)

        except json.JSONDecodeError as e:
            _logger.error(f"Failed to parse JSON from LLM response: {e}")
            _logger.debug(f"Raw response text: {response_text[:1000]}")

            # Fallback structure
            return {
                "legal_name": None,
                "marketing_name": None,
                "website": None,
                "linkedin_url": None,
                "facebook_url": None,
                "employee_count": None,
                "employee_range": None,
                "industry": None,
                "founded_year": None,
                "headquarters": None,
                "full_address": None,
                "street_address": None,
                "city": None,
                "state": None,
                "country": None,
                "postal_code": None,
                "seo_description": None,
                "description": None,
                "confidence_score": 0.0,
            }

    def extract(self, query: str, scraped_markdown: str) -> dict[str, Any]:
        """
        Extract company information using the configured LLM provider.
        """
        prompt = self.create_extraction_prompt(query, scraped_markdown)

        match self.provider.lower():
            case "ollama":
                return self.extract_with_ollama(prompt)
            case _:
                raise ValueError(f"Unsupported LLM provider: {self.provider}")


def process_with_llm(scraped_data: dict[str, object], query: str) -> CompanyInfo:
    """
    Process scraped data with LLM to extract structured company information.
    """
    scraped_markdown = str(scraped_data.get("content_markdown", ""))
    _logger.info(f"Processing scraped data with LLM for query: '{query}'")

    processor = LLMProcessor(
        provider=settings.LLM_PROVIDER,
        model=settings.LLM_MODEL,
        base_url=settings.LLM_BASE_URL,
    )

    extracted_data = processor.extract(query, scraped_markdown)

    try:
        company_info = CompanyInfo(**extracted_data)
        _logger.info(
            f"Successfully extracted company info "
            f"({company_info.legal_name or company_info.marketing_name}) "
            f"with confidence {company_info.confidence_score:.2f}"
        )
        return company_info

    except Exception as e:
        _logger.error(f"Failed to create CompanyInfo model: {e}", exc_info=True)
        return CompanyInfo(marketing_name=query, confidence_score=0.0)
