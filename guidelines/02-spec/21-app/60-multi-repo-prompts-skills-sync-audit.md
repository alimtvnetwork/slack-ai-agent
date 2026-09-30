# Canonical Specification: Multi-Repository Prompts V1/V2 & Skills Synchronization Audit

> **Document Version:** 1.2.0  
> **Status:** APPROVED & ACTIVE  
> **Target Scope:** Meta-Repository (`alimtvnetwork/coding-guidelines-v24`) & 16 Connected Repositories

---

## 1. Executive Summary & Architectural Mandate

This specification formalizes the enterprise-wide modernization, prompt segregation (V1/V2), GitMap AUM acceleration, and atomic multi-repository release ceremony across the meta-repository `coding-guidelines` and all 16 connected codebases in `d:/work`.

### 1.1 Core Architecture Principles

1. **Meta-Repository Skills First:** Modernize all skill definitions within `coding-guidelines/.agents/skills/` before touching child repositories.
2. **Prompts V1/V2 Segregation:**
   - `01-prompts/v1/`: Preserves classic prompts using the Python toolchain (`03-ai-scripts/`) as the primary execution engine.
   - `01-prompts/v2/`: Modernized prompts elevating **GitMap Native AUM** (`gitmap find`, `gitmap search`, `gitmap cat`, `gitmap release`, `gitmap pl-ai`, `gitmap cpf`, `gitmap cpb`, `gitmap cpr`, `gitmap pwsh`) as primary, retaining Python scripts as secondary fallbacks.
3. **Multi-Engine Benchmarks:** Live empirical performance comparison across GitMap, Ripgrep, Python, and PowerShell embedded in root `readme.md`, spec 21, and `gitmap/docs/benchmarks/`.
4. **Guaranteed Release Ceremony:** Every child repository executes `git pull`, backup branch creation (`backup/sync-prompts-v1-v2-*`), feature branch migration (`feat/sync-prompts-v1-v2-gitmap`), atomic commit, patch release bump, release tag (`vX.Y.Z`), and merge back to `main`.

---

## 2. User Request (Verbatim)

```text
is it done proerly??

For all the prompts we have first update skills for this repo first then others please

Can you please update all these prompts to these repositories and update these skills as well? Also, at the same time, I want you to change the Git map AUM functionality instead of the Python script. Okay? We can keep the Python script. What we will do is inside the prompts, we create V1, V2 folder. So current prompts will go as the V1 prompts. The next prompts will go inside the V2 prompts. So all copy and then modify. And what we do is we modify the, let's say, prompts, okay, and also the root README of the coding guideline. We mention the benchmark, okay? So we can run the benchmark for complex regex search, file searching, all these things using Git map. We will have a Git map example, PowerShell, Python, all three examples, and others if we have. And then we create the table, showcase this table. Also, we update this inside the Git map benchmarking as well. And then once we have it, we update the code bases. What do I mean by that? That means inside the code base, we have empty Gravity Manager. We have a spec builder. We have movie CLI, macro HK. We have Laravel automation, Lara publishing, Lara licensing. Okay? Git mapped. WP exam, WP Git log, WP HTML automate, WP link manager, WP onboarding. All these cases, I want this new format, new skills to be added. And make sure before you do that, you always pull, commit, and resolve the commit, and push it to the Git. And before you do these changes, I request you to always take a backup of the branch and always make a release and mention the backup, like what you're doing, how you're changing it. And then you make these changes, make a new branch, do these changes, make a new release on all of these packages. Is it understood? Do you understand my request? Is it clear?
```

---

## 3. Synchronized Repositories & Release Matrix (Verified 100% Pass)

| Repository | Path | Release Tag | V1 Prompts | V2 Prompts | Skills | Scripts | Working Tree | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `coding-guidelines` | `.` | `v6.46.1` | 148 | 148 | 57 | 41 | Clean (`main`) | Certified |
| `antigravity-manager` | `../antigravity-manager` | `v4.75.3` | 148 | 148 | 57 | 41 | Clean (`main`) | Certified |
| `spec-builder` | `../spec-builder` | `v3.19.2` | 148 | 148 | 57 | 41 | Clean (`main`) | Certified |
| `movie-cli` | `../movie-cli` | `v2.343.2` | 148 | 148 | 57 | 41 | Clean (`main`) | Certified |
| `macro-ahk` | `../macro-ahk` | `v6.101.2` | 148 | 148 | 57 | 41 | Clean (`main`) | Certified |
| `laravel-automation` | `../laravel-automation` | `v5.2.4` | 148 | 148 | 57 | 41 | Clean (`main`) | Certified |
| `lara-publishing` | `../lara-publishing` | `v5.2.4` | 148 | 148 | 57 | 41 | Clean (`main`) | Certified |
| `lara-licensing` | `../lara-licensing` | `v0.691.2` | 148 | 148 | 57 | 41 | Clean (`main`) | Certified |
| `gitmap` | `../gitmap` | `v6.344.3` | 148 | 148 | 57 | 41 | Clean (`main`) | Certified |
| `wp-exam` | `../wp-exam` | `v0.3.1` | 148 | 148 | 57 | 41 | Clean (`main`) | Certified |
| `wp-git-log` | `../wp-git-log` | `v4.2.2` | 148 | 148 | 57 | 41 | Clean (`main`) | Certified |
| `wp-html-automate` | `../wp-html-automate` | `v6.17.2` | 148 | 148 | 57 | 41 | Clean (`main`) | Certified |
| `wp-link-manager` | `../wp-link-manager` | `v0.2.2` | 148 | 148 | 57 | 41 | Clean (`main`) | Certified |
| `wp-onboarding` | `../wp-onboarding` | `v0.2.2` | 148 | 148 | 57 | 41 | Clean (`main`) | Certified |
| `cat-my` | `../cat-my` | `v4.112.2` | 148 | 148 | 57 | 41 | Clean (`main`) | Certified |
| `scripts-fixer` | `../scripts-fixer` | `v1.51.1` | 148 | 148 | 57 | 41 | Clean (`main`) | Certified |
| `gitlogger-new` | `../gitlogger-new` | `v1.1.1` | 148 | 148 | 57 | 41 | Clean (`main`) | Certified |

---

## 4. Verification Protocol

The multi-repository audit script `03-ai-scripts/41-audit-all-repos.py` verifies the following invariants across all 17 repositories:
1. `Branch`: Active branch is strictly `main`.
2. `Clean`: Working tree has zero uncommitted changes (`git status --porcelain` is empty).
3. `Tag`: Latest SemVer tag is bumped and pushed.
4. `V1`: Exactly 148 markdown prompts present in `01-prompts/v1/`.
5. `V2`: Exactly 148 markdown prompts present in `01-prompts/v2/`.
6. `Skills`: Exactly 57 skill definitions present in `.agents/skills/`.
7. `Remotes`: Remote backup branch (`backup/*`), feature branch (`feat/*`), and release branch (`release/*`) exist on `origin`.
