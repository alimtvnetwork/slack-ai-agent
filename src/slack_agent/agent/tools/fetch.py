from __future__ import annotations

import re

import httpx
from bs4 import BeautifulSoup
from langchain_core.tools import tool

from slack_agent.core.logger import get_logger

logger = get_logger(__name__)

_DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)
_TAGS_TO_REMOVE = (
    "script",
    "style",
    "nav",
    "footer",
    "header",
    "noscript",
    "aside",
    "form",
    "svg",
    "iframe",
)


def _sanitize_url(url: str) -> str:
    """Normalize and validate target URL string, handling Slack link formatting."""
    cleaned = url.strip().strip("<>\"'")
    if "|" in cleaned:
        cleaned = cleaned.split("|", 1)[0]
    cleaned = cleaned.strip()
    if not cleaned.startswith(("http://", "https://")):
        return f"https://{cleaned}"
    return cleaned


def _extract_text_from_html(html_content: str, max_chars: int, source_url: str = "") -> str:
    """Extract readable text from HTML markup, removing scripts and boilerplate."""
    soup = BeautifulSoup(html_content, "html.parser")
    for tag in soup(_TAGS_TO_REMOVE):
        tag.decompose()

    page_title = soup.title.string.strip() if soup.title and soup.title.string else "Untitled Page"
    body_text = "\n".join(soup.stripped_strings)
    body_text = re.sub(r"\n{3,}", "\n\n", body_text)
    source_prefix = f"Source: <{source_url}|{page_title}>\n\n" if source_url else ""
    full_text = f"# {page_title}\n\n{source_prefix}{body_text}"

    if len(full_text) > max_chars:
        return f"{full_text[:max_chars]}\n\n[...Content truncated due to length...]"

    return full_text


@tool
def fetch_web_page(url: str, max_chars: int = 15000) -> str:
    """
    Fetch and read the full text content of a specific web page or article URL.

    You MUST call this tool whenever the user provides a specific website link or URL
    and asks you to summarize, analyze, or answer questions about that specific page.
    """
    target_url = _sanitize_url(url)
    try:
        headers = {"User-Agent": _DEFAULT_USER_AGENT}
        with httpx.Client(headers=headers, follow_redirects=True, timeout=15.0) as client:
            response = client.get(target_url)
            response.raise_for_status()

        return _extract_text_from_html(response.text, max_chars=max_chars, source_url=target_url)
    except httpx.HTTPStatusError as http_err:
        logger.warning(
            "HTTP error fetching web page",
            extra={"Url": target_url, "StatusCode": http_err.response.status_code},
        )
        return f"Could not read web page from {target_url} (HTTP {http_err.response.status_code})."
    except Exception as exc:
        logger.warning(
            "Unexpected error fetching web page",
            extra={"Url": target_url, "Error": str(exc)},
        )
        return f"Could not fetch web page from {target_url}: {exc}"
