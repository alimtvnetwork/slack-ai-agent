from __future__ import annotations

import re
from typing import Any

from ddgs import DDGS
from langchain_core.tools import tool

from slack_agent.core.logger import get_logger

logger = get_logger(__name__)


def _clean_search_query(raw_query: str) -> str:
    """Sanitize queries from LLM JSON escapes and malformed site operators."""
    cleaned = raw_query.replace(r"\'", "'").replace(r"\"", '"').replace("\\", " ")
    cleaned = re.sub(r"site:([a-zA-Z0-9.-]+)/[^\s]+", r"site:\1", cleaned)
    return " ".join(cleaned.split())


def _format_search_hits(raw_hits: list[dict[str, Any]]) -> str:
    """Format raw search hits into structured markdown bullet points with Slack links."""
    formatted_items: list[str] = []
    for hit in raw_hits:
        title = str(hit.get("title", "No Title")).strip()
        href = str(hit.get("href") or hit.get("url") or "").strip()
        body = str(hit.get("body") or hit.get("snippet") or "").strip()
        link = f"<{href}|{title}>" if href else f"**{title}**"
        formatted_items.append(f"• {link}\n  {body}")

    return "\n\n".join(formatted_items)


def _execute_ddgs_query(query: str, max_results: int) -> list[dict[str, Any]]:
    """Execute text search with automatic operator-fallback and news-fallback."""
    with DDGS() as ddgs:
        hits = list(ddgs.text(query, max_results=max_results))
        if hits:
            return hits

        # Fallback 1: If site: filter caused empty results, strip site: operator
        if "site:" in query:
            fallback_query = re.sub(r"site:\S+", "", query).strip()
            hits = list(ddgs.text(fallback_query, max_results=max_results))
            if hits:
                return hits

        # Fallback 2: Try news endpoint for recent event topics
        news_hits = list(ddgs.news(query, max_results=max_results))
        if news_hits:
            return news_hits

    return []


@tool
def web_search(query: str, max_results: int = 5) -> str:
    """
    Search the live web for external facts, recent news, market data, and documentation.

    Use this tool when external factual knowledge is needed to answer a user's question.
    """
    cleaned_query = _clean_search_query(query)
    try:
        raw_hits = _execute_ddgs_query(cleaned_query, max_results=max_results)
        if not raw_hits:
            return f"No relevant web search results found for query: '{cleaned_query}'."

        return _format_search_hits(raw_hits)
    except Exception as exc:
        logger.warning(
            "DuckDuckGo web search encountered an error",
            extra={"Query": cleaned_query, "Error": str(exc)},
        )
        return f"Web search could not be completed due to a temporary network issue: {exc}"
