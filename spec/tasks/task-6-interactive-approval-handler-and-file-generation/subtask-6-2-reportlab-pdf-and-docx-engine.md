# Subtask 6.2: ReportLab PDF & DOCX Generation Engine

> **Task Reference:** `TASK-06` > `SUBTASK-6.2`  
> **Source Rule:** `agent_rules/01-python-guidelines.md` §3, `agent_rules/03-error-handling-architecture.md`  

---

## 1. Description

Implement `src/generators/pdf.py` using ReportLab Platypus and `src/generators/docx.py` using `python-docx` to build publication-quality, styled documents directly in memory.

---

## 2. Requirements & Implementation Details

### 2.1 File: `src/generators/pdf.py` (ReportLab Platypus)
- Build in-memory PDF using `io.BytesIO`:
  ```python
  from reportlab.lib.pagesizes import letter
  from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
  from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
  from reportlab.lib import colors

  def generate_pdf_bytes(title: str, content: str) -> Result[bytes]:
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
              fontSize=20,
              leading=24,
              textColor=colors.HexColor("#1A1D21"),
              spaceAfter=12,
          )
          body_style = ParagraphStyle(
              "ReportBody",
              parent=styles["Normal"],
              fontSize=10,
              leading=15,
              textColor=colors.HexColor("#2C3136"),
              spaceAfter=8,
          )
          
          story = [
              Paragraph(title, title_style),
              HRFlowable(width="100%", thickness=1, color=colors.HexColor("#E2E8F0"), spaceAfter=14),
          ]
          
          # Format paragraphs
          for block in content.split("\n\n"):
              clean_block = block.strip().replace("\n", "<br/>")
              if clean_block:
                  story.append(Paragraph(clean_block, body_style))
                  story.append(Spacer(1, 6))
                  
          doc.build(story)
          return Result.ok(buffer.getvalue())
      except Exception as exc:
          return Result.fail(
              AppError.wrap(exc, code="E5003", message="ReportLab failed to generate PDF document")
          )
  ```

### 2.2 File: `src/generators/docx.py` (`python-docx`)
- Build in-memory `.docx` document from text/headings.
- Return `Result.ok(buffer.getvalue())`.

---

## 3. Verification

Create unit test `tests/unit/test_generators.py`:
1. Generate sample PDF: returns non-empty byte stream starting with `%PDF-`.
2. Generate sample DOCX: returns non-empty byte stream matching ZIP/DOCX magic bytes.
3. Validate PDF with `pypdf.PdfReader` to verify it opens and parses with zero errors.
