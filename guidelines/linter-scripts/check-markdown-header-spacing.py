#!/usr/bin/env python3
"""
check-markdown-header-spacing.py

Checks that every markdown heading (lines starting with # outside fenced code blocks) has:
  - Exactly one blank line BEFORE the heading (unless it is the very first content line)
  - Exactly one blank line AFTER the heading

Applies to all .md files in 01-general-prompts/ and .ai-memory/
"""

import os
import sys

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

SCAN_DIRS = ["01-general-prompts", ".ai-memory"]
IGNORE_DIRS = {".git", "node_modules", ".github", "dist", "build", "tmp"}


def check_file(filepath):
    violations = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except (UnicodeDecodeError, IOError):
        return violations

    lines = content.split("\n")
    n = len(lines)
    is_in_code_block = False

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Track fenced code blocks
        if stripped.startswith("```"):
            is_in_code_block = not is_in_code_block
            continue

        # Skip headers inside code blocks
        if is_in_code_block:
            continue

        if not stripped.startswith("#"):
            continue

        line_num = i + 1  # 1-indexed for reporting

        # Check BEFORE: there must be a blank line before (unless i == 0)
        if i > 0:
            prev = lines[i - 1].strip()
            if prev != "":
                violations.append(
                    (line_num, f"Missing blank line BEFORE heading: '{stripped[:60]}'")
                )

        # Check AFTER: there must be a blank line after (unless it is the last line)
        if i + 1 < n:
            nxt = lines[i + 1].strip()
            if nxt != "":
                violations.append(
                    (line_num, f"Missing blank line AFTER heading: '{stripped[:60]}'")
                )

    return violations


def main():
    cwd = os.getcwd()
    total_violations = 0
    files_checked = 0

    for scan_dir in SCAN_DIRS:
        target = os.path.join(cwd, scan_dir)
        if not os.path.exists(target):
            continue

        for root, dirs, files in os.walk(target):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            for file in sorted(files):
                if not file.endswith(".md"):
                    continue
                filepath = os.path.join(root, file)
                files_checked += 1
                violations = check_file(filepath)
                for line_num, msg in violations:
                    rel = os.path.relpath(filepath, cwd).replace("\\", "/")
                    print(f"{rel}:{line_num}: {msg}")
                    total_violations += 1

    print(f"\nChecked {files_checked} markdown file(s). Found {total_violations} violation(s).")

    if total_violations > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
