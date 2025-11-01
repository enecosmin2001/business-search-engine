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

        prompt = f"""Extract structured business data from the web content below and return a single valid JSON object.

        **Search Query:** {query}

        **Web Content:**
        {cleaned_markdown}

        ---

        **Required JSON Schema:**
        {{
            "legal_name": "string or null",
            "marketing_name": "string or null",
            "website": "string or null",
            "linkedin_url": "string or null",
            "facebook_url": "string or null",
            "employee_count": "integer or null",
            "employee_range": "string or null",
            "industry": "string or null",
            "founded_year": "integer or null",
            "headquarters": "string or null",
            "full_address": "string or null",
            "street_address": "string or null",
            "city": "string or null",
            "state": "string or null",
            "country": "string or null",
            "postal_code": "string or null",
            "seo_description": "string or null",
            "description": "string or null",
            "confidence_score": "float (0.0-1.0)",
            "sources": ["array of URLs"]
        }}

        ---

        **Extraction Rules:**

        1. **Prefer explicit data** over inference; use `null` if missing/uncertain
        2. **Normalize URLs** to include `https://` prefix
        3. **Employee data:**
        - Exact number → `employee_count` (integer), `employee_range` = null
        - Range/phrase (e.g. "51-200", "100+") → store original text in `employee_range`, estimate midpoint/lower bound for `employee_count`
        4. **Addresses:** Use null for "Remote", "N/A", or unknown values
        5. **Sources:** List all valid URLs found (website, LinkedIn, etc.)
        6. **Confidence score:**
        - 0.9-1.0: All major fields present
        - 0.7-0.9: Most fields present, minor gaps
        - 0.5-0.7: Basic data only
        - 0.3-0.5: Minimal info
        - <0.3: Very incomplete

        **Output only valid JSON** — no markdown fences, comments, or explanations.
        """
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
                options={"temperature": 0.0, "format": "json"},
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
                "sources": [],
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
