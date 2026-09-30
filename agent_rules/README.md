# Agent Rules & Architecture Reference

> **Repository:** Slack Bot AI Agent  
> **Authority Level:** Mandatory / Non-Negotiable  
> **Source Base:** Consolidated from `guidelines/` specifications  
> **Status:** Active & Production-Ready  

---

## 📌 Executive Summary

This directory contains the canonical coding, architectural, error handling, and behavioral guidelines for developing the Python-based Slack Bot AI Agent. Every file here is derived from the comprehensive specifications in `guidelines/` and adapted specifically for Python, modern asynchronous AI agent frameworks, and Slack bot architectures.

As an AI coding agent pair-programming on this project, **all rules in this directory must be strictly followed without exception.**

---

## 📂 Document Catalog

| # | Document | Scope & Focus |
|---|---|---|
| **01** | [`01-python-guidelines.md`](01-python-guidelines.md) | Python 3.11+ standards, strict typing (`mypy`), Ruff linter rules, Pydantic boundary validation, async concurrency (`asyncio.gather`), and size limits. |
| **02** | [`02-general-coding-guidelines.md`](02-general-coding-guidelines.md) | Universal coding principles: Rule 0 (no committed artifacts), naming standards, boolean positive framing, zero nested `if`, immutability, and caching. |
| **03** | [`03-error-handling-architecture.md`](03-error-handling-architecture.md) | 🔴 **#1 Priority**: Zero swallowed errors, structured `AppError`, `Result[T]` monad, Universal Response Envelope, and session-based logging. |
| **04** | [`04-ai-agent-instructions.md`](04-ai-agent-instructions.md) | AI agent behavioral protocols: Anti-hallucination rules, "Read Before Write", strict relative path requirement (CODE RED), spec-first workflow, and Slack/LLM safety. |
| **05** | [`05-anti-hallucination-checklist.md`](05-anti-hallucination-checklist.md) | Pre-output validation checklist. Every code block and plan must pass these checks prior to output. |

---

## ⚡ Core Non-Negotiable Directives

1. **🔴 Rule Zero — Repository Protection:** Never commit generated code (`*.generated.*`), test artifacts, reports, virtual environments (`.venv/`), or Python caches (`__pycache__/`, `*.pyc`). Always maintain `.gitignore`.
2. **🔴 Zero Swallowed Errors:** Never use bare `except:`, `except Exception: pass`, or ignore returned `Result` errors. All exceptions must be caught specifically, wrapped in structured domain errors (`AppError`), and logged with contextual metadata.
3. **🔴 Zero Nested `if`:** Flatten all nested conditions using early returns and guard clauses. Cyclomatic complexity must remain ≤ 10.
4. **🔴 Strict Boolean Framing:** Every boolean variable, function, and parameter must begin with `is_` or `has_` (99%), use positive framing (no negative words like `not`, `no`, `non`), and never be passed as raw boolean flags.
5. **🔴 Single Return Value & Strict Typing:** Functions return a single typed value or `Result[T]`. Zero use of `Any` in business logic. Maximum 3 parameters per function (bundle 4+ into a typed Pydantic or `@dataclass(frozen=True)` options object).
6. **🔴 Parallel Async for Independent Calls:** Never `await` independent coroutines sequentially. Use `asyncio.gather()` for concurrent operations (e.g. parallel Slack API calls, independent LLM queries).
7. **🔴 Total Ban on Absolute Paths in Repo Files:** Never write absolute paths (`C:\...`, `/home/...`, `file:///...`) inside repository markdown documents, code comments, or citations. All paths must be relative to the Git root.

---

## 🔄 Workflow for Development

```
1. Read Requirements & Existing Definitions (Schemas, APIs, SDKs)
                    │
                    ▼
2. Author Spec / Contract in `02-spec/21-app/` (Verbatim User Prompt Captured)
                    │
                    ▼
3. Validate Against `agent_rules/05-anti-hallucination-checklist.md`
                    │
                    ▼
4. Implement Code with Strict Typing, Result[T], and Zero Nesting
                    │
                    ▼
5. Run Linters & Verifications (`ruff check .`, `mypy . --strict`, tests)
```
