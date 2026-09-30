from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

MAX_SECTION_LENGTH = 2800
MIN_TABLE_LINES = 2
ELLIPSIS_LENGTH = 3

VERDICT_MAP: dict[str, tuple[str, str]] = {
    "COMPLIANT": ("COMPLIANT", "✅"),
    "REVISIONS REQUIRED": ("REVISIONS REQUIRED", "⚠️"),
    "NON-COMPLIANT": ("NON-COMPLIANT", "❌"),
}

EMOJI_SHORTCODES: dict[str, str] = {
    ":pushpin:": "📌",
    ":white_check_mark:": "✅",
    ":warning:": "⚠️",
    ":x:": "❌",
    ":clipboard:": "📋",
    ":bar_chart:": "📊",
    ":chart_with_upwards_trend:": "📈",
    ":chart_with_downwards_trend:": "📉",
    ":tools:": "🛠️",
    ":hammer_and_wrench:": "🛠️",
    ":wrench:": "🔧",
    ":scales:": "⚖️",
    ":balance_scale:": "⚖️",
    ":heavy_check_mark:": "✔️",
    ":white_square:": "▫️",
    ":white_medium_square:": "▫️",
    ":mag:": "🔍",
    ":mag_right:": "🔍",
    ":bulb:": "💡",
    ":target:": "🎯",
    ":memo:": "📝",
    ":robot_face:": "🤖",
    ":small_blue_diamond:": "🔹",
    ":dart:": "🎯",
    ":shield:": "🛡️",
    ":zap:": "⚡",
    ":hourglass_flowing_sand:": "⏳",
    ":hourglass:": "⌛",
}


@dataclass(frozen=True)
class ResponseCardParams:
    """Parameters to format a Slack response into a polished card."""

    text: str
    title: str = ""
    agent_name: str = "AIAssistant"
    model_name: str = ""
    accent_color: str = "#1A85FF"
    has_footer: bool = True


def _protect_code_blocks(text: str) -> tuple[str, list[str]]:
    """Extract fenced code blocks and inline code to protect them from regex formatting."""
    placeholders: list[str] = []

    def replace_fenced(match: re.Match[str]) -> str:
        idx = len(placeholders)
        placeholders.append(match.group(0))
        return f"__CODE_BLOCK_{idx}__"

    protected = re.sub(r"```[\s\S]*?```", replace_fenced, text)

    def replace_inline(match: re.Match[str]) -> str:
        idx = len(placeholders)
        placeholders.append(match.group(0))
        return f"__INLINE_CODE_{idx}__"

    protected = re.sub(r"`[^`\n]+`", replace_inline, protected)
    return protected, placeholders


def _restore_code_blocks(text: str, placeholders: list[str]) -> str:
    """Restore extracted code blocks back into the text."""
    result = text
    for idx, block in enumerate(placeholders):
        result = result.replace(f"__CODE_BLOCK_{idx}__", block)
        result = result.replace(f"__INLINE_CODE_{idx}__", block)
    return result


def _replace_emoji_shortcodes(text: str) -> str:
    """Convert common Slack emoji shortcodes into standard Unicode emojis."""
    result = text
    for shortcode, emoji in EMOJI_SHORTCODES.items():
        result = result.replace(shortcode, emoji)
    return result


def _normalize_headings(text: str) -> str:
    """Transform markdown, numbered, and lettered headings into bold emoji headings."""
    formatted = re.sub(r"(?m)^###\s+(.+)$", r"🔹 *\1*", text)
    formatted = re.sub(r"(?m)^##\s+(.+)$", r"📌 *\1*", formatted)
    formatted = re.sub(r"(?m)^#\s+(.+)$", r"📊 *\1*", formatted)
    formatted = re.sub(r"(?m)^([0-9]+[\)\.])\s+([^\n]+)$", r"\n📊 *\1 \2*\n", formatted)
    formatted = re.sub(r"(?m)^([A-Z][\)\.])\s+([^\n]+)$", r"\n🔹 *\1 \2*\n", formatted)
    heading_pattern = re.compile(
        r"(?m)^([📋📊📌🔹🔍💡🎯]|🛠️?|⚖️?|⚠️?)\s+([A-Z][A-Za-z0-9\s&/\-_]+?):?\s*$"
    )
    return heading_pattern.sub(r"\1 *\2*", formatted)


def _normalize_bullets(text: str) -> str:
    """Normalize bullet items and format definition prefixes."""
    formatted = re.sub(r"(?m)^[\*\-]\s+(.+)$", r"• \1", text)
    formatted = re.sub(r"(?m)^•\s+([A-Za-z][A-Za-z0-9\s/]{1,35}):\s+", r"• *\1:* ", formatted)
    return re.sub(r"(?m)^•\s+(.+?)\s+-\s+", r"• *\1:* ", formatted)


def _format_summary_callout(lead: str, body: str) -> str:
    """Format an executive summary callout blockquote with cleanly separated sections."""
    if not body:
        return lead

    parts = body.split("\n\n", 1)
    summary_para = parts[0].strip()
    rest = parts[1].strip() if len(parts) > 1 else ""

    quoted_lines = [f"> {line}" if line.strip() else ">" for line in summary_para.splitlines()]
    callout = f"{lead}\n" + "\n".join(quoted_lines)
    return f"{callout}\n\n{rest}" if rest else callout


def _normalize_residue_summary(text: str) -> str | None:
    """Detect and clean multiple-choice menu residue from executive summaries."""
    residue_pattern = re.compile(
        r"(?i)^(?:[📌\s]*)?Executive\s+Summary:?\s*"
        r"COMPLIANT[^\n/]*[/|\\]\s*REVISIONS REQUIRED[^\n/]*[/|\\]\s*NON-COMPLIANT[^\n]*\n+"
        r"(?:\s*Overall\s+status:\s*([^\n]+)\n+)?",
        re.MULTILINE,
    )
    res_match = residue_pattern.search(text)
    if not res_match:
        return None

    raw_verdict = (res_match.group(1) or "").upper()
    matched_tuple = next((v for k, v in VERDICT_MAP.items() if k in raw_verdict), None)
    verdict_str, emoji = matched_tuple if matched_tuple else ("REVISIONS REQUIRED", "⚠️")
    body = text[res_match.end() :].strip()
    lead = f"> 📌 *Executive Summary:* *{verdict_str}* {emoji}"
    return _format_summary_callout(lead, body)


def _normalize_direct_verdict_summary(text: str) -> str | None:
    """Detect and format direct verdict summary (e.g. Executive Summary: NON-COMPLIANT: ...)."""
    direct_pattern = re.compile(
        r"(?i)^(?:>\s*)?(?:[📌\s]*)?Executive\s+Summary:?\s*"
        r"(NON-COMPLIANT|REVISIONS REQUIRED|COMPLIANT)\s*[:—\-]?\s*(.*)$",
        re.MULTILINE,
    )
    dir_match = direct_pattern.search(text)
    if not dir_match:
        return None

    verdict_key = dir_match.group(1).upper().strip()
    verdict_str, emoji = VERDICT_MAP.get(verdict_key, (verdict_key, "⚠️"))
    body = dir_match.group(2).strip()
    lead = f"> 📌 *Executive Summary:* *{verdict_str}* {emoji}"
    return _format_summary_callout(lead, body)


def _normalize_preamble_summary(text: str) -> str | None:
    """Detect conversational opening preamble and wrap in blockquote."""
    preamble_pattern = re.compile(r"^(Here(?:'s| is| are)[^\n]+)(.*)$", re.IGNORECASE | re.DOTALL)
    opening_match = preamble_pattern.match(text)
    if not opening_match:
        return None

    lead, rest = opening_match.groups()
    lead_clean = lead.strip().rstrip(":")
    return f"> 📌 *Executive Summary:* {lead_clean}\n\n{rest.strip()}"


def _normalize_executive_summary(text: str) -> str:
    """Ensure opening summary or conversational preamble has blockquote formatting."""
    residue_cleaned = _normalize_residue_summary(text)
    if residue_cleaned is not None:
        return residue_cleaned

    stripped = text.strip()
    has_callout = stripped.startswith(">") or "*Executive Summary*" in stripped
    if has_callout:
        return text

    direct_cleaned = _normalize_direct_verdict_summary(text)
    if direct_cleaned is not None:
        return direct_cleaned

    preamble_cleaned = _normalize_preamble_summary(text)
    if preamble_cleaned is not None:
        return preamble_cleaned

    if stripped.lower().startswith("executive summary:"):
        body = stripped[len("executive summary:") :].strip()
        lead = "> 📌 *Executive Summary:*"
        return _format_summary_callout(lead, body)

    return text


def _clean_artifacts(text: str) -> str:
    """Strip chat client copy-paste timestamps, rogue header tokens, and redundant newlines."""
    cleaned = re.sub(r"\[\d{1,2}:\d{2}\s*(?:AM|PM)?\]", "", text)
    cleaned = re.sub(r"(?m)^HEADER\s*", "", cleaned)
    cleaned = re.sub(r"(?m)\s*HEADER$", "", cleaned)
    cleaned = re.sub(r"^HEADER\s*•", "•", cleaned)
    cleaned = re.sub(r"(?m)^text\s+(Findings|Summary|Table)", r"\1", cleaned)
    return re.sub(r"\n{3,}", "\n\n", cleaned)


def _clean_table_code_blocks(text: str) -> str:
    """Unwrap code blocks that enclose markdown tables so they can be formatted."""
    cleaned = re.sub(r"```[a-z]*\s*(\|.+)", r"\1", text)

    def unwrap(match: re.Match[str]) -> str:
        content = match.group(1).strip()
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        is_table = bool(lines and lines[0].startswith("|") and ("|" in lines[0]))
        return f"\n\n{content}\n\n" if is_table else match.group(0)

    return re.sub(r"```[a-z]*\n([\s\S]*?)```", unwrap, cleaned)


def _format_cell_value(val: str, width: int, is_last: bool) -> str:
    """Format a cell value, truncating the last column if it exceeds width."""
    if not is_last:
        return f"{val:<{width}}"
    is_overflow = len(val) > width
    return (
        f"{val[: width - ELLIPSIS_LENGTH]}..." if is_overflow and width > ELLIPSIS_LENGTH else val
    )


def _render_table_row(row: list[str], widths: list[int]) -> str:
    """Render a single table row with column alignment and 2-space padding."""
    num_cols = len(widths)
    cells: list[str] = []
    for i, width in enumerate(widths):
        val = row[i] if i < len(row) else ""
        is_last = i == (num_cols - 1)
        cells.append(_format_cell_value(val, width, is_last))
    return "  ".join(cells).rstrip()


def _compute_compact_widths(
    headers: list[str], rows: list[list[str]], max_width: int = 78
) -> list[int]:
    """Calculate column widths for compact 1-line-per-row table."""
    num_cols = len(headers)
    widths = [len(h) for h in headers]
    for row in rows:
        for i in range(min(num_cols, len(row))):
            widths[i] = max(widths[i], len(row[i]))

    if num_cols > 1:
        last_col = num_cols - 1
        prefix_width = sum(widths[:last_col]) + (2 * last_col)
        widths[last_col] = max(18, max_width - prefix_width)

    return widths


def _render_ascii_table(headers: list[str], rows: list[list[str]], max_width: int = 78) -> str:
    """Format tabular data into a sleek, compact monospace table with 1 line per item."""
    widths = _compute_compact_widths(headers, rows, max_width)
    header_line = _render_table_row(headers, widths)
    divider_len = max(len(header_line), min(max_width, sum(widths) + 2 * (len(widths) - 1)))
    divider = "-" * divider_len

    output_lines: list[str] = [header_line, divider]
    for row in rows:
        output_lines.append(_render_table_row(row, widths))

    return "```\n" + "\n".join(output_lines) + "\n```"


def _is_table_divider(line: str) -> bool:
    """Check if line is a markdown table divider (e.g. |---|---|)."""
    return bool(re.match(r"^\|?[-:\s|]+\|?$", line.strip()))


def _convert_table_match(match: re.Match[str]) -> str:
    """Convert a single matched markdown table into a compact monospace table."""
    raw_table = match.group(1).strip()
    fixed_table = re.sub(r"\|\s*\|", "|\n|", raw_table)
    raw_lines = [line.strip() for line in fixed_table.splitlines() if line.strip()]
    if len(raw_lines) < MIN_TABLE_LINES:
        return raw_table

    headers = [c.strip() for c in raw_lines[0].strip("|").split("|")]
    data_lines = [line for line in raw_lines[1:] if not _is_table_divider(line)]
    rows = [[c.strip() for c in line.strip("|").split("|")] for line in data_lines]
    is_valid_table = bool(headers and rows)
    if not is_valid_table:
        return raw_table

    return f"\n\n{_render_ascii_table(headers, rows)}\n\n"


def _format_markdown_tables(text: str) -> str:
    """Detect and convert markdown tables into aligned ASCII monospace tables."""
    unwrapped = _clean_table_code_blocks(text)
    pattern = re.compile(r"(?:^|\n)((?:\|[^\n]+\|\r?\n?){2,})", re.MULTILINE)
    return pattern.sub(_convert_table_match, unwrapped)


def format_slack_mrkdwn(raw_text: str) -> str:
    """
    Normalize standard Markdown syntax into clean Slack-compatible mrkdwn.

    - Replaces **bold** with *bold*
    - Converts emoji shortcodes into standard Unicode emojis
    - Converts markdown links [text](url) to <url|text>
    - Converts markdown, numbered, and lettered headers into bold emoji-badged headers
    - Converts bullet item terms to bold labels
    - Converts markdown tables into compact 1-line monospace tables
    - Formats executive summary with clean callout blockquote and single verdict
    - Preserves fenced code blocks and inline code unchanged
    """
    if not raw_text.strip():
        return raw_text

    unwrapped_tables = _clean_table_code_blocks(raw_text)
    protected, placeholders = _protect_code_blocks(unwrapped_tables)

    # 1. Convert emoji shortcodes to Unicode emojis
    formatted = _replace_emoji_shortcodes(protected)

    # 2. Convert standard markdown links [Label](https://...) to <https://...|Label>
    formatted = re.sub(r"\[([^\]]+)\]\((https?://[^\)]+)\)", r"<\2|\1>", formatted)

    # 3. Convert standard markdown bold **text** to *text*
    formatted = re.sub(r"\*\*([^\*\n]+)\*\*", r"*\1*", formatted)

    # 4. Clean artifacts and normalize sections
    formatted = _clean_artifacts(formatted)
    formatted = _normalize_headings(formatted)
    formatted = _normalize_bullets(formatted)
    formatted = _format_markdown_tables(formatted)
    formatted = _normalize_executive_summary(formatted)
    formatted = _clean_artifacts(formatted)

    return _restore_code_blocks(formatted, placeholders)


def _slice_long_line(line: str, max_chars: int) -> list[str]:
    """Slice a single oversized line into chunks bounded by max_chars."""
    return [line[i : i + max_chars] for i in range(0, len(line), max_chars)]


def _partition_oversized_lines(lines: list[str], max_chars: int) -> list[str]:
    """Ensure no individual line exceeds max_chars by slicing oversized lines."""
    normalized: list[str] = []
    for line in lines:
        is_oversized = len(line) > max_chars
        chunks = _slice_long_line(line, max_chars) if is_oversized else [line]
        normalized.extend(chunks)
    return normalized


def _accumulate_lines(lines: list[str], max_chars: int) -> list[str]:
    """Group lines into chunks without exceeding max character length."""
    chunks: list[str] = []
    current_lines: list[str] = []
    current_length = 0

    for line in lines:
        line_len = len(line) + 1
        exceeds_limit = (current_length + line_len > max_chars) and bool(current_lines)
        if exceeds_limit:
            chunks.append("\n".join(current_lines))
            current_lines = [line]
            current_length = line_len
            continue

        current_lines.append(line)
        current_length += line_len

    if current_lines:
        chunks.append("\n".join(current_lines))

    return chunks


def _split_oversized_paragraph(paragraph: str, max_chars: int) -> list[str]:
    """Split a paragraph exceeding max_chars into bounded line groups."""
    raw_lines = paragraph.split("\n")
    safe_lines = _partition_oversized_lines(raw_lines, max_chars)
    return _accumulate_lines(safe_lines, max_chars)


def _flatten_paragraphs(paragraphs: list[str], max_chars: int) -> list[str]:
    """Split any paragraph exceeding max_chars into safe sub-paragraphs."""
    result: list[str] = []
    for paragraph in paragraphs:
        is_oversized = len(paragraph) > max_chars
        sub_paras = (
            _split_oversized_paragraph(paragraph, max_chars) if is_oversized else [paragraph]
        )
        result.extend(sub_paras)
    return result


def _accumulate_paragraphs(paragraphs: list[str], max_chars: int) -> list[str]:
    """Group paragraphs into chunks without exceeding max character length."""
    chunks: list[str] = []
    current_chunk: list[str] = []
    current_length = 0

    for paragraph in paragraphs:
        para_len = len(paragraph) + 2
        exceeds_limit = (current_length + para_len > max_chars) and bool(current_chunk)
        if exceeds_limit:
            chunks.append("\n\n".join(current_chunk))
            current_chunk = [paragraph]
            current_length = para_len
            continue

        current_chunk.append(paragraph)
        current_length += para_len

    if current_chunk:
        chunks.append("\n\n".join(current_chunk))

    return chunks


def split_text_into_sections(text: str, max_chars: int = MAX_SECTION_LENGTH) -> list[str]:
    """Split long text into chunks that satisfy Slack's 3,000-char section block limit."""
    if len(text) <= max_chars:
        return [text]

    raw_paragraphs = text.split("\n\n")
    safe_paragraphs = _flatten_paragraphs(raw_paragraphs, max_chars)
    return _accumulate_paragraphs(safe_paragraphs, max_chars)


def _build_footer_blocks(params: ResponseCardParams) -> list[dict[str, Any]]:
    """Build divider and context footer block with agent metadata."""
    if not params.has_footer:
        return []

    footer_elements: list[dict[str, str]] = []
    if params.agent_name:
        footer_elements.append({"type": "mrkdwn", "text": f"🤖 *{params.agent_name}*"})

    if not footer_elements:
        return []

    return [
        {"type": "divider"},
        {"type": "context", "elements": footer_elements},
    ]


def _build_section_blocks(chunks: list[str]) -> list[dict[str, Any]]:
    """Convert text chunks into Slack section blocks."""
    return [
        {"type": "section", "text": {"type": "mrkdwn", "text": chunk}}
        for chunk in chunks
        if chunk.strip()
    ]


def _build_header_blocks(params: ResponseCardParams) -> list[dict[str, Any]]:
    """Build header block if a title is provided."""
    if not params.title.strip():
        return []
    return [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": params.title.strip()[:150],
                "emoji": True,
            },
        }
    ]


def build_response_blocks(params: ResponseCardParams) -> list[dict[str, Any]]:
    """Construct structured Slack Block Kit blocks from text and metadata."""
    formatted_text = format_slack_mrkdwn(params.text)
    text_chunks = split_text_into_sections(formatted_text)
    header_blocks = _build_header_blocks(params)
    section_blocks = _build_section_blocks(text_chunks)
    footer_blocks = _build_footer_blocks(params)
    return header_blocks + section_blocks + footer_blocks


def build_response_attachment(params: ResponseCardParams) -> dict[str, Any]:
    """
    Wrap response blocks into a Slack secondary attachment with a colored side accent bar.

    Provides the distinctive left-border color branding for each bot persona.
    """
    blocks = build_response_blocks(params)
    return {
        "color": params.accent_color,
        "blocks": blocks,
    }
