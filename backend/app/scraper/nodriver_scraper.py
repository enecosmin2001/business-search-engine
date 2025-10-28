"""
Web Scraper using Nodriver (CDP-based)
Scrapes company information from Google AI search.
"""

import asyncio
import logging
from pathlib import Path
from types import TracebackType
from typing import Any

import nodriver as uc

from app.scraper.utils import html_to_markdown

# -------------------------------------------------------------------------
# Setup Logging
# -------------------------------------------------------------------------
_logger = logging.getLogger(__name__)


# -------------------------------------------------------------------------
# Browser Manager
# -------------------------------------------------------------------------
class BrowserManager:
    """Context-managed wrapper around Nodriver Browser."""

    def __init__(self, headless: bool = True, lang: str = "en-US,en"):
        self.headless = headless
        self.lang = lang
        self.browser: uc.Browser | None = None
        self.tab: uc.Tab | None = None

    @property
    def safe_tab(self) -> uc.Tab:
        if self.tab is None:
            raise RuntimeError("Browser tab is not initialized.")
        return self.tab

    async def __aenter__(self) -> "BrowserManager":
        await self._start_browser()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.stop()

    async def _start_browser(self):
        """Start browser with stealth settings."""
        _logger.info("Launching browser...")
        self.browser = await uc.start(
            headless=self.headless,
            sandbox=False,
            browser_args=[
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-software-rasterizer",
                "--no-sandbox",
                "--remote-debugging-port=9222",
                f"--lang={self.lang}",
                "--disable-blink-features=AutomationControlled",
            ],
        )
        self.tab = await self.browser.get("about:blank")
        await self._apply_stealth_settings()

    async def _apply_stealth_settings(self):
        """Apply user agent, timezone, device metrics, and JS spoofing."""
        assert self.tab

        ua = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
        await self.tab.send(uc.cdp.network.set_user_agent_override(ua))
        await self.tab.send(uc.cdp.emulation.set_timezone_override(timezone_id="America/New_York"))
        await self.tab.send(
            uc.cdp.emulation.set_device_metrics_override(
                width=1366, height=768, device_scale_factor=1, mobile=False
            )
        )

        spoof_js = Path(__file__).with_name("stealth_patch.js")
        if spoof_js.exists():
            script = spoof_js.read_text()
            try:
                await self.tab.send(
                    uc.cdp.page.add_script_to_evaluate_on_new_document(source=script)
                )
                await self.tab.evaluate(script)
            except Exception as e:
                _logger.warning(f"Failed to inject stealth JS: {e}")

    async def stop(self):
        """Stop browser gracefully."""
        if self.browser:
            try:
                self.browser.stop()
                _logger.info("Browser closed.")
            except Exception as e:
                _logger.warning(f"Failed to stop browser: {e}")


# -------------------------------------------------------------------------
# Google AI Scraper
# -------------------------------------------------------------------------
class GoogleAIScraper:
    """Handles AI-powered Google search interactions."""

    def __init__(self, browser: BrowserManager, query: str):
        self.browser = browser
        self.query = query
        self.tab = browser.safe_tab

    async def scrape(self) -> str:
        """Perform the scraping flow."""
        assert self.tab, "Browser tab not initialized"
        await self.tab.get("https://www.google.com/?hl=en")
        await asyncio.sleep(3)

        await self._accept_cookies()
        await self._enable_ai_mode()

        await self._ask_questions()
        markdown = html_to_markdown(await self.tab.get_content())
        return markdown

    async def _accept_cookies(self):
        """Accept cookie banner if present."""
        cookie_btn = await self.tab.find("accept all", best_match=True)
        if cookie_btn:
            await cookie_btn.click()
            await asyncio.sleep(2)

    async def _enable_ai_mode(self):
        """Switch to AI mode."""
        ai_mode_btn = await self.tab.find("AI Mode", best_match=True)
        if not ai_mode_btn:
            raise RuntimeError("AI Mode button not found on Google.")
        await ai_mode_btn.click()
        await asyncio.sleep(3)

    async def _ask_questions(self):
        """Ask structured questions about the company."""
        questions = [
            (
                "legal_business_name and marketing_name (short name or DBA)",
                f"Key-value format only. Company: {self.query}",
            ),
            ("website_url, linkedin_url, facebook_url", "Return all values in key-value format."),
            (
                "industry, employees_count, employee_range, full_address, "
                "street_address, city, state, country, postal_code, "
                "seo_description, description",
                "Return all values in key-value format.",
            ),
        ]

        for _idx, (keys, prompt) in enumerate(questions, start=1):
            question = f"Keep the answer short and direct. What are the {keys}? {prompt}"
            await self._ask(question)
            await asyncio.sleep(3)

    async def _ask(self, question: str):
        """Send a question to the Google AI input."""
        search_bar = await self.tab.find(text="ask", best_match=True)
        if not search_bar:
            raise RuntimeError("Could not locate the AI search bar.")
        await search_bar.mouse_click()
        await asyncio.sleep(1)
        await search_bar.send_keys(question)
        await self.tab.send(
            uc.cdp.input_.dispatch_key_event(
                type_="keyDown", key="Enter", code="Enter", windows_virtual_key_code=13
            )
        )
        await self.tab.send(
            uc.cdp.input_.dispatch_key_event(
                type_="keyUp", key="Enter", code="Enter", windows_virtual_key_code=13
            )
        )


# -------------------------------------------------------------------------
# Orchestrator
# -------------------------------------------------------------------------
class CompanyScraper:
    """High-level interface to scrape company info."""

    @staticmethod
    async def scrape_async(query: str, timeout: int = 30) -> dict[str, Any]:
        _logger.info(f"Starting company info scraping for: {query}")
        async with BrowserManager() as browser:
            scraper = GoogleAIScraper(browser, query)
            markdown = await asyncio.wait_for(scraper.scrape(), timeout=timeout)
        return {"query": query, "content_markdown": markdown}

    @staticmethod
    def scrape(query: str, timeout: int = 30) -> dict[str, Any]:
        return asyncio.run(CompanyScraper.scrape_async(query, timeout))
