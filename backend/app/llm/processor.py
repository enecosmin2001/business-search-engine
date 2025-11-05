"""
LLM Processor
Processes scraped data using local or cloud LLM to extract structured information.
"""

import json
import logging
import re
from pathlib import Path
from typing import Any

from app.config import settings
from app.models.schemas import CompanyInfo

_logger = logging.getLogger(__name__)

# RFC 3986–inspired URL regex (handles http, https, www, query params, fragments, ports, etc.)
URL_REGEX = re.compile(
    r"\b(?:(?:https?|ftp):\/\/|www\.)"
    r"[-a-zA-Z0-9@:%._\+~#=]{1,256}"
    r"\.[a-zA-Z0-9()]{1,6}\b"
    r"([-a-zA-Z0-9()@:%_\+.~#?&//=]*)",
    re.IGNORECASE,
)


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

    def clean_markdown(self, markdown: str) -> tuple[str, list[str]]:
        """
        Clean and preprocess scraped markdown content.
        Returns a tuple: (cleaned_markdown, extracted_urls)
        """

        import re

        cleaned = markdown.replace("\r", "").replace("\n\n", "\n").strip()

        # --- Remove Google / UI / boilerplate noise ---
        noise_patterns = [
            r"Please click.*?seconds\.",
            r"# Accessibility links.*?(AI Mode|Start new search)",
            r"(Start new search|Open AI Mode history|Delete this search\?.*?Cancel)",
            r"(Shared public links.*?Delete all\nCancel)",
            r"Thank you.*?Privacy.*?Close",
            r"Map data ©.*?(AI responses|AI-generated responses).*?\.",
            r"\b(Learn more|Report a problem)\b",
            r"\b(\d+\s+sites|Show all)\b",
        ]
        for pattern in noise_patterns:
            cleaned = re.sub(pattern, "", cleaned, flags=re.S | re.I)

        # --- Extract and remove URLs ---
        urls, cleaned = self.extract_and_clean_urls(cleaned)

        # --- Deduplicate lines ---
        seen = set()
        lines = []
        for line in cleaned.split("\n"):
            line = line.strip()
            if line and line not in seen:
                seen.add(line)
                lines.append(line)
        cleaned = "\n".join(lines)

        cleaned = re.sub(r"\n{2,}", "\n\n", cleaned).strip()

        return cleaned, urls

    def extract_and_clean_urls(self, text: str):
        """
        Extracts all full URLs from text and removes them cleanly.
        Returns (urls, cleaned_text)
        """
        urls = re.findall(URL_REGEX, text)

        # `re.findall` returns only captured groups if parentheses are present,
        # so we use re.finditer instead to get full matches.
        urls = [m.group(0) for m in re.finditer(URL_REGEX, text)]

        cleaned_text = re.sub(URL_REGEX, "", text)
        cleaned_text = re.sub(r"\s+", " ", cleaned_text).strip()

        return urls, cleaned_text

    def create_extraction_prompt(self, query: str, markdown: str) -> str:
        """
        Create a prompt for the LLM to extract company information.
        """
        cleaned_markdown, urls = self.clean_markdown(markdown)

        prompt = f"""
        You are an AI data extractor. Analyze the provided web content and extract **structured business information** as a single, valid JSON object.

        Be exhaustive and prefer to fill as many fields as possible instead of leaving them null.
        If multiple possible values appear, choose the one most consistent across sources.
        Normalize and clean all text values.
        Use URLs in the text to infer social or company links where possible.
        If data is ambiguous, include the most probable option and lower the confidence score accordingly.
        Do not include explanations or markdown — output only the JSON object.

        ---

        **Search Query:** {query}
        **URLs Found:** {urls}
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

        1. **Data completeness**
        - Extract every distinct data point that appears relevant.
        - Prefer explicit data over inferred values.
        - Use `null` only if the value is missing or unclear.

        2. **URLs & Sources**
        - Normalize all URLs to include the `https://` prefix.
        - Use any valid link found in content (website, LinkedIn, Facebook, Crunchbase, etc.) as potential sources.
        - Use only URLs that clearly relate to the company by having the company name in the domain or page title.
        - Deduplicate URLs.

        3. **Employees**
        - Exact number → `employee_count` (integer), `employee_range` = null.
        - Range/phrase (e.g. "51-200", "100+") → store text in `employee_range`, estimate midpoint or lower bound for `employee_count`.

        4. **Addresses**
        - Combine available pieces into `headquarters` and `full_address`.
        - Use `null` for “Remote”, “N/A”, or unknown values.

        5. **Confidence scoring**
        - 0.9-1.0 → All major fields present.
        - 0.7-0.9 → Most fields present, minor gaps.
        - 0.5-0.7 → Basic company info only.
        - 0.3-0.5 → Minimal or partial info.
        - <0.3 → Very incomplete.

        6. **Final Output**
        - Return **only valid JSON**, no markdown, comments, or prose.
        - Do not include any text before or after the JSON.

        ---

        Now extract the business data from the provided content and return **a single JSON object** following the schema exactly.

        """

        # save prompt for debugging
        save_path = Path("./logs/llm_prompts")
        save_path.mkdir(parents=True, exist_ok=True)
        prompt_file = save_path / f"extraction_prompt_{query}.txt"
        prompt_file.write_text(prompt, encoding="utf-8")
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
                options={"temperature": 0.0, "format": "json", "num_ctx": 16384},
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
