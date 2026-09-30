# Subtask 7.1: Isolated Mocking & Unit Tests

> **Task Reference:** `TASK-07` > `SUBTASK-7.1`  
> **Source Rule:** `agent_rules/01-python-guidelines.md`, `agent_rules/03-error-handling-architecture.md`  

---

## 1. Description

Construct unit test fixtures and mock suites in `tests/unit/` verifying isolated components without network calls.

---

## 2. Test Suites & Coverage Targets

### 2.1 Test Matrix
1. **`tests/unit/test_errors_and_result.py`:**
   - Test `Result.ok(val)` and `Result.fail(err)`.
   - Test guard failure when accessing `val = result.value()` on failure.
   - Test `AppError.wrap()` with custom context and path.
2. **`tests/unit/test_config.py`:**
   - Test validation of `xoxb-` and `xapp-` prefixes.
   - Test missing required variables fail gracefully with `ValidationError`.
3. **`tests/unit/test_parsers.py`:**
   - Test PDF parsing with multi-page in-memory PDF.
   - Test Word DOCX parsing with tables and headings.
   - Test CSV and code files parsing.
4. **`tests/unit/test_proposals.py`:**
   - Test proposal saving and retrieval.
   - Test TTL expiration eviction.
5. **`tests/unit/test_approval_cards.py`:**
   - Test Block Kit structure and button action IDs.

---

## 3. Execution Command

```bash
uv run pytest tests/unit -v
```
