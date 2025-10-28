from datetime import datetime
from pathlib import Path

import html2text


# -------------------------------------------------------------------------
# Utility Functions
# -------------------------------------------------------------------------
def save_debug_html(content: str, path: Path, name_prefix: str = "page") -> Path:
    """Save an HTML snapshot for debugging."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = Path(f"./logs/{name_prefix}_{ts}.html")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def html_to_markdown(content: str) -> str:
    """Convert HTML content to Markdown."""
    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = True
    return h.handle(content)
