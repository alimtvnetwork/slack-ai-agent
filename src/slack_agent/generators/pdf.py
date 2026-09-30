from __future__ import annotations

import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer

from slack_agent.core.errors import ERR_PDF_RENDER_FAILED, AppError, ErrorCategoryType
from slack_agent.core.result import Result


def generate_pdf_bytes(title: str, content: str) -> Result[bytes]:
    """Render publication-quality styled PDF bytes using ReportLab Platypus."""
    try:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=54,
            leftMargin=54,
            topMargin=54,
            bottomMargin=54,
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "ReportTitle",
            parent=styles["Heading1"],
            fontSize=18,
            leading=22,
            textColor=colors.HexColor("#1A1D21"),
            spaceAfter=10,
        )
        body_style = ParagraphStyle(
            "ReportBody",
            parent=styles["Normal"],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#2C3136"),
            spaceAfter=8,
        )

        story: list[Paragraph | Spacer | HRFlowable] = [
            Paragraph(title, title_style),
            HRFlowable(
                width="100%",
                thickness=1,
                color=colors.HexColor("#E2E8F0"),
                spaceAfter=12,
            ),
        ]

        for block in content.split("\n\n"):
            clean_block = block.strip().replace("\n", "<br/>")
            if clean_block:
                story.append(Paragraph(clean_block, body_style))
                story.append(Spacer(1, 4))

        doc.build(story)
        return Result.ok(buffer.getvalue())
    except Exception as exc:
        return Result.fail(
            AppError.wrap(
                exc,
                code=ERR_PDF_RENDER_FAILED,
                message="ReportLab Platypus failed to render PDF document",
                category=ErrorCategoryType.FileSystem,
                context={"Title": title},
            )
        )
