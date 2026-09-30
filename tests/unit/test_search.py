from __future__ import annotations

from unittest.mock import MagicMock, patch

from slack_agent.agent.tools.search import (
    _clean_search_query,
    _format_search_hits,
    web_search,
)


def test_clean_search_query() -> None:
    raw = r"site:drarefin.com/surgery \"cost of surgery\""
    cleaned = _clean_search_query(raw)
    assert cleaned == 'site:drarefin.com "cost of surgery"'


def test_format_search_hits_with_slack_links() -> None:
    hits = [
        {
            "title": "Gallbladder Surgery Guide",
            "href": "https://drarefin.com/surgery/gallbladder",
            "body": "Typical laparoscopic surgery costs 40,000 to 80,000 BDT in Bangladesh.",
        },
        {
            "title": "Hospital Price Index 2026",
            "href": "https://example.org/pricing",
            "body": "Private clinics range up to 120,000 BDT depending on room category.",
        },
    ]

    formatted = _format_search_hits(hits)

    # Clickable Slack links: <URL|Label>
    assert "<https://drarefin.com/surgery/gallbladder|Gallbladder Surgery Guide>" in formatted
    assert "<https://example.org/pricing|Hospital Price Index 2026>" in formatted
    assert "40,000 to 80,000 BDT" in formatted
    assert "• <https://" in formatted


def test_format_search_hits_without_href() -> None:
    hits = [{"title": "Offline Resource", "href": "", "body": "Summary content."}]
    formatted = _format_search_hits(hits)
    assert "**Offline Resource**" in formatted
    assert "Summary content." in formatted


@patch("slack_agent.agent.tools.search._execute_ddgs_query")
def test_web_search_success(mock_execute: MagicMock) -> None:
    mock_execute.return_value = [
        {
            "title": "Health Ministry Guidelines",
            "href": "https://dghs.gov.bd/guidelines",
            "body": "Official fee structure for medical facilities.",
        }
    ]

    result = web_search.invoke({"query": "surgery costs in bangladesh"})

    assert "<https://dghs.gov.bd/guidelines|Health Ministry Guidelines>" in result
    assert "Official fee structure" in result


@patch("slack_agent.agent.tools.search._execute_ddgs_query")
def test_web_search_empty_results(mock_execute: MagicMock) -> None:
    mock_execute.return_value = []
    result = web_search.invoke({"query": "nonexistent query 12345"})
    assert "No relevant web search results found" in result


@patch("slack_agent.agent.tools.search._execute_ddgs_query")
def test_web_search_exception_handling(mock_execute: MagicMock) -> None:
    mock_execute.side_effect = ConnectionError("Search API timeout")
    result = web_search.invoke({"query": "test query"})
    assert "could not be completed due to a temporary network issue" in result
