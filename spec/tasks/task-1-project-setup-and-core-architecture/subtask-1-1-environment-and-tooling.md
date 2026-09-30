# Subtask 1.1: Environment Initialization & Tooling Setup with `uv`

> **Task Reference:** `TASK-01` > `SUBTASK-1.1`  
> **Source Rule:** `agent_rules/01-python-guidelines.md`  

---

## 1. Description

Initialize the Python project using `uv` (modern high-performance Python package and environment manager), specify project metadata in `pyproject.toml`, install all runtime and development dependencies, and configure Ruff and Mypy.

---

## 2. Requirements & UV Commands

### 2.1 Initialization
```bash
# Initialize uv project with package structure
uv init --name slack-agent

# Set target Python version to 3.12
uv python pin 3.12
```

### 2.2 Core Runtime Dependencies
Install production dependencies using `uv add`:
```bash
uv add \
  "slack-bolt>=1.20.0" \
  "slack-sdk>=3.31.0" \
  "langgraph>=0.2.20" \
  "langchain-core>=0.3.0" \
  "langchain-openai>=0.2.0" \
  "pydantic>=2.8.0" \
  "pydantic-settings>=2.4.0" \
  "httpx>=0.27.0" \
  "duckduckgo-search>=6.2.0" \
  "pypdf>=4.3.0" \
  "python-docx>=1.1.2" \
  "reportlab>=4.2.2" \
  "python-dotenv>=1.0.1"
```

### 2.3 Development & Verification Dependencies
```bash
uv add --dev \
  "ruff>=0.6.0" \
  "mypy>=1.11.0" \
  "pytest>=8.3.0" \
  "pytest-asyncio>=0.24.0" \
  "types-requests>=2.32.0" \
  "types-reportlab>=4.2.0"
```

---

## 3. Configuration in `pyproject.toml`

Ensure `pyproject.toml` contains:
- `target-version = "py312"`
- Line length = 100
- Ruff rule selection: `["E", "W", "F", "I", "N", "UP", "S", "B", "C90", "SIM", "RET", "PTH", "PLR", "PLC", "PLE", "FA", "D"]`
- Mypy `strict = true`, `disallow_any_explicit = true`, `disallow_untyped_defs = true`

---

## 4. Verification

```bash
uv run python -c "import slack_bolt, langgraph, pypdf, reportlab; print('All core libraries imported successfully')"
uv run ruff check .
uv run mypy . --strict
```
