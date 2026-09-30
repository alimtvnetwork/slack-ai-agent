# Slack AI Agent: System Specification & Technical Blueprint

> **System:** Enterprise Slack AI Assistant (File Ingestion, Web Search, Mandatory Write Approval)  
> **Status:** Specification Phase (Implementation on user signal)  
> **Package Manager:** `uv`  
> **Frameworks:** LangGraph, OpenRouter, Slack Socket Mode (`slack_bolt`), ReportLab, `pypdf`, `python-docx`  
> **Coding Standard:** Strict adherence to `agent_rules/`  

---

## ## User Request (Verbatim)

```text
this is the requirements of the slack bot
first make a spec folder and create spec
dont write 1 long spce

the spce should be divided in to task subtask

we will use uv instead of pip

also you need add slcak configuation instrunction in the spec folder with a spearte file 

after spec creation will go for implementation(do not start immediately, i will start)

--- From Attached Requirements PDF: "System Requirements & Technical Blueprint (Updated)" ---
Slack AI Agent: File Ingestion & Analysis, Web Search, and Mandatory Write Approval

1. System Architecture & Objectives
This system specifies an enterprise Slack AI assistant built on LangGraph, OpenRouter, and Slack Socket Mode. The bot
natively supports File Reading & Analysis (PDF, DOCX, Code, CSV), autonomous Web Search for external facts, and
implements a Strict Human-in-the-Loop Write Gate: the agent is prohibited from creating, modifying, or uploading any files or
documents without explicit interactive button approval in Slack.

2. Core Capabilities & Acceptance Criteria
- File Read & Analyze (pypdf, python-docx, requests): Extracts text from user-uploaded PDFs, DOCX, CSV, and code files in Slack channels or DMs and injects into LLM context for deep analysis.
- Web Search (DuckDuckGo Search tool): Autonomously triggers when external data, market facts, regulations, or recent news are required to complete an analysis.
- Mandatory Write Approval (Slack Block Kit + LangGraph tool): Any action generating a PDF, report, script, or document is routed to `propose_file_write`. Sends interactive [Approve] / [Reject] cards.
- File Generation & Upload (ReportLab & Slack files.upload_v2): Upon user approval, renders the verified content into a clean PDF, DOCX, or text file and uploads directly to the Slack conversation thread.
- Thread Memory (LangGraph Checkpointer): State is keyed by `channel_id:thread_ts` to ensure multi-turn context without cross-talk between different conversations.

3. Required Slack Scopes (api.slack.com)
• files:read - Required to download and parse user-uploaded PDFs and documents.
• files:write - Required to upload generated PDFs and approved documents to threads.
• chat:write - Posts conversational text and interactive Block Kit approval cards.
• app_mentions:read - Listens to bot @mentions in team channels.
• im:history, im:read, im:write - Supports 1-on-1 private DM threads.

4. End-to-End Execution Flow
1. File Upload & Prompt: User uploads a PDF/file with a prompt (e.g. 'Analyze this contract and search recent SEC compliance rulings').
2. Extraction & Ingestion: Slack webhook downloads bytes, extracts text via `pypdf`/`docx`, and prepends to prompt.
3. Reasoning & Web Search: LLM analyzes document text and invokes `web_search` to retrieve recent external regulations.
4. Write Proposal: If asked to produce a summary or revised document, agent calls `propose_file_write`.
5. Human Gate: Slack renders an interactive Block Kit preview card with [Approve & Write] and [Reject] buttons.
6. Execution: If approved, ReportLab builds the PDF and dispatches it via `files_upload_v2`. If rejected, cache is cleared.
```

---

## 🏛️ High-Level System Architecture

```
                    ┌───────────────────────────────────────────┐
                    │               Slack Client                │
                    │   (User Uploads File / Prompt / Mentions) │
                    └─────────────────────┬─────────────────────┘
                                          │ WebSocket (Socket Mode)
                                          ▼
                    ┌───────────────────────────────────────────┐
                    │          Slack Event Dispatcher           │
                    │   - Deduplication (event_id/client_msg_id) │
                    │   - Thread-aware routing                  │
                    └───────┬───────────────────────────┬───────┘
                            │                           │
                            │ User uploaded file        │ Interactive Button Click
                            ▼                           ▼
┌─────────────────────────────────────────┐   ┌─────────────────────────────────────────┐
│     File Ingestion & Parsing Engine     │   │      Block Kit Interactivity Router     │
│   - Auth Slack File Downloader          │   │   - [Approve & Write] ──▶ PDF Engine    │
│   - pypdf / python-docx / CSV / Code    │   │   - [Reject]          ──▶ Evict Proposal│
└───────────────────┬─────────────────────┘   └─────────────────────────────────────────┘
                    │ Extracted text payload
                    ▼
┌───────────────────────────────────────────────────────────────────────────────────────┐
│                     LangGraph Autonomous Agent Workflow Engine                        │
│                                                                                       │
│   State Key: `channel_id:thread_ts` via Thread Checkpointer                           │
│                                                                                       │
│   ┌────────────────────┐          LLM Call           ┌────────────────────────────┐   │
│   │ State Checkpointer │────────────────────────────▶│ OpenRouter LLM Gateway     │   │
│   └────────────────────┘                             └──────────────┬─────────────┘   │
│                                                                     │                 │
│                                            Tool Selection           │                 │
│                      ┌──────────────────────────────────────────────┴──────────────┐  │
│                      │                                                             │  │
│                      ▼                                                             ▼  │
│      ┌──────────────────────────────┐                       ┌──────────────────────────────┐
│      │ DuckDuckGo Search Tool       │                       │ `propose_file_write` Tool    │
│      │ (Autonomous Web Retrieval)   │                       │ (MANDATORY WRITE GATE)       │
│      └──────────────────────────────┘                       └──────────────┬───────────────┘
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┼──────────┘
                                                                             │ Emits Approval Card
                                                                             ▼
                                                              ┌─────────────────────────────┐
                                                              │ Slack Interactive Card Post │
                                                              │ [Approve & Write] [Reject]  │
                                                              └─────────────────────────────┘
```

---

## 📋 Modular Task & Subtask Index

All specifications are broken down into task and subtask modules:

| Task # | Directory | Focus Area |
|---|---|---|
| **Task 1** | [`tasks/task-1-project-setup-and-core-architecture/`](tasks/task-1-project-setup-and-core-architecture/01-task-overview.md) | Project initialization with `uv`, `pyproject.toml`, Ruff/Mypy configuration, structured `AppError` & `Result[T]` foundation, and `pydantic-settings`. |
| **Task 2** | [`tasks/task-2-slack-socket-mode-and-event-pipeline/`](tasks/task-2-slack-socket-mode-and-event-pipeline/01-task-overview.md) | Slack Socket Mode client (`AsyncApp`), event filtering, signature verification, event deduplication, and thread-aware routing. |
| **Task 3** | [`tasks/task-3-file-ingestion-and-text-extraction/`](tasks/task-3-file-ingestion-and-text-extraction/01-task-overview.md) | Authenticated Slack file download, multi-format text parsing (`pypdf`, `python-docx`, CSV, plain text/code), sanitization, and prompt prepending. |
| **Task 4** | [`tasks/task-4-langgraph-agent-and-tools/`](tasks/task-4-langgraph-agent-and-tools/01-task-overview.md) | LangGraph autonomous graph, OpenRouter client, DuckDuckGo search tool, thread-keyed state checkpointer (`channel_id:thread_ts`). |
| **Task 5** | [`tasks/task-5-human-in-the-loop-write-gate/`](tasks/task-5-human-in-the-loop-write-gate/01-task-overview.md) | Mandatory Write Gate: `propose_file_write` tool, Block Kit preview cards, and thread-scoped pending proposal storage with TTL. |
| **Task 6** | [`tasks/task-6-interactive-approval-handler-and-file-generation/`](tasks/task-6-interactive-approval-handler-and-file-generation/01-task-overview.md) | Block Kit action listeners, ReportLab PDF generation engine, DOCX/Text builders, Slack `files.upload_v2` dispatch, and proposal cleanup. |
| **Task 7** | [`tasks/task-7-testing-verification-and-ci/`](tasks/task-7-testing-verification-and-ci/01-task-overview.md) | Unit tests, mock Slack Socket Mode/event tests, mock OpenRouter tests, and verification pipeline using `uv run`. |

---

## ⚙️ Configuration Guide

A separate, comprehensive Slack configuration guide is available at:  
👉 [`slack-configuration.md`](slack-configuration.md) — includes required OAuth scopes, Socket Mode setup, App Manifest, and token management.
