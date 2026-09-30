from __future__ import annotations

from slack_agent.slack.blocks.response_card import (
    ResponseCardParams,
    build_response_attachment,
    build_response_blocks,
    format_slack_mrkdwn,
    split_text_into_sections,
)


def test_format_slack_mrkdwn_bold_and_links() -> None:
    raw = "Check out **Quarterly Report** at [Report Link](https://example.com/report)."
    formatted = format_slack_mrkdwn(raw)
    assert "*Quarterly Report*" in formatted
    assert "<https://example.com/report|Report Link>" in formatted
    assert "**" not in formatted


def test_format_slack_mrkdwn_headings() -> None:
    raw = "# Main Title\n\n## Sub Title\n\n### Section"
    formatted = format_slack_mrkdwn(raw)
    assert "📊 *Main Title*" in formatted
    assert "📌 *Sub Title*" in formatted
    assert "🔹 *Section*" in formatted
    assert "#" not in formatted


def test_format_slack_mrkdwn_preserves_code_blocks() -> None:
    raw = (
        "Here is the code:\n"
        "```python\n"
        "# Python comment\n"
        "x = **not_bold**\n"
        "```\n"
        "Also see `x = **inline**` for details."
    )
    formatted = format_slack_mrkdwn(raw)
    # Inside code blocks, content must NOT be altered
    assert "# Python comment" in formatted
    assert "x = **not_bold**" in formatted
    assert "`x = **inline**`" in formatted


def test_split_text_into_sections() -> None:
    short_text = "This is a short paragraph."
    assert len(split_text_into_sections(short_text, max_chars=100)) == 1

    para1 = "A" * 80
    para2 = "B" * 80
    long_text = f"{para1}\n\n{para2}"
    chunks = split_text_into_sections(long_text, max_chars=100)
    assert len(chunks) == 2
    assert chunks[0] == para1
    assert chunks[1] == para2


def test_build_response_blocks_and_attachment() -> None:
    params = ResponseCardParams(
        text="Executive Summary:\n**Strong growth** across all segments.",
        agent_name="AnalystBot",
        accent_color="#007A5A",
        has_footer=True,
    )

    blocks = build_response_blocks(params)
    assert len(blocks) >= 2
    # Section block
    assert blocks[0]["type"] == "section"
    assert "*Strong growth*" in blocks[0]["text"]["text"]

    # Context footer block
    context_block = next((b for b in blocks if b["type"] == "context"), None)
    assert context_block is not None
    footer_text = " ".join(e["text"] for e in context_block["elements"])
    assert "AnalystBot" in footer_text
    assert "claude" not in footer_text

    # Attachment wrapper
    attachment = build_response_attachment(params)
    assert attachment["color"] == "#007A5A"
    assert "blocks" in attachment
    assert attachment["blocks"] == blocks


def test_format_slack_mrkdwn_numbered_sections_and_definitions() -> None:
    raw = (
        "1) Key architectural differences\n"
        "- Per-interpreter GIL - introduces sub-interpreters\n"
        "A) Sub Benchmark\n"
        "[5:24 PM]"
    )
    formatted = format_slack_mrkdwn(raw)
    assert "📊 *1) Key architectural differences*" in formatted
    assert "• *Per-interpreter GIL:* introduces sub-interpreters" in formatted
    assert "🔹 *A) Sub Benchmark*" in formatted
    assert "[5:24 PM]" not in formatted


def test_format_slack_mrkdwn_conversational_preamble() -> None:
    raw = (
        "Here's a concise, engineer-focused comparison of Python 3.11 vs 3.12.\n\n"
        "1) Key Differences"
    )
    formatted = format_slack_mrkdwn(raw)
    assert "> 📌 *Executive Summary:* Here's a concise, engineer-focused comparison" in formatted


def test_split_text_into_sections_oversized_single_paragraph() -> None:
    oversized_para = "A" * 3500
    chunks = split_text_into_sections(oversized_para, max_chars=2800)
    assert len(chunks) == 2
    assert all(len(c) <= 2800 for c in chunks)
    assert len(chunks[0]) == 2800
    assert len(chunks[1]) == 700


def test_split_text_into_sections_oversized_table_with_single_newlines() -> None:
    # 35 lines of 100 characters each separated by \n (no \n\n)
    table_lines = [f"Item {i:02d}: " + ("x" * 90) for i in range(35)]
    raw_table = "\n".join(table_lines)
    assert len(raw_table) > 3000

    chunks = split_text_into_sections(raw_table, max_chars=2800)
    assert len(chunks) >= 2
    assert all(len(c) <= 2800 for c in chunks)
    # Joining chunks with newlines restores all lines
    rejoined = "\n".join(chunks)
    assert rejoined == raw_table


def test_split_text_into_sections_oversized_unbroken_line() -> None:
    unbroken = "Z" * 6000
    chunks = split_text_into_sections(unbroken, max_chars=2800)
    assert len(chunks) == 3
    assert all(len(c) <= 2800 for c in chunks)
    assert "".join(chunks) == unbroken


def test_build_response_blocks_all_sections_under_slack_limit() -> None:
    row_template = "Item {i:02d} | Standard {std} | PASS | Citation clause {i} "
    rows = [row_template.format(i=i, std=i % 5 + 1) * 3 for i in range(30)]
    huge_compliance_report = "### Compliance Audit Findings\n\n" + "\n".join(rows)
    params = ResponseCardParams(
        text=huge_compliance_report,
        agent_name="KITA-Analyst",
        accent_color="#007A5A",
        has_footer=True,
    )
    blocks = build_response_blocks(params)
    section_blocks = [b for b in blocks if b["type"] == "section"]
    assert len(section_blocks) >= 2
    for block in section_blocks:
        block_text = block["text"]["text"]
        assert len(block_text) <= 2800
        assert len(block_text) < 3001


def test_format_slack_mrkdwn_converts_markdown_table_to_ascii_grid() -> None:
    raw = (
        "### Audit Findings\n\n"
        "| Item | Standard | Status | Citation |\n"
        "|---|---|---|---|\n"
        "| 1.1 | CS13/CSS2 | FAIL | Missing Regulator/NRT logo |\n"
        "| 1.5 | CS71a | FAIL | RTO code not visible |\n"
        "| 1.6 | CS71b | PASS | Nationally recognised unit |"
    )
    formatted = format_slack_mrkdwn(raw)
    assert "```" in formatted
    assert "---" in formatted
    assert "Item" in formatted
    assert "Standard" in formatted
    assert "CS13/CSS2" in formatted
    assert "FAIL" in formatted
    assert "PASS" in formatted


def test_format_slack_mrkdwn_handles_glued_table_rows() -> None:
    raw = (
        "| Item ID | Standard | Status | Citation || "
        "1.1 | CS13/CSS2 | FAIL | No logo || "
        "1.5 | CS71a | FAIL | Missing RTO code |"
    )
    formatted = format_slack_mrkdwn(raw)
    assert "```" in formatted
    assert "---" in formatted
    assert "1.1" in formatted
    assert "1.5" in formatted


def test_format_slack_mrkdwn_replaces_emoji_shortcodes() -> None:
    raw = ":pushpin: Header :warning: alert :white_check_mark: success :tools: fix"
    formatted = format_slack_mrkdwn(raw)
    assert "📌" in formatted
    assert "⚠️" in formatted
    assert "✅" in formatted
    assert "🛠️" in formatted
    assert ":pushpin:" not in formatted
    assert ":warning:" not in formatted


def test_format_slack_mrkdwn_cleans_compliance_verdict_residue() -> None:
    raw = (
        ":pushpin: Executive Summary: COMPLIANT :white_check_mark: / "
        "REVISIONS REQUIRED :warning: / NON-COMPLIANT :x:\n"
        " Overall status: REVISIONS REQUIRED :warning:\n"
        " The document largely describes telehandler training offerings accurately.\n\n"
        ":clipboard: AUDIT SCOPE & DETAILS:\n"
        "• Material audited: Attached document — kita_article.pdf"
    )
    formatted = format_slack_mrkdwn(raw)
    assert "> 📌 *Executive Summary:* *REVISIONS REQUIRED* ⚠️" in formatted
    assert "COMPLIANT :white_check_mark:" not in formatted
    assert "Overall status:" not in formatted
    assert "The document largely describes" in formatted
    assert "📋 *AUDIT SCOPE & DETAILS*" in formatted
    assert "• *Material audited:* Attached document" in formatted


def test_format_slack_mrkdwn_direct_compliance_verdict() -> None:
    raw = (
        "Executive Summary: NON-COMPLIANT : The document does not visibly display RTO logos.\n\n"
        ":clipboard: AUDIT SCOPE & DETAILS:\n"
        "• Scope: Telehandler audit"
    )
    formatted = format_slack_mrkdwn(raw)
    assert "> 📌 *Executive Summary:* *NON-COMPLIANT* ❌" in formatted
    assert "The document does not visibly display" in formatted


def test_format_slack_mrkdwn_cleans_rogue_header_tokens() -> None:
    raw = (
        "HEADER• Scope: Audit of document kita_article.pdf\n"
        "HEADER\n"
        "text Findings Table\n"
        "• Overall status: NON-COMPLIANT"
    )
    formatted = format_slack_mrkdwn(raw)
    assert "HEADER" not in formatted
    assert "text Findings" not in formatted
    assert "• *Scope:* Audit of document" in formatted
    assert "Findings Table" in formatted


def test_build_response_blocks_renders_header_block_when_title_present() -> None:
    params = ResponseCardParams(
        text="Executive summary content",
        title="⚖️ RTO Marketing Compliance Audit",
        agent_name="KITA-Analyst",
    )
    blocks = build_response_blocks(params)
    assert blocks[0]["type"] == "header"
    assert blocks[0]["text"]["text"] == "⚖️ RTO Marketing Compliance Audit"
    assert any(b["type"] == "section" for b in blocks)
    assert any(b["type"] == "context" for b in blocks)
