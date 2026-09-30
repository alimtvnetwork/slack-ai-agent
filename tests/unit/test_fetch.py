from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx

from slack_agent.agent.tools.fetch import (
    _extract_text_from_html,
    _sanitize_url,
    fetch_web_page,
)


def test_sanitize_url_formats() -> None:
    assert _sanitize_url("https://example.com/page") == "https://example.com/page"
    assert _sanitize_url("example.com/path") == "https://example.com/path"
    assert _sanitize_url("<https://example.com/article|Read More>") == "https://example.com/article"
    assert _sanitize_url("<https://example.com>") == "https://example.com"


def test_extract_text_from_html() -> None:
    html = """
    <!DOCTYPE html>
    <html>
      <head>
        <title>Medical Surgery Costs in Bangladesh</title>
        <script>var tracking = true;</script>
        <style>body { font-size: 14px; }</style>
      </head>
      <body>
        <nav><a href="/">Home</a></nav>
        <header><h1>Site Header</h1></header>
        <main>
          <h2>Laparoscopic Cholecystectomy</h2>
          <p>The standard procedure costs between 40,000 and 80,000 BDT in private hospitals.</p>
        </main>
        <footer><p>Copyright 2026</p></footer>
      </body>
    </html>
    """
    text = _extract_text_from_html(html, max_chars=10000)

    assert "Medical Surgery Costs in Bangladesh" in text
    assert "Laparoscopic Cholecystectomy" in text
    assert "40,000 and 80,000 BDT" in text
    assert "tracking = true" not in text
    assert "font-size" not in text
    assert "Site Header" not in text
    assert "Copyright 2026" not in text

    # Verify clickable source header is generated when source_url provided
    text_with_source = _extract_text_from_html(
        html,
        max_chars=10000,
        source_url="https://drarefin.com/surgery",
    )
    expected_header = "Source: <https://drarefin.com/surgery|Medical Surgery Costs in Bangladesh>"
    assert expected_header in text_with_source


def test_extract_text_from_html_truncation() -> None:
    html = (
        "<html><head><title>Title</title></head><body>"
        + "<p>long content</p>" * 50
        + "</body></html>"
    )
    text = _extract_text_from_html(html, max_chars=100)

    assert len(text) <= 160
    assert "[...Content truncated due to length...]" in text


@patch("httpx.Client.get")
def test_fetch_web_page_success(mock_get: MagicMock) -> None:
    mock_resp = MagicMock()
    mock_resp.text = (
        "<html><head><title>Test Page</title></head><body><p>Article body.</p></body></html>"
    )
    mock_resp.status_code = 200
    mock_resp.raise_for_status.return_value = None
    mock_get.return_value = mock_resp

    result = fetch_web_page.invoke({"url": "https://example.com/article"})

    assert "Test Page" in result
    assert "Article body." in result


@patch("httpx.Client.get")
def test_fetch_web_page_http_error(mock_get: MagicMock) -> None:
    mock_resp = MagicMock()
    mock_resp.status_code = 404
    mock_req = MagicMock()
    error = httpx.HTTPStatusError("Not Found", request=mock_req, response=mock_resp)
    mock_get.side_effect = error

    result = fetch_web_page.invoke({"url": "https://example.com/missing"})

    assert "HTTP 404" in result
