# Subtask 3.3: Content Injection & Context Synthesis

> **Task Reference:** `TASK-03` > `SUBTASK-3.3`  
> **Source Rule:** `agent_rules/01-python-guidelines.md` §5  

---

## 1. Description

Implement prompt synthesis in `src/files/injector.py` to package extracted file contents with metadata headers, handle truncation for context window protection, and inject the formatted text into the agent prompt.

---

## 2. Requirements & Implementation Details

### 2.1 File: `src/files/injector.py`
- Structured Document Header:
  ```python
  @dataclass(frozen=True)
  class ExtractedDocument:
      file_id: str
      file_name: str
      file_type: str
      text_content: str
      char_count: int
  ```
- Formatting Function:
  ```python
  def synthesize_prompt_with_files(
      user_prompt: str,
      documents: list[ExtractedDocument],
      max_chars_per_doc: int = 40000,
  ) -> str:
      """Prepend extracted document texts to user prompt with clear boundary markers."""
  ```
- **Boundary Layout:**
  ```text
  [ATTACHED DOCUMENT: contract.pdf (Type: pdf, Characters: 18250)]
  --- START DOCUMENT CONTENT ---
  {extracted_text}
  --- END DOCUMENT CONTENT ---

  User Request: {user_prompt}
  ```
- **Truncation Guard:** If `char_count > max_chars_per_doc`, truncate gracefully with an explicit notice:
  `"... [Content truncated due to context limits: 40000 of 95000 characters shown]"`

---

## 3. Verification

Create unit test `tests/unit/test_injector.py`:
1. Synthesize 2 documents with prompt: formats boundary tags properly.
2. Truncation test: text exceeding 40k characters truncates with warning marker.
