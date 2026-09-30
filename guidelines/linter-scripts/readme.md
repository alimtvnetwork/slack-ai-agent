# Linter Scripts Catalog & CI/CD Cross-Platform Architecture

`linter-scripts/` contains the internal quality-gate linters and validators for the coding guidelines meta-repository.

---

## 🎯 Architectural Principles

1. **Pure Cross-Platform Python (No Shell Scripts):**
   - All linters in this directory MUST be implemented in pure Python 3 (`.py`) or Node.js (`.mjs`).
   - Legacy `.sh` shell scripts are strictly prohibited to ensure 100% identical validation behavior across Windows (`pwsh`), Linux (`bash`), and macOS (`zsh`).
2. **Deterministic Exit Codes:**
   - Exit `0`: All rules satisfied / Clean pass.
   - Exit `1`: Policy violation / Failing check.
3. **Integration with Shared AI Toolchain:**
   - Internal linters leverage the centralized cache, file-locking primitives, and compiled regular expressions in `03-ai-scripts/02-shared-engine.py`.
   - All quality gates are enqueued and executed concurrently via `03-ai-scripts/06-cicd-local-runner.py`.

---

## 📋 Internal Linters Directory

| Script | Language | Purpose & Scope | CI Automated |
|---|---|---|---|
| [`check-sequence-integrity.py`](check-sequence-integrity.py) | Python 3 | Verifies sequential numbering, broken file links, and prompt references across `01-prompts/`, `.ai-memory/plans/`, and `.agents/skills/`. | ✅ Yes |
| [`check-relative-paths.py`](check-relative-paths.py) | Python 3 | Enforces strict relative git paths and bans absolute filesystem paths / `file:///` URIs. | ✅ Yes |
| [`check-boolean-guidelines.py`](check-boolean-guidelines.py) | Python 3 | Audits codebase for boolean naming conventions (`is`, `has`), bans explicit `== true`, and detects inverted success checks. | ✅ Yes |
| [`check-enum-and-boolean.py`](check-enum-and-boolean.py) | Python 3 | Validates `Type` suffix on enum identifiers and enforces positive implicit guards. | ✅ Yes |
| [`check-error-management.py`](check-error-management.py) | Python 3 | Audits `AppError` wrapping, HTTP error models, and universal error envelopes across Go/TS/Python. | ✅ Yes |
| [`check-forbidden-strings.py`](check-forbidden-strings.py) | Python 3 | TOML-driven scanner (`forbidden-strings.toml`) enforcing renamed symbols and deprecated naming patterns. | ✅ Yes |
| [`check-forbidden-spec-paths.py`](check-forbidden-spec-paths.py) | Python 3 | Blocks deprecated or uppercase `.md` paths and ensures consolidated spec structure. | ✅ Yes |
| [`check-spec-folder-refs.py`](check-spec-folder-refs.py) | Python 3 | Validates folder-level references in specifications and guides against stale directory names. | ✅ Yes |
| [`check-spec-cross-links.py`](check-spec-cross-links.py) | Python 3 | Validates cross-specification markdown links using `spec-cross-links.allowlist`. | ✅ Yes |
| [`check-placeholder-comments.py`](check-placeholder-comments.py) | Python 3 | Blocks placeholder comments (`// TODO`, `/* fill here */`, `[N]`) across all specification files. | ✅ Yes |
| [`check-prompts-loaded.py`](check-prompts-loaded.py) | Python 3 | Ensures all prompt categories and canonical prompts are registered in prompt manifests. | ✅ Yes |
| [`check-readme-install-section.py`](check-readme-install-section.py) | Python 3 | Audits `readme.md` for consistent install instructions and valid curl/irm commands. | ✅ Yes |
| [`check-file-sizes.py`](check-file-sizes.py) | Python 3 | Tracks file size baseline (`.file-size-baseline.json`) to prevent uncontrolled document bloat. | ✅ Yes |
| [`check-newline-styling.py`](check-newline-styling.py) | Python 3 | Validates single blank line spacing between top-level declarations and trailing newline conventions. | ✅ Yes |
| [`check-newline-styling.mjs`](check-newline-styling.mjs) | Node.js | Fast AST/regex verification of newline styling. | ✅ Yes |
| [`check-axios-version.py`](check-axios-version.py) | Python 3 | Validates approved Axios dependency versions in `package.json`. | ✅ Yes |
| [`check-runner-dispatch-antipatterns.py`](check-runner-dispatch-antipatterns.py) | Python 3 | Audits installer runner scripts for platform-specific anti-patterns. | ✅ Yes |
| [`validate-guidelines.py`](validate-guidelines.py) | Python 3 | General coding guidelines validator across multi-language source trees. | ✅ Yes |

---

## 🚀 Local Execution

Run all internal linters concurrently:
```bash
python 03-ai-scripts/06-cicd-local-runner.py
```

Run a specific linter individually:
```bash
python linter-scripts/check-sequence-integrity.py
python linter-scripts/check-relative-paths.py
python linter-scripts/check-forbidden-strings.py
```
