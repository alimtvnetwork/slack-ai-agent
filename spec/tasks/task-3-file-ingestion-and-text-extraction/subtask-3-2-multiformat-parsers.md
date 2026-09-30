# Subtask 3.2: Multi-Format Text Parsers

> **Task Reference:** `TASK-03` > `SUBTASK-3.2`  
> **Source Rule:** `agent_rules/01-python-guidelines.md` §3, `agent_rules/02-general-coding-guidelines.md` §4  

---

## 1. Description

Implement in-memory format parsers in `src/files/parser.py` supporting PDF, Word DOCX, CSV spreadsheets, and plain text/code files.

---

## 2. Requirements & Implementation Details

### 2.1 File: `src/files/parser.py`
- Main dispatcher function:
  ```python
  def parse_file_bytes(
      file_bytes: bytes,
      file_name: str,
      file_type: str,
  ) -> Result[str]:
  ```
- **PDF Parser (`pypdf.PdfReader`):**
  - Read bytes via `io.BytesIO(file_bytes)`.
  - Iterate pages and extract text: `page.extract_text()`.
  - Filter out blank pages; join with `\n\n`.
- **Word DOCX Parser (`docx.Document`):**
  - Read bytes via `io.BytesIO(file_bytes)`.
  - Extract text from all paragraphs and table cells:
    - Paragraph text: `[p.text for p in doc.paragraphs if p.text.strip()]`
    - Tables: Iterate rows and cells, join row cells with ` | `.
- **CSV Parser (`csv.reader`):**
  - Decode UTF-8 (fallback to `latin-1`).
  - Format rows as markdown tables or comma-separated lines.
- **Code & Text Parser:**
  - Support common code extensions (`.py`, `.js`, `.ts`, `.json`, `.yaml`, `.yml`, `.html`, `.sql`, `.sh`, `.txt`, `.md`).
  - Decode with UTF-8 (`errors="replace"`).

### 2.2 Error Handling
- Catch `pypdf.errors.PdfReadError`, `docx.opc.exceptions.PackageNotFoundError`, and `UnicodeDecodeError`.
- Wrap in `AppError.wrap(err, code=ERR_FILE_PARSE_FAILED, message="Failed to parse document text")`.

---

## 3. Verification

Create unit test `tests/unit/test_file_parsers.py`:
1. Parse synthetic PDF generated in memory: extracts expected text.
2. Parse synthetic DOCX generated in memory: extracts paragraphs and table contents.
3. Parse CSV byte stream: converts into clean tabular string.
4. Parse corrupted bytes: gracefully returns `Result.fail()`.
