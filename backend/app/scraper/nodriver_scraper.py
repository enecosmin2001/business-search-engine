"""
Optimized Google AI Web Scraper using Nodriver
- Keeps human-like typing
- Waits dynamically for 'thinking...' instead of fixed sleeps
- Reduces startup overhead
"""

import asyncio
import logging
from pathlib import Path
from types import TracebackType
from typing import Any

import nodriver as uc

from app.scraper.utils import html_to_markdown

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
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-software-rasterizer",
                "--disable-blink-features=AutomationControlled",
                f"--lang={self.lang}",
            ],
        )
        # Directly open Google
        self.tab = await self.browser.get("about:blank")
        await self._apply_stealth_settings()
        self.tab = await self.browser.get("https://www.google.com/?hl=en")

    async def _apply_stealth_settings(self):
        """Apply user agent, timezone, device metrics, and JS spoofing."""
        assert self.tab
        ua = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
        try:
            await asyncio.wait_for(
                self.tab.send(uc.cdp.network.set_user_agent_override(ua)), timeout=2
            )
            await asyncio.wait_for(
                self.tab.send(
                    uc.cdp.emulation.set_timezone_override(timezone_id="America/New_York")
                ),
                timeout=2,
            )
            await asyncio.wait_for(
                self.tab.send(
                    uc.cdp.emulation.set_device_metrics_override(
                        width=1366, height=768, device_scale_factor=1, mobile=False
                    )
                ),
                timeout=2,
            )
        except Exception as e:
            _logger.warning(f"Failed stealth CDP setup: {e}")

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

    # ---------------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------------
    async def wait_until_text_appears_n_times(self, text: str, n: int, timeout: int = 10):
        """Wait until specific text appears n times in the DOM."""
        for _ in range(timeout * 2):
            try:
                html = await self.tab.get_content()
                if html.lower().count(text.lower()) >= n:
                    return
            except Exception:
                pass
            await asyncio.sleep(0.5)

    # ---------------------------------------------------------------------
    # Main Flow
    # ---------------------------------------------------------------------
    async def scrape(self) -> str:
        """Perform the scraping flow."""
        assert self.tab, "Browser tab not initialized"
        await self._accept_cookies()
        await self._enable_ai_mode()
        await self._ask_questions()
        html = await self.tab.get_content()
        return html_to_markdown(html)

    async def _accept_cookies(self):
        """Accept cookie banner if present."""
        btn = await self.tab.find("accept all", best_match=True)
        if btn:
            await btn.click()
            await asyncio.sleep(0.5)

    async def _enable_ai_mode(self):
        """Switch to AI mode."""
        ai_btn = await self.tab.find("AI Mode", best_match=True)
        if not ai_btn:
            raise RuntimeError("AI Mode button not found on Google.")
        await ai_btn.click()
        await asyncio.sleep(0.5)

    async def _ask_questions(self):
        """Ask structured questions about the company."""
        await self._ask(
            f"""
                What are the : Company Name Website URL Primary Domain Location (city, state, country, street address, postal code) Number of Employees (total and by department) Industry (primary industry and keywords) Annual Revenue Phone Number (corporate general directory) Technologies Used (tech stack) Total Funding Amount Latest Funding Stage Latest Funding Amount Latest Funding Date Founded Year Company Description LinkedIn URL Twitter URL Facebook URL Number of Job Postings Sample Job Posting Titles Publicly Traded Status (symbol, exchange) Buying Intent Signals (identifies companies actively researching products/services) Hiring Trends Website Visitor Tracking Data (identifies anonymous visitors) Company Score (based on custom lead scoring models) Number of Retail Locations Number of Languages (used for business) for the company < {self.query} > ?
            """
        )
        await self.wait_until_text_appears_n_times("AI responses may include mistakes", 1)
        await asyncio.sleep(1)

    async def _ask(self, question: str):
        """Send a question to the Google AI input."""
        search_bar = await self.tab.find(text="ask", best_match=True)
        if not search_bar:
            raise RuntimeError("Could not locate the AI search bar.")

        await search_bar.send_keys(question)

        # Press Enter
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
    async def scrape_async(
        query: str, timeout: int = 1000, headless: bool = True
    ) -> dict[str, Any]:
        _logger.info(f"Starting company info scraping for: {query}")
        async with BrowserManager(headless=headless) as browser:
            scraper = GoogleAIScraper(browser, query)
            markdown = await asyncio.wait_for(scraper.scrape(), timeout=timeout)

        # save markdown for debugging
        save_path = Path("./logs/scraped_markdown")
        save_path.mkdir(parents=True, exist_ok=True)
        md_file = save_path / f"{query.replace(' ', '_')}_scraped.md"
        md_file.write_text(markdown, encoding="utf-8")
        return {"query": query, "content_markdown": markdown}

    @staticmethod
    def scrape(query: str, timeout: int = 1000, headless: bool = True) -> dict[str, Any]:
        return asyncio.run(CompanyScraper.scrape_async(query, timeout, headless))
