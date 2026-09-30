from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import matplotlib
import matplotlib.pyplot as plt
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from slack_agent.core.logger import get_logger

matplotlib.use("Agg")
logger = get_logger(__name__)


@dataclass(frozen=True)
class GeneratedChart:
    """Represents a locally generated chart image awaiting upload to Slack."""

    chart_id: str
    title: str
    chart_type: str
    file_path: Path


_generated_charts: list[GeneratedChart] = []


def get_generated_charts() -> list[GeneratedChart]:
    """Retrieve all generated charts in the current session."""
    return list(_generated_charts)


def clear_generated_charts() -> None:
    """Clear generated charts registry (useful between messages and for tests)."""
    _generated_charts.clear()


class GenerateChartInput(BaseModel):
    """Input parameters for the generate_chart tool."""

    chart_type: str = Field(..., description="Type of chart: 'bar', 'line', or 'pie'")
    title: str = Field(..., description="Title of the chart")
    categories: list[str] = Field(..., description="Category labels for each data point")
    values: list[float] = Field(..., description="Numeric values for each category")
    x_label: str = Field(default="", description="Label for horizontal X axis")
    y_label: str = Field(default="", description="Label for vertical Y axis")


def _plot_series(ax: Any, norm_type: str, categories: list[str], values: list[float]) -> None:
    """Plot data points on matplotlib axes according to chart type."""
    if norm_type == "bar":
        ax.bar(categories, values, color="#1A85FF", edgecolor="#004DA8")
        plt.xticks(rotation=25, ha="right")
    elif norm_type == "line":
        ax.plot(categories, values, marker="o", color="#D41159", linewidth=2.5)
        plt.xticks(rotation=25, ha="right")
    elif norm_type == "pie":
        ax.pie(values, labels=categories, autopct="%1.1f%%", startangle=140)
    else:
        ax.bar(categories, values, color="#1A85FF")
        plt.xticks(rotation=25, ha="right")


def _apply_axes_decorations(ax: Any, params: GenerateChartInput, norm_type: str) -> None:
    """Set labels, title, and styling for chart axes."""
    if norm_type != "pie":
        if params.x_label:
            ax.set_xlabel(params.x_label)
        if params.y_label:
            ax.set_ylabel(params.y_label)
    ax.set_title(params.title, fontsize=13, fontweight="bold", pad=12)


def _render_chart_image(params: GenerateChartInput) -> Path:
    """Render chart to a PNG file using matplotlib headless backend."""
    output_dir = Path("data/charts")
    output_dir.mkdir(parents=True, exist_ok=True)
    file_path = output_dir / f"chart_{uuid.uuid4().hex[:8]}.png"

    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=150)
    norm_type = params.chart_type.lower().strip()
    _plot_series(ax, norm_type, params.categories, params.values)
    _apply_axes_decorations(ax, params, norm_type)

    fig.tight_layout()
    fig.savefig(file_path, format="png")
    plt.close(fig)

    return file_path


@tool("generate_chart", args_schema=GenerateChartInput)
def generate_chart(  # noqa: PLR0913, PLR0917
    chart_type: str,
    title: str,
    categories: list[str],
    values: list[float],
    x_label: str = "",
    y_label: str = "",
) -> str:
    """
    Generate a high-quality visualization chart (bar, line, or pie) from data.

    Call this tool when the user requests a chart, or when analyzing tabular data (e.g. Excel/CSV)
    and visual trend comparison is needed.
    """
    if len(categories) != len(values):
        return (
            f"Error: categories count ({len(categories)}) must match values count ({len(values)})."
        )

    try:
        chart_params = GenerateChartInput(
            chart_type=chart_type,
            title=title,
            categories=categories,
            values=values,
            x_label=x_label,
            y_label=y_label,
        )
        chart_path = _render_chart_image(chart_params)
        _generated_charts.append(
            GeneratedChart(
                chart_id=f"chart_{uuid.uuid4().hex[:8]}",
                title=title,
                chart_type=chart_type,
                file_path=chart_path,
            )
        )
        logger.info(
            "Rendered data chart",
            extra={"Title": title, "Type": chart_type, "Path": str(chart_path)},
        )
        return (
            f"✅ Chart generated successfully: '{title}' ({chart_type}) "
            "saved and queued for Slack upload."
        )
    except Exception as exc:
        logger.warning("Failed to render chart", extra={"Error": str(exc)})
        return f"Failed to generate chart due to an error: {exc}"
