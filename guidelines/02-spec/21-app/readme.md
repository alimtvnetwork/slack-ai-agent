# App

> **/goal** Master and enforce the architectural standards, specifications, and CI/CD validation rules for 21 App.
> **/learn** Read the sequentially ordered specification files in this directory, follow the actionable CI/CD checklist, and apply mandatory rules before generating code.

## 🎯 Actionable CI/CD & Agent Checklist

- [ ] `/goal` Read and understand all numbered specifications under `21-app/`.
- [ ] `/learn` Adhere strictly to `.ai-memory/folder-structure.md` and `.ai-memory/strictly-avoid.md`.
- [ ] `/goal` Verify zero explicit `true` boolean evaluations and no mixed-polarity conditionals.
- [ ] `/learn` Run all local verification linters via `python 03-ai-scripts/06-cicd-local-runner.py`.

. **CRITICAL AI INSTRUCTION:** This `readme.md` file is the primary entry point for this directory. AI agents MUST read this file first before exploring other files in this folder.

**Version:** 3.2.0
**Updated:** 2026-04-16
**AI Confidence:** Production-Ready
**Ambiguity:** None

---

## Overview

App-specific specification content at the root spec level. This folder contains implementation specs, feature definitions, workflows, and architecture decisions for whatever project this repo ships — web app, Chrome extension, browser plugin, CLI tool, mobile app, WordPress plugin, desktop app, or any other deliverable.

Whatever the app is, **its product-level documentation lives here.** Foundational, cross-cutting guidelines (naming, error handling, design tokens, CI/CD, etc.) belong in the core fundamentals range (`01–20`).

---

## Placement Rule

Any content that defines a specific application feature, workflow, screen, command, or implementation detail belongs here, regardless of the app's runtime (browser, Node, PHP, Go, native, extension manifest, etc.). Foundational, reusable principles belong in the core fundamentals range (`01–20`).

Sibling folders for app-scoped concerns:

- `22-app-issues/` — bug reports and root-cause analyses for this app
- `23-app-db/` — database schema and queries for this app
- `24-app-ui-design-system/` — UI components and design tokens for this app

---

## Specification Authoring Standards for AI Prompts & Agents

All specification writing prompts (e.g. `02-plan-spec-steps-v2.md`) and parent execution prompts (e.g. `06-execute-parent-task-with-n-steps-v2.md`) MUST author product specifications directly inside this folder (`02-spec/21-app/`):

1. **Pure Spec Authoring Isolation:** Spec creation must focus strictly on architecture, contracts, and requirements. No source code implementation or build execution occurs during the spec phase.
2. **Authoring Structure Patterns:**
   - **Focused Feature (Single File):** `02-spec/21-app/xx-<feature-slug>.md` (e.g. `02-spec/21-app/02-auth-session-management.md`).
   - **Complex Feature (Segmented Subfolder):** `02-spec/21-app/xx-<feature-slug>/` for multi-module features exceeding 3 subtasks or involving UI, database, and backend contracts:
     - `01-overview.md` — Architectural context, domain logic, and `## User Request (Verbatim)`.
     - `02-data-contracts.md` — Types, schemas, API request/response structures, and database models.
     - `03-workflow-and-state.md` — Control flows, state machine transitions, and business validation rules.
     - `04-ui-ux-spec.md` — Visual layout, typography, design tokens, and embedded relative screenshot links (`assets/screenshots/...`).
     - `05-acceptance-criteria.md` — Testable verification rules and quality gates.
3. **Lossless Verbatim Capture:** Every spec authored MUST contain a dedicated `## User Request (Verbatim)` section preserving 100% of the user's prompt text, edge cases, and constraints without summarization or truncation.
4. **Decoupled Task Planning (`.ai-memory/plans/`):** Actionable execution plans and lean subtasks are placed in `.ai-memory/plans/pending/xx-<slug>.md` and `.ai-memory/plans/subtasks/xx-<slug>/`, and MUST explicitly reference the canonical specification files here (`02-spec/21-app/...`).
5. **Registry Update:** Every newly authored specification in `21-app/` must be registered below in the `## Contents` table.

---

## Contents

| File / Folder | Title | Type | Status |
|:---|:---|:---|:---|
| [`readme.md`](readme.md) | App Specifications Root Index & Standards | Standard Index | Active |
| [`02-prompts-v1-v2-and-gitmap-benchmarks.md`](02-prompts-v1-v2-and-gitmap-benchmarks.md) | AI Prompts V1/V2 Architecture & GitMap Discovery Benchmarks | Application Spec | Active |
| [`03-multi-repo-prompts-skills-sync-audit.md`](03-multi-repo-prompts-skills-sync-audit.md) | Multi-Repository Prompts V1/V2 & Skills Synchronization Audit | Application Spec | Active |
| [`60-multi-repo-prompts-skills-sync-audit.md`](60-multi-repo-prompts-skills-sync-audit.md) | Multi-Repository Prompts V1/V2 & Skills Synchronization Audit (Canonical) | Application Spec | Active |
| [`05-design-system-and-slide-engine.md`](05-design-system-and-slide-engine.md) | Design System, CSS3 Building Blocks & Slide Presentation Engine | Application Spec | Active |
| [`06-ai-adaptable-design-system.md`](06-ai-adaptable-design-system.md) | AI-Adaptable Design System & Modern SaaS UI Architecture | Application Spec | Active |
| [`12-modern-design-system-and-themes.md`](12-modern-design-system-and-themes.md) | Modern Design System, Theme Architecture & AI Training Guide | Application Spec | Active |

---

## Cross-References

| Reference | Location |
|-----------|----------|
| App Issues | [../22-app-issues/readme.md](../22-app-issues/readme.md) |
| Spec Authoring Guide | [../01-spec-authoring-guide/readme.md](../01-spec-authoring-guide/readme.md) |

---

## Verification

_Auto-generated section — see `02-spec/21-app/97-acceptance-criteria.md` for the full criteria index._

### AC-APP-001: App-level conformance: Index

**Given** Run the application's integration smoke suite.
**When** Run the verification command shown below.
**Then** Boot sequence completes; health endpoint returns 200; no unhandled promise rejections appear in the log.

**Verification command:**

```bash
npm run test
```

**Expected:** exit 0. Any non-zero exit is a hard fail and blocks merge.

_Verification section last updated: 2026-08-30_
