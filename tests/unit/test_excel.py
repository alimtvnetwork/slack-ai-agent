from __future__ import annotations

import io

import openpyxl

from slack_agent.files.parser import parse_excel_bytes, parse_file_bytes


def _generate_test_xlsx_bytes() -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    assert ws is not None
    ws.title = "Q1_Metrics"
    ws.append(["Department", "Budget", "Actual", "Variance"])
    ws.append(["Engineering", 500000, 485000, 15000])
    ws.append(["Marketing", 250000, 260000, -10000])

    ws2 = wb.create_sheet(title="Headcount")
    ws2.append(["Role", "Current", "Open"])
    ws2.append(["Senior Developer", 8, 2])

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def test_parse_excel_bytes_success() -> None:
    xlsx_bytes = _generate_test_xlsx_bytes()
    result = parse_excel_bytes(xlsx_bytes)

    assert result.is_success is True
    content = result.value()
    assert "--- Sheet: Q1_Metrics ---" in content
    assert "Engineering | 500000 | 485000 | 15000" in content
    assert "--- Sheet: Headcount ---" in content
    assert "Senior Developer | 8 | 2" in content


def test_parse_file_bytes_dispatches_excel() -> None:
    xlsx_bytes = _generate_test_xlsx_bytes()
    result = parse_file_bytes(xlsx_bytes, "quarterly_budget.xlsx", "application/vnd.openxmlformats")

    assert result.is_success is True
    assert "Q1_Metrics" in result.value()
