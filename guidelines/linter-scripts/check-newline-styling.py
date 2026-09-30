#!/usr/bin/env python3
"""
Newline & Code Style Linter
Enforces:
  1. Unix LF (\n) line endings only (no CRLF).
  2. UTF-8 encoding with NO Byte Order Mark (BOM).
  3. Exactly one trailing newline at EOF.
  4. No double empty lines (\n\n\n).
  5. No empty line at the start of a function or block.
  6. Blank line before return/throw/raise in multi-line blocks.
  7. Blank line after closing } when followed by more code.
"""

import os
import sys

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def check_file(filepath):
    violations = []

    # Check raw bytes for BOM and CRLF
    try:
        with open(filepath, "rb") as f:
            raw_bytes = f.read()
    except Exception as e:
        return [(1, f"Unable to read file: {e}")]

    # Check BOM
    if raw_bytes.startswith(b"\xef\xbb\xbf"):
        violations.append((1, "UTF-8 BOM detected (file must be UTF-8 with NO BOM)"))

    # Check CRLF
    if b"\r\n" in raw_bytes:
        violations.append((1, "CRLF (\\r\\n) line endings detected (must use Unix LF \\n only)"))

    # Decode text
    try:
        content = raw_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        violations.append((1, f"Encoding error: {exc} (must be valid UTF-8)"))
        return violations

    # Check trailing newline
    if content and not content.endswith("\n"):
        violations.append((len(content.splitlines()), "Missing terminating newline (\\n) at EOF"))

    lines = content.split("\n")

    empty_streak = 0
    for i, line in enumerate(lines):
        stripped = line.strip()

        # 1. No double empty lines (\n\n\n)
        if stripped == "":
            empty_streak += 1
            if empty_streak == 2:
                violations.append((i + 1, "No double empty lines (\\n\\n\\n) allowed"))
        else:
            empty_streak = 0

        # 2. No empty line at the start of a function/block
        if stripped.endswith("{"):
            if i + 1 < len(lines) and lines[i + 1].strip() == "":
                violations.append((i + 2, "No empty line at the start of a function or block"))

        # 3. Blank line before return (for multi-line functions/blocks)
        if stripped.startswith("return ") or stripped == "return":
            if i > 0:
                prev_line = lines[i - 1].strip()
                if (
                    prev_line != ""
                    and not prev_line.endswith("{")
                    and not prev_line.endswith("}")
                    and not prev_line.endswith(":")
                    and not prev_line.startswith("//")
                    and not prev_line.startswith("/*")
                    and not prev_line.startswith("*")
                ):
                    violations.append((i + 1, "Blank line required before return"))

        # 4. Blank line after } if followed by more code
        if stripped == "}":
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line != "" and not next_line.startswith(
                    ("}", "else", "catch", "finally", ")", "]", ",", ";", "//", "/*", "</")
                ):
                    violations.append((i + 1, "Blank line required after '}' if followed by more code"))

        # 5. Check for \n in Go files (exempt constant declarations)
        if filepath.endswith(".go"):
            if '"\\n"' in line and not stripped.startswith("const ") and not stripped.startswith("NewLine"):
                violations.append((i + 1, 'Use constants.NewLineUnix instead of literal "\\n"'))

    return violations


def get_target_dir():
    src_dir = os.path.join(os.getcwd(), "src")
    if os.path.exists(src_dir):
        return src_dir
    return os.getcwd()


def main():
    target_dir = get_target_dir()
    extensions = (".go", ".ts", ".tsx", ".js")
    ignore_dirs = {".git", "node_modules", ".github", ".ci-out", "dist", "build", "tmp", ".venv", "vendor"}

    total_violations = 0

    for root, dirs, files in os.walk(target_dir):
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        for file in files:
            if file.endswith(extensions):
                filepath = os.path.join(root, file)
                violations = check_file(filepath)
                if violations:
                    for line_num, msg in violations:
                        rel_path = os.path.relpath(filepath, os.getcwd()).replace("\\", "/")
                        print(f"{rel_path}:{line_num}: {msg}")
                        total_violations += 1

    if total_violations > 0:
        print(f"\n[FAIL] Found {total_violations} newline or encoding violation(s).")
        sys.exit(1)
    else:
        print("[PASS] All newline styling, encoding, and line ending checks passed.")
        sys.exit(0)


if __name__ == "__main__":
    main()
