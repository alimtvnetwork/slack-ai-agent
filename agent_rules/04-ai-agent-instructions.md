# AI Agent Operating Instructions & Protocols

> **File:** `agent_rules/04-ai-agent-instructions.md`  
> **Source Specs:** `guidelines/02-spec/02-coding-guidelines/06-ai-optimization/`, `guidelines/02-spec/17-consolidated-guidelines/35-ai-code-review-guide.md`, `guidelines/02-spec/21-app/readme.md`  
> **Target Audience:** AI Coding Assistants & Automated Pair Programmers working on this project.  

---

## 1. Anti-Hallucination Framework (AH Rules)

An AI agent "hallucinates" when it invents non-existent APIs, imagines database columns or schemas, calls deprecated third-party functions, or creates files in arbitrary non-standard locations.

### 1.1 The "Read Before Write" Protocol (Mandatory)
Before generating or modifying any code:
1. **Locate & Read Definition Files:** Inspect the actual function signatures, database models, Slack SDK documentation, and configuration models.
2. **Never Assume Parameters:** Never guess library parameter names or response structures (e.g. Slack SDK `chat_postMessage` vs `conversations_history`). Check the actual installed SDK or type stubs.
3. **Verify Existing Types:** Check `agent_rules/` and existing schemas to ensure consistency with existing enums, models, and errors.

### 1.2 Self-Verification Loop
Immediately after creating or editing code, the agent must execute local static analysis:
```bash
# Linting & Style Check
ruff check .

# Format Verification
ruff format --check .

# Strict Type Checking
mypy . --strict
```
If errors are reported, the agent MUST resolve them before reporting completion to the user.

---

## 2. Strict Relative Path & Citation Mandate (CODE RED 🔴)

### 2.1 Total Ban on Absolute Paths in Repository Files
- **NEVER** write absolute filesystem paths (e.g. `C:\Users\...`, `/home/...`, `/d:/...`) or `file:///` URI schemes inside markdown plans, subtask files, code comments, or committed repository files.
- **Portability Requirement:** Every file path and markdown link inside repository files **MUST be strictly relative to the Git repository root**.
  - ❌ **INVALID:** `[Config](file:///D:/others/Github/slack-agent/config.py)`
  - ❌ **INVALID:** `# Loaded from C:\projects\slack-agent\agent_rules\...`
  - ✅ **VALID:** `[Config](src/config.py)`
  - ✅ **VALID:** `# Per agent_rules/01-python-guidelines.md §3`

### 2.2 Mandatory Spec Citation
When an AI agent generates code, creates plans, creates subtasks, or explains design decisions, it **MUST cite the specific spec file and section** justifying the action using strictly relative paths.
- *Example:* `"Implementing early returns to enforce zero nesting, per agent_rules/02-general-coding-guidelines.md §4."`
- *Example:* `"Wrapping Slack API exception with AppError, per agent_rules/03-error-handling-architecture.md §2."`

---

## 3. Spec-First Authoring Protocol

Features and architectural changes follow a strict specification sequence:

```
User Request (Verbatim) ──▶ Spec Authoring ──▶ Task Breakdown ──▶ Implementation
```

1. **Lossless Verbatim Capture:**
   Every spec authored in `02-spec/21-app/` MUST include a dedicated `## User Request (Verbatim)` section preserving 100% of the user's prompt text, edge cases, and constraints without summarization or truncation.
2. **Pure Spec Isolation:**
   Spec creation focuses purely on requirements, data models, contracts, and architecture. No source code implementation occurs during the spec authoring turn.
3. **Decoupled Task Planning:**
   Actionable execution plans belong in `.ai-memory/plans/pending/xx-<slug>.md` and subtasks in `.ai-memory/plans/subtasks/xx-<slug>/`, citing the canonical spec.

---

## 4. Agent Memory Lifecycle & TTL

1. **State Transition:** When a planned task is completed, its entry in `.ai-memory/plans/pending/` must be moved to completed/done registers.
2. **Canonical Spec Authority:** The `guidelines/` and `agent_rules/` specifications ALWAYS supersede `.ai-memory/` memories. If an older memory contradicts a spec, the spec wins and the stale memory must be updated or purged.
3. **Dynamic Waiting (No Tight-Loop Polling):**
   When waiting for external processes, subagents, or background tasks, avoid rapid tight-loop polling. Rely on notification wakeups or dynamic sleep intervals (`-t <sec>`).

---

## 5. Slack Bot & LLM Agent Specific Directives

### 5.1 Secret Management
- **Never Hardcode Secrets:** Never commit or hardcode `SLACK_BOT_TOKEN`, `SLACK_APP_TOKEN`, `SLACK_SIGNING_SECRET`, or LLM API keys (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`).
- Always load configuration via Pydantic Settings (`pydantic-settings`) reading from environment variables or `.env`.

### 5.2 Slack Event Idempotency & De-duplication
- Slack automatically retries events if the bot doesn't acknowledge with HTTP 200 within 3 seconds.
- The bot MUST track processed `event_id` or `client_msg_id` values (in memory or SQLite with TTL) to prevent executing duplicate AI agent actions on the same user message.

### 5.3 Graceful Degradation & User Feedback
- If an LLM call fails, times out, or encounters a rate limit (HTTP 429), **never crash or leave the user hanging**.
- Post a friendly, polite fallback message directly into the Slack thread:
  > *"I encountered a temporary issue communicating with my AI brain. Please try asking again in a moment."*
- Log the full diagnostic `AppError` internally for developer triage.
