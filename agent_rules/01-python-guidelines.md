# Python Coding Standards & Enforcement

> **File:** `agent_rules/01-python-guidelines.md`  
> **Source Specs:** `guidelines/02-spec/02-coding-guidelines/12-python/02-standards.md`, `guidelines/02-spec/02-coding-guidelines/01-cross-language/16-static-analysis/08-python-ruff.md`, `guidelines/02-spec/17-consolidated-guidelines/34-compiled-simple-coding-guidelines.md`  
> **Applies to:** All Python source files (`*.py`) in this repository.  

---

## 1. Environment & Target Version

- **Python Version:** 3.11+ (Target 3.12 recommended).
- **Future Annotations:** All Python files MUST begin with:
  ```python
  from __future__ import annotations
  ```
  *(Enforces PEP 563 postponed evaluation of annotations and clean type references).*

---

## 2. Formatting & Static Analysis Tools

We use **Ruff** for high-speed unified linting and formatting, and **Mypy** for strict type checking.

### 2.1 Standard Configuration (`pyproject.toml`)

```toml
[tool.ruff]
target-version = "py312"
line-length = 100

[tool.ruff.lint]
select = [
  "E",      # pycodestyle errors
  "W",      # pycodestyle warnings
  "F",      # pyflakes
  "I",      # isort (import ordering)
  "N",      # pep8-naming
  "UP",     # pyupgrade
  "S",      # flake8-bandit (security)
  "B",      # flake8-bugbear
  "C90",    # mccabe complexity
  "SIM",    # flake8-simplify
  "RET",    # flake8-return (no else after return)
  "PTH",    # flake8-use-pathlib
  "PLR",    # Pylint refactor
  "PLC",    # Pylint convention
  "PLE",    # Pylint error
  "FA",     # flake8-future-annotations
  "D",      # pydocstyle
]
ignore = [
  "D203",   # 1 blank line required before class docstring (conflicts with D211)
  "D213",   # Multi-line docstring summary should start at the second line (conflicts with D212)
]

[tool.ruff.lint.mccabe]
max-complexity = 10

[tool.ruff.lint.pylint]
max-args = 3
max-statements = 10

[tool.ruff.lint.per-file-ignores]
"tests/**/*.py" = ["S101", "PLR0913", "D100", "D103"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"

[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_any_explicit = true
disallow_any_generics = true
disallow_untyped_defs = true
check_untyped_defs = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
```

---

## 3. Strict Type Hinting

- **Total Type Coverage:** Every public and private function, method, and class attribute MUST be explicitly typed (parameters and return values).
- **Ban on `Any`:** The `Any` type is strictly forbidden in business logic, domain models, and service interfaces.
- **Modern Union Syntax:** Use `T | None` instead of `Optional[T]`, and `T1 | T2` instead of `Union[T1, T2]`.
- **Generics & TypeVar:** Use parameterized generics (e.g. `list[str]`, `dict[str, int]`, `Result[T]`) for container types.
- **Type Aliases:** Define explicit named type aliases rather than repeating complex inline types:
  ```python
  # ❌ FORBIDDEN: Complex inline type repeated at call sites
  def process_queue(tasks: dict[str, list[dict[str, str]]]) -> None: ...

  # ✅ REQUIRED: Concrete domain type alias
  type TaskPayload = dict[str, str]
  type TaskQueueMap = dict[str, list[TaskPayload]]

  def process_queue(tasks: TaskQueueMap) -> None: ...
  ```

---

## 4. Data Validation: Pydantic vs Dataclasses

- **System Boundaries (External APIs, Slack Events, Database, Config):**
  - **MUST use `pydantic.BaseModel`** for input validation, schema enforcement, and deserialization.
  - Enable strict validation and immutability where appropriate (`model_config = ConfigDict(frozen=True, extra="forbid")`).
- **Internal DTOs & Options Bags:**
  - Use `@dataclass(frozen=True)` or Pydantic models for internal parameters.
  - Never pass raw dictionaries (`dict[str, Any]`) across internal service boundaries.

```python
from dataclasses import dataclass
from pydantic import BaseModel, ConfigDict, Field

# ✅ System boundary: Slack Webhook Request Model
class SlackEventPayload(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)
    
    event_id: str = Field(..., alias="event_id")
    event_type: str = Field(..., alias="type")
    team_id: str = Field(..., alias="team_id")
    channel_id: str | None = None
    user_id: str | None = None
    text: str = ""

# ✅ Internal parameter bundle (Options Bag)
@dataclass(frozen=True)
class SendMessageParams:
    channel_id: str
    message_text: str
    thread_ts: str | None = None
```

---

## 5. Function & File Size Limits

| Dimension | Rule | Action if Exceeded |
|---|---|---|
| **Function Body** | Maximum **15 lines** (target 8–10 lines) | Extract helper methods or decompose logic. *(Error-handling lines exempt)* |
| **Function Arguments** | Maximum **3 parameters** | Group 4+ parameters into a typed dataclass / Pydantic object. |
| **File Size** | Maximum **300 lines** (hard ceiling 400 lines) | Split into `_helpers.py`, `_types.py`, or separate service modules. |
| **Class / Struct** | Maximum **120 lines** | Decompose with composition and focused responsibility. |
| **Cognitive Complexity** | Maximum **10** (McCabe) | Flatten conditionals, extract functions, use early returns. |

---

## 6. Python-Specific Best Practices & Prohibitions

### 6.1 Modern Path Handling (`pathlib`)
```python
# ❌ FORBIDDEN: os.path
import os
file_path = os.path.join(base_dir, "config.json")
exists = os.path.exists(file_path)

# ✅ REQUIRED: pathlib.Path
from pathlib import Path
file_path = Path(base_dir) / "config.json"
is_existing = file_path.is_file()
```

### 6.2 String Formatting
```python
# ❌ FORBIDDEN: %-formatting or .format()
msg = "User %s joined channel %s" % (user_id, channel_id)
msg = "User {} joined channel {}".format(user_id, channel_id)

# ✅ REQUIRED: f-strings
msg = f"User {user_id} joined channel {channel_id}"
```

### 6.3 Mutable Default Arguments
```python
# ❌ FORBIDDEN (B006): Mutable defaults cause shared state bugs
def add_listener(listeners: list[str] = []) -> None: ...

# ✅ REQUIRED: None default + immutable initialization
def add_listener(listeners: list[str] | None = None) -> None:
    active_listeners = list(listeners) if listeners is not None else []
```

### 6.4 None Comparisons
```python
# ❌ FORBIDDEN (E711): Equality comparison with None
if value == None: ...
if value != None: ...

# ✅ REQUIRED: Identity comparison
if value is None: ...
if value is not None: ...
```

### 6.5 Security Prohibitions
- **No `assert` in Production:** `assert` statements are stripped when Python runs with optimization (`-O`). Use explicit guard clauses and domain exceptions.
- **No `eval()` or `exec()`:** Dynamic code execution is strictly prohibited due to severe code injection vulnerabilities.
- **No Hardcoded Secrets:** Tokens (Slack Bot Token, Signing Secret, LLM API keys) must be loaded from secure environment variables or secret vaults.

### 6.6 Import Organization
Imports must be structured in 4 distinct groups, separated by a single blank line:
1. Standard library imports (e.g. `asyncio`, `pathlib`, `typing`)
2. Third-party package imports (e.g. `slack_sdk`, `pydantic`, `httpx`)
3. First-party absolute project imports (e.g. `from src.services.llm import LLMService`)
4. First-party relative imports (e.g. `from .types import MessageResult`)

*Wildcard imports (`from module import *`) are strictly banned (F403).*

---

## 7. Asynchronous Execution Standards

- **Parallel Execution for Independent Async Tasks:**
  Whenever two or more async operations do not depend on each other's output, they **MUST be executed concurrently using `asyncio.gather()`**. Sequential `await` on independent tasks is a **CODE RED** violation.

```python
# ❌ CODE RED: Sequential await on independent operations
async def fetch_slack_context(client: AsyncWebClient, user_id: str, channel_id: str) -> SlackContext:
    user_info = await client.users_info(user=user_id)
    channel_info = await client.conversations_info(channel=channel_id)
    return build_context(user_info, channel_info)

# ✅ REQUIRED: Parallel execution via asyncio.gather
async def fetch_slack_context(client: AsyncWebClient, user_id: str, channel_id: str) -> SlackContext:
    user_task = client.users_info(user=user_id)
    channel_task = client.conversations_info(channel=channel_id)
    
    user_info, channel_info = await asyncio.gather(user_task, channel_task)
    
    return build_context(user_info, channel_info)
```

- **Async Resource Cleanup:**
  Always use `async with` context managers for clients, connections, or sessions (`httpx.AsyncClient`, file locks, database connections).
