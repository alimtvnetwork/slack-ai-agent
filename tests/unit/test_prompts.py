from __future__ import annotations

from slack_agent.agent.prompts import SYSTEM_PROMPT


def test_system_prompt_excel_directives() -> None:
    # Verifies Excel (.xlsx/.xls) multi-sheet directives
    assert "Excel" in SYSTEM_PROMPT
    assert ".xlsx" in SYSTEM_PROMPT
    assert "explore all sheets" in SYSTEM_PROMPT.lower()
    assert "sheet names" in SYSTEM_PROMPT.lower()


def test_system_prompt_chart_directives() -> None:
    # Verifies proactive chart generation and tool invocation directives
    assert "generate_chart" in SYSTEM_PROMPT
    assert "proactively generate" in SYSTEM_PROMPT.lower()
    assert "numeric comparisons" in SYSTEM_PROMPT.lower()
    assert "time-series trends" in SYSTEM_PROMPT.lower()
    assert "`bar`" in SYSTEM_PROMPT
    assert "`line`" in SYSTEM_PROMPT
    assert "`pie`" in SYSTEM_PROMPT


def test_system_prompt_human_in_the_loop_write_gate() -> None:
    # Verifies write gate protection
    assert "propose_file_write" in SYSTEM_PROMPT
    assert "HUMAN-IN-THE-LOOP WRITE GATE" in SYSTEM_PROMPT


def test_system_prompt_web_citations() -> None:
    # Verifies Slack clickable links and sources section
    assert "<URL|Page Title or Domain>" in SYSTEM_PROMPT
    assert "📚 *Sources:*" in SYSTEM_PROMPT
