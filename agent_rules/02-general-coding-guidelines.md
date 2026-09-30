# General Coding Guidelines & Architecture Rules

> **File:** `agent_rules/02-general-coding-guidelines.md`  
> **Source Specs:** `guidelines/02-spec/02-coding-guidelines/01-cross-language/`, `guidelines/02-spec/17-consolidated-guidelines/34-compiled-simple-coding-guidelines.md`, `guidelines/02-spec/17-consolidated-guidelines/03-strictly-avoid-quickref.md`  
> **Applies to:** All source code and project configurations across the repository.  

---

## 1. Rule Zero: Repository Protection (Non-Negotiable)

**NEVER commit generated code, build artifacts, test outputs, or cache files to Git.**

- Prohibited items: `__pycache__/`, `*.pyc`, `*.pyo`, `.venv/`, `.pytest_cache/`, `test-results/`, `coverage/`, `*.log`, `*.generated.*`, compiled binaries (`.exe`, `.so`, `.dll`), temporary SQLite database files.
- The `.gitignore` file must proactively exclude all such patterns.
- Auto-generated or runtime artifacts must be produced ephemerally or in CI/CD, never checked into version control.

---

## 2. Naming Standards

### 2.1 Acronym & Abbreviation Casing
Abbreviations and acronyms are treated as regular words—**only the first letter is capitalized**.
- ❌ **FORBIDDEN:** `ID`, `URL`, `API`, `JSON`, `HTTP`, `HTML`, `SQL`, `DB`, `UUID`
- ✅ **REQUIRED:** `Id`, `Url`, `Api`, `Json`, `Http`, `Html`, `Sql`, `Db`, `Uuid`

*Examples:* `user_id`, `UserId`, `api_client`, `ApiClient`, `base_url`, `BaseUrl`.

### 2.2 Identifier Casing Matrix

| Element | Casing Style | Examples | Notes |
|---|---|---|---|
| **Classes / Types / Models** | `PascalCase` | `SlackEventDispatcher`, `UserProfile` | Clear, descriptive nouns |
| **Enums** | `PascalCase` + `Type` suffix | `MessageType`, `AgentStatusType` | Never omit `Type` suffix |
| **Enum Members** | `PascalCase` | `MessageActionType.SendNotification` | Fallback / 0-value: `Invalid` |
| **Functions & Methods** | `snake_case` | `handle_message()`, `verify_signature()` | Verb-noun phrases |
| **Variables & Attributes** | `snake_case` | `user_id`, `slack_client` | No single-letter names outside loops |
| **Constants** | `UPPER_SNAKE_CASE` | `MAX_RETRY_ATTEMPTS`, `DEFAULT_TIMEOUT` | Declared at module level |
| **JSON / API Keys** | `PascalCase` | `"UserId"`, `"CreatedAt"`, `"ChannelId"` | Universal wire contract |
| **Database Tables / Columns** | `PascalCase` | `Tables: SlackUsers`, `Cols: TeamId, CreatedAt` | SQLite / Relational convention |

---

## 3. Boolean Principles (Positive Logic Standard)

Boolean logic must be readable, unambiguous, and strictly positive.

### 3.1 Mandatory Prefixes (`is_` / `has_`)
Every boolean variable, model field, function, or parameter **MUST start with `is_` or `has_`** (99% of cases). `should_` is reserved exclusively for recommendations/preferences.
- ❌ **BANNED:** `active`, `ready`, `admin`, `valid`, `can_edit`, `was_sent`, `will_retry`, `did_process`
- ✅ **REQUIRED:** `is_active`, `is_ready`, `is_admin`, `is_valid`, `has_permission`, `has_sent`

### 3.2 Positive Framing (No Negative Identifiers)
Never use negative words (`not`, `no`, `non`, `disable`) in boolean names. Invert the logic to an approved positive synonym.
- ❌ **BANNED:** `is_not_ready`, `has_no_token`, `is_invalid`, `disable_cache`
- ✅ **REQUIRED:** `is_pending`, `is_token_missing`, `is_invalid` (as a semantic status), `is_cache_enabled`

### 3.3 Semantic Inverse Functions
Never use the raw negation operator (`not`) on function calls. Use semantic inverse methods.
- ❌ **FORBIDDEN:** `if not payload.is_valid(): ...`
- ✅ **REQUIRED:** `if payload.is_invalid(): ...`

### 3.4 No Explicit Boolean Comparisons
Never compare directly to `True` or `False`. Positive booleans must be evaluated implicitly.
- ❌ **FORBIDDEN:** `if is_verified == True: ...` or `if is_admin is True: ...`
- ✅ **REQUIRED:** `if is_verified: ...`

### 3.5 No Boolean Flag Parameters
Functions must never accept boolean parameters that branch execution logic. Split into two explicit methods.
- ❌ **FORBIDDEN:** `def post_message(text: str, is_ephemeral: bool) -> None:`
- ✅ **REQUIRED:**
  - `def post_channel_message(text: str) -> None:`
  - `def post_ephemeral_message(text: str, user_id: str) -> None:`

### 3.6 Condition Complexity Cap
- Maximum of **2 conditions** per `if` statement.
- **NEVER mix `and` with `or`** in a single `if` expression.
- When 3+ conditions are present, extract them into well-named boolean variables before the `if`.

```python
# ❌ FORBIDDEN: Mixed logic, hard to parse, high cognitive load
if (user.is_active and user.has_license or user.is_admin) and not team.is_locked:
    ...

# ✅ REQUIRED: Decomposed into named booleans
has_user_access = user.is_active and user.has_license
is_privileged_user = user.is_admin or has_user_access
is_team_accessible = team.is_unlocked

if is_privileged_user and is_team_accessible:
    ...
```

---

## 4. Control Flow: Zero Nested `if` (Absolute Rule)

**Zero nested `if` statements are permitted.** Flatten execution using guard clauses and early exits.

```python
# ❌ CODE RED: Nested conditionals
def handle_event(event: SlackEvent) -> None:
    if event.is_message:
        if event.channel_id:
            if not event.is_bot:
                process_user_message(event)

# ✅ REQUIRED: Early return / Guard clause pattern
def handle_event(event: SlackEvent) -> None:
    if event.is_non_message:
        return

    if event.is_channel_missing:
        return

    if event.is_bot:
        return

    process_user_message(event)
```

- **No `else` after `return` / `raise` / `break` / `continue`:** The statement following an early exit block is implicitly the alternative path.

---

## 5. Line Gaps & Whitespace Conventions

1. **Blank line before `return` / `raise`:** Place exactly one blank line before `return` or `raise` when preceded by other statements. *(Single-line bodies are exempt).*
2. **No blank line at start of block:** The first line of code inside a function or class must immediately follow the declaration / docstring without an empty line.
3. **No double blank lines:** Never use two consecutive blank lines inside functions, classes, or between methods.
4. **Blank line after blocks:** Exactly one blank line after a closing block (`if`, `for`, `try/except`) when followed by further code.
5. **Top-level spacing:** Exactly two blank lines between top-level classes or functions (PEP-8 standard).

```python
# ✅ Correct whitespace pattern
def compute_rate_limit(user_id: str) -> int:
    current_tier = get_user_tier(user_id)
    base_quota = current_tier.quota_per_minute

    if current_tier.is_premium:
        return base_quota * 2

    return base_quota
```

---

## 6. Immutability & Mutation Avoidance

- **Assign Once:** Variables should be assigned at declaration and treated as immutable. Avoid reassigning variables across branching logic.
- **Frozen Models:** Use `@dataclass(frozen=True)` or Pydantic `frozen=True` for internal transfer types.
- **Pure Transformations:** Create new instances using model copy/spread (`model.model_copy(update={...})`) rather than mutating object properties in place.

---

## 7. Caching Directives (CODE RED 🔴)

1. **Never Cache Errors as Success:** Never store empty arrays, default fallbacks, or nulls in cache upon catching an error. If an operation fails, invalidate or delete the cache key.
2. **Mandatory TTL:** Every cache entry MUST have an explicit Time-To-Live (TTL). Unbounded in-memory caches cause memory leaks and stale data.
3. **Deterministic Keys:** Cache keys must be composed from stable, predictable identifiers (e.g. `f"slack:user:{team_id}:{user_id}"`). Never include timestamps, random numbers, or unformatted objects in cache keys.
4. **Invalidate on Mutation:** Any create, update, or delete operation must immediately invalidate or update the corresponding cache entry.

---

## 8. Single Source of Truth: Versioning

- The project version is defined **exclusively in `version.json`** located at the repository root.
- Python code must import or read `version.json` to expose `__version__`.
- Never hardcode duplicate version strings in Python files.
