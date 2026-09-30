# Canonical Specification: AI Prompts V1/V2 Architecture & GitMap Discovery Benchmarks

> **Document Version:** 1.0.0  
> **Status:** APPROVED & ACTIVE  
> **Target Scope:** Meta-Repository (`alimtvnetwork/coding-guidelines-v24`) & All Connected Repositories

---

## 1. Executive Summary & Architecture Overview

To eliminate execution latency, avoid token waste from repetitive disk scans, and provide a deterministic multi-tier discovery pipeline, the AI Prompts library (`01-prompts/`) is segregated into two versioned tiers:

1. **V1 Prompts Tier (`01-prompts/v1/`):** Classic, proven prompts utilizing the Python script ecosystem (`03-ai-scripts/`) as their primary acceleration mechanism.
2. **V2 Prompts Tier (`01-prompts/v2/`):** Next-generation, high-performance prompts elevating the **GitMap Native AUM Engine** (`gitmap` CLI) as the primary discovery toolchain, with Python automation scripts preserved as resilient fallbacks.

```text
01-prompts/
├── readme.md                           # Architecture index & tier guide
├── v1/                                 # Classic prompts (Python-accelerated)
│   ├── 00-folder-structure/
│   ├── ... (all 22 categories)
│   └── 21-temp-end-to-end-tests/
└── v2/                                 # Modernized prompts (GitMap AUM Primary)
    ├── 00-folder-structure/
    ├── ... (all 22 categories)
    └── 21-temp-end-to-end-tests/
```

---

## 2. Multi-Engine Performance Benchmarks

The benchmark suite (`03-ai-scripts/40-run-search-benchmarks.py`) was executed across the `coding-guidelines-v24` codebase (700+ specifications, 22 prompt categories, 150,000+ lines).

### 2.1 Measured Performance Matrix

| Category | Workload / Query | Engine / Tool | Command / Syntax | Measured Latency (Avg) | Speedup vs PowerShell |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Wildcard File Search** | Universal `*test*.md` match | **Ripgrep** | `rg --files -g "*test*.md"` | **21.03 ms** | **16.7x faster** |
| | | **GitMap Native AUM** | `gitmap find "*test*" -ext "md"` | **57.50 ms** | **6.1x faster** |
| | | **Python Fast Scanner** | `python 03-ai-scripts/11-fast-file-scanner.py --search "test"` | **72.84 ms** | **4.8x faster** |
| | | **PowerShell Standard** | `Get-ChildItem -Recurse -File -Filter '*test*.md'` | **351.00 ms** | **1.0x (Baseline)** |
| **Complex Content / Regex** | Pattern `appfault\.AppError` | **GitMap Hot-Cache (`DH2D`)** | `gitmap search "AppError"` | **54.85 ms** (proc) / **0.04 ms** (RAM) | **5.3x – 7,000x faster** |
| | | **Ripgrep** | `rg "appfault\.AppError" .` | **32.02 ms** | **9.1x faster** |
| | | **PowerShell Pipeline** | `Get-ChildItem -Recurse -File \| Select-String "appfault\.AppError"` | **290.66 ms** (filtered) / **14.85 s** (full) | **1.0x (Baseline)** |
| | | **Python Cached Grep** | `python 03-ai-scripts/12-fast-cached-grep.py --pattern "..."` | **11,986.73 ms** | 0.02x |
| **File Content Streaming** | Stream `readme.md` (157 KB) | **Ripgrep** | `rg "^" readme.md` | **9.02 ms** | **26.0x faster** |
| | | **GitMap Cat** | `gitmap cat readme.md` | **49.05 ms** | **4.8x faster** |
| | | **Python Fast Reader** | `python 03-ai-scripts/17-fast-file-reader.py --file readme.md` | **53.76 ms** | **4.4x faster** |
| | | **PowerShell Get-Content** | `Get-Content readme.md` | **234.35 ms** | **1.0x (Baseline)** |

---

## 3. Concrete CLI Syntax Across Engines

### 3.1 GitMap Native AUM Engine (Primary Fast Path)
```bash
# 1. Universal Wildcard File Discovery (<60ms)
gitmap find "*test*" -ext "md"
gitmap find-files-any "error"

# 2. Substring & Indexed Repo Search (<55ms cold, <0.05ms hot)
gitmap search "AppError"
gitmap search history

# 3. Direct Zero-Disk File Streaming (<50ms)
gitmap cat readme.md
gitmap cat 02-spec/03-error-manage/readme.md

# 4. Pipeline Dynamic Waiting & Release Automation
gitmap pipeline-ai status -t 120
gitmap release --bump patch -y
```

### 3.2 Ripgrep (High-Throughput Multi-Core Grep)
```bash
# 1. File Glob Search (<25ms)
rg --files -g "*test*.md"

# 2. Complex Regex Content Search (<35ms)
rg "appfault\.AppError" .

# 3. Zero-Allocation File Streaming (<10ms)
rg "^" readme.md
```

### 3.3 Python Automation Toolchain (`03-ai-scripts/` Fallback)
```bash
# 1. Cached File Scanning
python 03-ai-scripts/11-fast-file-scanner.py --search "test" --limit 100

# 2. Cached Multi-threaded Grep
python 03-ai-scripts/12-fast-cached-grep.py --pattern "appfault\.AppError" --limit 50

# 3. Fast File Reader (<1000 lines)
python 03-ai-scripts/17-fast-file-reader.py --file readme.md --limit 1000
```

### 3.4 PowerShell 7 (`pwsh` Baseline)
```powershell
# 1. File Discovery with Pipeline Filtering
Get-ChildItem -Recurse -File -Filter "*test*.md" -Exclude ".git","node_modules"

# 2. Regex Content Search
Get-ChildItem -Path 01-prompts,04-code -Recurse -File -Filter *.go | Select-String -Pattern "appfault\.AppError"

# 3. File Content Reading
Get-Content readme.md -TotalCount 1000
```

---

## 4. Architectural Analysis & Speedup Drivers

1. **Elimination of CLR Object Overhead:** Standard PowerShell instantiates full `System.IO.FileInfo` objects with rich metadata for every file in the tree, creating massive GC pressure on repos with thousands of files. GitMap and Ripgrep run unmanaged, zero-alloc traversal loops.
2. **Analytical SplitDB Hot-Tier (`DH2D`):** GitMap persists query hashes into local SQLite tables. When a prompt or subagent repeats a query during verification loops, the result returns in microseconds (`0.04 ms`).
3. **Pipelined Raw Streaming:** Tools like `gitmap cat` stream directly to OS stdout, avoiding intermediate memory copies or disk writes.
