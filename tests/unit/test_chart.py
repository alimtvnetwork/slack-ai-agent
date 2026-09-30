from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from slack_agent.agent.tools.chart import (
    GeneratedChart,
    clear_generated_charts,
    generate_chart,
    get_generated_charts,
)
from slack_agent.core.config import Settings
from slack_agent.slack.handlers.messages import (
    PipelineExecutionContext,
    _upload_generated_charts,
)


def test_generate_bar_chart() -> None:
    result = generate_chart.invoke(
        {
            "chart_type": "bar",
            "title": "Quarterly Revenue",
            "categories": ["Q1", "Q2", "Q3", "Q4"],
            "values": [100.0, 150.0, 180.0, 220.0],
            "x_label": "Quarter",
            "y_label": "Revenue ($K)",
        }
    )

    assert "✅ Chart generated successfully" in result
    assert "Quarterly Revenue" in result


def test_generate_pie_chart() -> None:
    result = generate_chart.invoke(
        {
            "chart_type": "pie",
            "title": "Department Expense Breakdown",
            "categories": ["Eng", "Sales", "Ops"],
            "values": [50.0, 30.0, 20.0],
        }
    )

    assert "✅ Chart generated successfully" in result


def test_generate_chart_mismatched_counts() -> None:
    result = generate_chart.invoke(
        {
            "chart_type": "bar",
            "title": "Invalid Data",
            "categories": ["A", "B"],
            "values": [10.0],
        }
    )

    assert "Error:" in result


def test_generated_charts_registry() -> None:
    clear_generated_charts()
    assert len(get_generated_charts()) == 0

    generate_chart.invoke(
        {
            "chart_type": "bar",
            "title": "Registry Test Chart",
            "categories": ["A", "B"],
            "values": [1.0, 2.0],
        }
    )

    charts = get_generated_charts()
    assert len(charts) == 1
    assert charts[0].title == "Registry Test Chart"
    assert charts[0].file_path.is_file()

    clear_generated_charts()
    assert len(get_generated_charts()) == 0


@pytest.mark.asyncio
async def test_upload_generated_charts_dispatch(tmp_path: Path) -> None:
    chart_file = tmp_path / "chart_dispatch.png"
    chart_file.write_bytes(b"\x89PNG\r\n\x1a\nFakeChartBytes")

    chart = GeneratedChart(
        chart_id="chart_test_disp",
        title="Regional Sales & Profit",
        chart_type="bar",
        file_path=chart_file,
    )

    mock_client = AsyncMock()
    mock_client.files_upload_v2.return_value = {"ok": True, "file": {"id": "F_CHART_1"}}

    ctx = PipelineExecutionContext(
        channel_id="C_CHART_TEST",
        thread_ts="1700000000.999",
        user_id="U_CHART_USER",
        raw_text="make chart",
        files=[],
        client=mock_client,
        settings=Settings(),
        agent_graph=MagicMock(),
    )

    await _upload_generated_charts([chart], ctx)

    assert mock_client.files_upload_v2.called
    kwargs = mock_client.files_upload_v2.call_args.kwargs
    assert kwargs["channel"] == "C_CHART_TEST"
    assert kwargs["thread_ts"] == "1700000000.999"
    assert kwargs["filename"] == "regional_sales__profit.png"
    assert "📊 *Regional Sales & Profit*" in kwargs["initial_comment"]
