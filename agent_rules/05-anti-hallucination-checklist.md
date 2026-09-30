# Pre-Output Anti-Hallucination Checklist

> **File:** `agent_rules/05-anti-hallucination-checklist.md`  
> **Source Specs:** `guidelines/02-spec/02-coding-guidelines/06-ai-optimization/03-ai-quick-reference-checklist.md`, `guidelines/02-spec/02-coding-guidelines/06-ai-optimization/02-anti-hallucination-rules.md`  
> **Purpose:** Actionable checklist for AI agents to validate generated code and specifications in < 30 seconds before submitting.  

---

## 📋 Pre-Flight Verification Checklist

Before emitting code blocks or concluding a task, verify each item below:

### 1. Repository Protection & Hygiene (Rule Zero)
- [ ] No generated code, test reports, `.pyc` files, `__pycache__/`, `.venv/`, or `.db` files are staged for Git commit.
- [ ] Any new cache or artifact patterns are added to `.gitignore`.

### 2. Naming Standards
- [ ] **Acronyms:** Only first letter capitalized (`UserId`, `SlackApi`, `BaseUrl`, `HttpError`, `JsonData`). Never `ID`, `API`, `URL`.
- [ ] **Variables & Functions:** `snake_case` only (`user_id`, `process_event()`, `fetch_channel_info()`).
- [ ] **Classes & Models:** `PascalCase` (`SlackMessage`, `AgentState`, `AppError`).
- [ ] **Enums:** `PascalCase` with mandatory `Type` suffix (`ActionType`, `MessageType`).
- [ ] **JSON & Serialization Keys:** `PascalCase` (`"UserId"`, `"CreatedAt"`, `"ChannelId"`).
- [ ] **Booleans:** Begin with `is_` or `has_` (99%), `should_` for recommendations. Never `can_`, `was_`, `will_`, `did_`.
- [ ] **Positive Framing:** Zero negative words (`not`, `no`, `non`, `disable`) in boolean names.

### 3. Control Flow & Structure
- [ ] **Zero nested `if`:** Nested conditionals are strictly flattened using early returns and guard clauses.
- [ ] **No `else` after return:** No `else` or `elif` immediately following a `return`, `raise`, `break`, or `continue`.
- [ ] **Condition Complexity:** Maximum 2 conditions per `if`. Never mix `and` with `or` in a single expression.
- [ ] **No Raw Negation on Function Calls:** Used semantic inverse (`payload.is_invalid()`, not `not payload.is_valid()`).
- [ ] **No Boolean Flag Parameters:** Split branching methods into two distinct methods (e.g. `save_draft()` vs `publish()`).
- [ ] **Function Length:** Function body is ≤ 15 lines (target 8–10 lines; error handling lines exempt).
- [ ] **Function Parameters:** Parameter count ≤ 3. If 4+, parameters are bundled into a typed dataclass / Pydantic object.
- [ ] **File Size:** File length is ≤ 300 lines (hard cap 400 lines).

### 4. Python Specifics & Type Safety
- [ ] `from __future__ import annotations` is the first line of the file.
- [ ] Every function and method has full type hints for all parameters and the return value.
- [ ] Zero `Any` in business logic. Generics, Union (`|`), or concrete types are used instead.
- [ ] System boundary inputs/outputs are validated using `pydantic.BaseModel`.
- [ ] Internal parameter bundles use `@dataclass(frozen=True)` or Pydantic `frozen=True`.
- [ ] Used `pathlib.Path` instead of `os.path`.
- [ ] Used f-strings instead of `.format()` or `%`.
- [ ] No mutable default arguments (`def func(items: list = []):` is eliminated).
- [ ] `None` comparisons use identity: `is None` or `is not None` (never `== None`).
- [ ] Imports are sorted into 4 standard groups with single blank lines between them. No wildcard imports (`*`).

### 5. Error Handling Architecture (🔴 CODE RED)
- [ ] **Zero Swallowed Errors:** No empty `except:`, no `except Exception: pass`, no unhandled errors.
- [ ] Caught exceptions are specific (e.g. `SlackApiError`, `ValidationError`), never bare `except:`.
- [ ] Operations return a single monadic `Result[T]` container instead of tuples or untyped returns.
- [ ] **Guard Rule:** Verified `if result.has_error:` before calling `result.value()`.
- [ ] Exceptions are wrapped using `AppError.wrap(err, code, message)` with contextual metadata.
- [ ] Registered error code assigned from the registry (`E1xxx`–`E10xxx`).

### 6. Asynchronous Concurrency (🔴 CODE RED)
- [ ] Independent async operations execute concurrently via `asyncio.gather()`.
- [ ] Zero sequential `await` on independent network, Slack, or LLM calls.
- [ ] Async context managers (`async with`) used for network sessions and connections.

### 7. Caching & State Management (🔴 CODE RED)
- [ ] Never cached an error, empty fallback, or failure response as success.
- [ ] Every cache entry has an explicit TTL.
- [ ] Cache keys are deterministic (no timestamps or random numbers).
- [ ] Mutations immediately invalidate related cache entries.

### 8. Security & Slack Integration
- [ ] No hardcoded tokens, secrets, or API keys in code or documentation.
- [ ] Slack webhook requests verify HMAC-SHA256 signature against signing secret.
- [ ] Handled Slack HTTP 429 rate limits with backoff.
- [ ] Handled event deduplication using `event_id` / `client_msg_id`.
- [ ] On AI agent failure, posted a friendly Slack thread message and logged structured diagnostics.

### 9. Relative Path & Citation Mandate (🔴 CODE RED)
- [ ] No absolute filesystem paths (`C:\...`, `/home/...`) or `file:///` URIs in any markdown, plan, or comment.
- [ ] All file paths in repository files are relative to the Git repository root.
- [ ] Architectural decisions and rules cite the relative spec file and section.

---

**Pass Criteria:** All applicable checks must be verified before submitting code or concluding tasks.
