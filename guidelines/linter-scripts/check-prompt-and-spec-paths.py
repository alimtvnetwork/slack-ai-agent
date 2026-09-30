#!/usr/bin/env python3
"""
Linter: check-prompt-and-spec-paths.py
Scans 01-prompts/, spec/, .ai-memory/, and .agents/ for relative file path references
in markdown links and backticks, verifying that all referenced paths exist on disk.
"""

import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

SCAN_DIRS = [
    REPO_ROOT / '01-prompts',
    REPO_ROOT / '.agents' / 'skills',
]

EXCLUDE_PARTS = {
    '.git', 'node_modules', 'dist', 'build', '.venv', 'tmp',
    '.gemini', '__pycache__', 'release-artifacts', 'old-coding-guidelines',
    'old-plan-prompts', '21-old-execute-prompts'
}

KNOWN_EXTENSIONS = (
    '.md', '.py', '.go', '.ts', '.tsx', '.json', '.yaml', '.yml',
    '.toml', '.sh', '.ps1', '.sql', '.txt', '.png', '.svg', '.cjs', '.mjs'
)

IGNORE_PREFIXES = (
    "http://", "https://", "mailto:", "conversation:", "file:///",
    "git://", "ssh://", "npm:", "cargo:", "cli/"
)

IGNORE_TERMS = {
    "path/to/file", "path/to/target", "path/to/dir", "path/to/component", "path/to/spec.md",
    "context.Context", "apperror.Wrap", "os.Exit", "fmt.Sprintf",
    "package.json", "tsconfig.json", "version.json", "agents.md", "readme.md",
    "target_files", "target-dir", "target_file", "your-branch", "src/enums/UserRoleType.ts",
    "src/services/user.go", "src/logger/log.ts", "src/storage/db.go", "src/types/UserTypes.ts",
    "src/services/UserService.ts", "app/main.go", "assets/<NN-folder>/<NN-file>.<ext>",
    "assets/01-icons/03-logo.svg", "src/types/", "src/enums/", "domain/types", "domain/types/",
    "types/", "models/", "pkg/types", "cmd/main.go", ".circleci/config.yml",
    ".ai-memory/plans/subtasks/01-coding-guideline-fixes/", ".ai-memory/29-plan.md",
    "src/models/auth.ts", "src/services/auth.ts", "src/services/api.ts",
    "src/state/user.ts", "src/utils/status.ts", "src/task.rs", "pkg/api/order.go",
    "gitmap/cmd/rootusage.go", "gitmap/cmd/clone.go", "gitmap/cloner/runners.go",
    "src/cluster/exec.go", "src/storage/temp.go", "./001-....md",
    "src/backend/", "src/frontend/", "src/shared/", "src/auth/service.go", "src/api/handler.ts",
    "spec/02", "colors-themes/Palette.md", "colors-themes/Tokens.json",
    "enums/user_role_type.go", "constants/http_constants.go", "src/enums/user-role-type.ts",
    "src/Enums/", "src/Enums/OrderStatusType.php", "enums/user_role_type.py",
    "cmd/user.go", "src/cli/audit.ts", "scripts/deploy.py",
    "02-spec/25-app-spec-audit/", "04-php/00-overview.md", "02-typescript/08-typescript-standards-reference.md",
    "01-cross-language/18-code-mutation-avoidance.md", ".ai-memory/temp/recent-file-changes.lock",
    ".ai-memory/temp/recent-file-changes.json", ".ai-memory/test-heatmap.json",
    ".ai-memory/ambiguous-questions/02-ambiguity-resolved/02-macro-step-open-command-behavior.md",
    "colors-themes/palette.md", "colors-themes/01-palette.md",
    "prompts/02-plan.md", "prompts/01-prompt.md",
    "icons-svg/01-logo.svg", "icons-svg/02-logo-dark.svg", "icons-svg/03-logo-white.svg",
    "icons-svg/04-logo-animated.svg", "icons-svg/logo-animated.svg",
    "02-projects/01-acme-pay/readme.md",
    "youtube-thumbnails/01-thumbnail-1280x720.png",
    "linkedin-banners/02-banner-3168x792.png", "linkedin-banners/02-banner-2256x382.png",
    "02-spec/02-coding-guidelines/01-cross-language/14-constants-enums.md",
    "constants/cors.py"
}

STRIP_CHARS = " `\"'(),:;[]{}"


def normalize_path(raw: str) -> str:
    s = raw.strip(STRIP_CHARS)
    if ":" in s:
        # Strip line numbers like linter-scripts/validate-guidelines.py:133
        parts = s.split(":")
        if parts[0] and (parts[1].isdigit() or "-" in parts[1]):
            s = parts[0]
    return s


def is_repo_path(raw: str) -> bool:
    s = normalize_path(raw)
    if not s or " " in s or "\n" in s or "\r" in s:
        return False
    if s.startswith("!["):
        return False
    for pfx in IGNORE_PREFIXES:
        if s.startswith(pfx):
            return False
    if s in IGNORE_TERMS or s.endswith(".sh") or s.endswith(".lock"):
        return False
    if "<" in s or ">" in s or "*" in s or "{" in s or "}" in s or "\\\\" in s:
        return False
    if "XX-" in s or "xx-" in s or "NN-" in s or "/XX/" in s or "/XX" in s or "vX." in s or "/tmp/" in s or "path/to/" in s:
        return False
    if s.startswith(("spec/", ".ai-memory/", ".agents/", "linter-scripts/", "linters-cicd/", "src/", "cmd/", "assets/", "reports/", "scripts/")):
        return True
    if "/" in s and any(s.endswith(ext) for ext in KNOWN_EXTENSIONS):
        return True
    return False


def check_paths() -> int:
    findings = []

    for sdir in SCAN_DIRS:
        if not sdir.exists():
           continue
        for p in sdir.rglob('*.md'):
            if any(ex in p.parts for ex in EXCLUDE_PARTS):
                continue
            rel_file = p.relative_to(REPO_ROOT).as_posix()
            try:
                content = p.read_text(encoding='utf-8', errors='replace')
            except Exception:
                continue

            for line_no, line in enumerate(content.splitlines(), start=1):
                # 1. Markdown links [text](target)
                for m in re.finditer(r"\[([^\]]*)\]\(([^)#\s]+)(?:#[^\)]*)?\)", line):
                    target = m.group(2).strip(STRIP_CHARS)
                    if is_repo_path(target):
                        p_root = (REPO_ROOT / target).resolve()
                        p_rel = (p.parent / target).resolve()
                        if not p_root.exists() and not p_rel.exists():
                            findings.append((rel_file, line_no, target, "markdown link"))

                # 2. Backtick paths `path/to/file`
                for m in re.finditer(r"`([^`\n]+)`", line):
                    target = m.group(1).strip(STRIP_CHARS)
                    if is_repo_path(target):
                        p_root = (REPO_ROOT / target).resolve()
                        p_rel = (p.parent / target).resolve()
                        if not p_root.exists() and not p_rel.exists():
                            findings.append((rel_file, line_no, target, "backtick path"))

    if not findings:
        print("[PASS] All markdown path references in prompts and specs exist on disk.")
        return 0

    print(f"[FAIL] Found {len(findings)} broken/dead path reference(s):")
    for rel_file, line_no, target, kind in findings:
        print(f'::error file={rel_file},line={line_no}::Dead {kind} reference "{target}" does not exist on disk.')
    return 1


if __name__ == "__main__":
    sys.exit(check_paths())
