# Slack AI Assistant 🤖

Slack AI assistant equipped with autonomous web research, deep document and multi-sheet spreadsheet analysis, automatic data visualization charts uploaded to threads, and a Human-in-the-Loop document write gate.

Built with **LangGraph**, **Slack Bolt (Async)**, **Matplotlib**, and **OpenRouter**.

---

## 🚀 How to Run

### 1. One-Command Launch (Zero Manual Setup)

On any Windows machine, open PowerShell in the project directory and run:

```powershell
.\run.ps1
```

> **Note:** If script execution is restricted on a brand new machine, run:  
> `powershell -ExecutionPolicy Bypass -File .\run.ps1`

#### What `run.ps1` handles automatically:
* **First Run (New Machine / Fresh Clone):**
  1. Installs `uv` (Astral's high-speed package manager) if not present.
  2. Downloads and configures the standalone Python 3.12 runtime via `uv`.
  3. Creates required storage directories (`data/`, `data/charts/`).
  4. Creates `.env` from `.env.example` if missing.
  5. Synchronizes all virtual environment dependencies from `uv.lock` in seconds.
  6. Prompts for credentials if `.env` is unconfigured, then launches the bot.
* **Subsequent Runs:**
  * Instantly detects that the environment is ready (<5ms) and launches the bot immediately with **zero delay**.

---

### 2. Environment Configuration (`.env`)

Before the bot can connect to Slack and OpenRouter, set your credentials in `.env`:

```env
# ==============================================================================
# Slack App Credentials (from https://api.slack.com/apps)
# ==============================================================================
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_APP_TOKEN=xapp-your-slack-app-level-token
SLACK_SIGNING_SECRET=your-slack-signing-secret

# ==============================================================================
# OpenRouter / LLM Credentials (from https://openrouter.ai/keys)
# ==============================================================================
OPENROUTER_API_KEY=sk-or-v1-your-openrouter-key
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# ==============================================================================
# Operational Settings
# ==============================================================================
AGENT_NAME=AIAssistant
PROPOSAL_TTL_SECONDS=1800
MAX_FILE_SIZE_BYTES=10485760
LOG_LEVEL=INFO
```

---



### 4. Manual Run (Alternative)

If you prefer using `uv` directly from your command line:

```powershell
# 1. Install dependencies
uv sync

# 2. Run the bot
uv run python main.py
```

---

## 🧠 System Capabilities

### 1. 🧠 Multi-Turn Conversational Memory & State
* **Thread-Isolated Memory:** Every Slack thread maintains its own isolated conversation history keyed strictly by composite identifier `channel_id:thread_ts`. Conversations in different threads or channels never bleed into each other.
* **Persistent SQLite Storage:** Powered by LangGraph's `AsyncSqliteSaver` (`data/checkpoints.sqlite`). Conversation memory survives bot restarts and process reloads.
* **In-Memory Fallback:** Seamlessly supports ephemeral in-memory checkpointing for automated testing and CI/CD pipelines.

---

### 2. ⚡ Zero-Token Fast-Path System Commands
*Commands are intercepted at pipeline entry and resolved immediately without consuming LLM tokens:*
* **`@bot help` (or `/help`, `commands`):** Renders an interactive Slack Block Kit cheat sheet summarizing all capabilities and commands.
* **`@bot status` (or `/status`, `info`):** Displays a live diagnostic card detailing:
  * Number of messages currently stored in the active thread's memory.
  * Active LLM model name (e.g. `anthropic/claude-3.5-sonnet`).
  * Checkpointer backend (`SQLite (Persistent)` vs. `In-Memory`).
  * Count of pending document proposals awaiting review.
* **`@bot reset` (or `@bot clear`, `/reset`):** Instantly purges SQLite checkpoints for that specific thread so you can start a fresh conversation.

> **Tip:** In direct messages (DMs), you can simply type `help`, `status`, or `reset` without any `@` mention.

---

### 3. 📄 Document & Multi-Sheet File Ingestion
*When files are attached in Slack, the bot downloads, parses, and injects their extracted contents above the prompt:*
* **PDFs (`.pdf`):** Extracts text across multi-page documents via `pypdf`.
* **Word Documents (`.docx`):** Parses headings, structural paragraphs, and tabular cells via `python-docx`.
* **Excel Spreadsheets (`.xlsx` / `.xls`):** Explores all sheets in multi-sheet workbooks, cross-references cell grids, and analyzes tabular data relationships via `openpyxl`.
* **CSVs (`.csv`):** Parses comma-separated records and data tables.
* **Source Code & Text Files (`.py`, `.json`, `.txt`, `.md`):** Ingests raw code snippets and configuration files for code review and debugging.

---

### 4. 🌐 Autonomous Web Research & Direct Page Ingestion
* **Live Web Search (`web_search`):** Powered by DuckDuckGo search with automatic query sanitization, operator stripping fallback (handles malformed `site:` filters), and breaking news fallback.
* **Direct Web Page Reading (`fetch_web_page`):** When given an HTTP/HTTPS URL, fetches the webpage directly, strips scripts/styles/boilerplate, and extracts readable article text.
* **Clickable Slack Citations:** Formats all web citations as native Slack links (`<URL|Page Title or Domain>`) and appends a structured `📚 *Sources:*` section at the end of responses.

---

### 5. 📊 Data Visualization & Slack Auto-Upload
* **Chart Generator Tool (`generate_chart`):** Renders high-resolution visualizations using headless Matplotlib:
  * **Bar charts:** Categorical comparisons, rankings, and discrete metrics.
  * **Line charts:** Time-series trends, timelines, and continuous tracking.
  * **Pie charts:** Budget allocations, market shares, and proportional breakdowns.
* **Automatic Thread Upload:** Generated PNG charts are automatically uploaded directly to the Slack conversation thread using `files.upload_v2` with a formatted caption (e.g. `📊 *Quarterly Revenue Growth*`).

---

### 6. ✍️ Human-in-the-Loop Document Write Gate
*The bot is strictly prohibited from generating files in secret. Every document requires human sign-off:*
* **Two-Phase Proposal Flow:** The bot calls `propose_file_write` to register a proposed document in the store with an executive summary and full preview.
* **Interactive Approval Card:** Renders a Block Kit card with 3 action buttons:
  * **`[Approve & Write]`:** Compiles the content into a downloadable file (PDF via `reportlab` or Word `.docx`) and uploads it to the thread.
  * **`[✏️ Edit / Refine]`:** Opens a Slack Modal dialog allowing you to change the filename, switch format (e.g. PDF to DOCX), or modify the document content before generating.
  * **`[Reject]`:** Immediately cancels and discards the proposal.
* **TTL Expiration:** Unapproved proposals automatically expire after 30 minutes to maintain memory hygiene.

---

### 7. ⏱️ Smooth Thread UX & Infrastructure Controls
* **In-Place Message Updates (Reply Count = 1):**
  1. Posts `⏳ _Thinking..._` as the initial thread reply.
  2. Updates in real-time as tools run (e.g. `🔍 Searching the web...`, `📊 Analyzing attached file(s)...`).
  3. Updates that exact message in-place with the final answer or proposal card. *(Eliminates deleted messages and keeps the reply count clean).*
* **Sub-3s Acknowledgment:** Complies with Slack Bolt's `<3s` acknowledgment SLA before launching async processing.
* **Deduplication Middleware:** Prevents duplicate runs if Slack resends an event during network latency.
* **Loopback Filtering:** Automatically ignores messages sent by the bot itself to prevent infinite loops.

---

## 💬 Sample Prompts to Try in Slack

* **Web Research:**
  > `@bot What are the latest developments in quantum computing this week?`
* **Direct URL Reading:**
  > `@bot Can you summarize this article: https://example.com/blog/ai-trends`
* **Spreadsheet Analysis & Charting:**
  > *(Attach `regional_sales_sample.xlsx`)*  
  > `@bot analyze this spreadsheet and generate a bar chart comparing total annual sales by region`
* **Pie Chart Request:**
  > `@bot create a pie chart of our department expense breakdown: Engineering 45%, Marketing 25%, Operations 20%, Legal 10%`
* **Document Drafting (Write Gate):**
  > `@bot draft a formal project charter for our Q4 security audit as a PDF report`
* **Thread Diagnostics:**
  > `@bot status`
* **Reset Memory:**
  > `@bot reset`