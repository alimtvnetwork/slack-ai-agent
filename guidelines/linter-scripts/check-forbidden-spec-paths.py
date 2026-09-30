#!/usr/bin/env python3
"""
Forbidden Spec Paths Guard (Cross-Platform Python)
==================================================
Fails CI on any of these violations:
  1. Re-appearance of deprecated folders under spec/:
       - 02-spec/14-generic-update/
       - 02-spec/15-self-update-app-update/
  2. Any MERGE-PROPOSAL.md (case-insensitive) under spec/.
  3. Any uppercase letters in .md filenames under spec/ or release-artifacts/.

Usage:
    python linter-scripts/check-forbidden-spec-paths.py
"""

import os
import sys

SPEC_ROOT = "02-spec"
RELEASE_ROOT = "release-artifacts"
FORBIDDEN_DIRS = [
    os.path.join(SPEC_ROOT, "14-generic-update"),
    os.path.join(SPEC_ROOT, "15-self-update-app-update"),
]


def check_forbidden_dirs() -> list[str]:
    violations = []
    for d in FORBIDDEN_DIRS:
        if os.path.exists(d):
            violations.append(f"Forbidden folder present: {d} (merged into 02-spec/14-update/, must not re-appear)")
    return violations


def check_forbidden_files() -> list[str]:
    violations = []
    if os.path.exists(SPEC_ROOT):
        for root, _, files in os.walk(SPEC_ROOT):
            for f in files:
                if f.lower() == "merge-proposal.md":
                    hit = os.path.join(root, f)
                    violations.append(f"Forbidden file: MERGE-PROPOSAL.md must not be committed under spec/ ({hit})")
    return violations


def check_uppercase_md() -> list[str]:
    violations = []
    for search_root in (SPEC_ROOT, RELEASE_ROOT):
        if not os.path.exists(search_root):
            continue
        for root, _, files in os.walk(search_root):
            for f in files:
                if f.endswith(".md"):
                    # Check if basename has any uppercase letter
                    if any(c.isupper() for c in f):
                        hit = os.path.join(root, f)
                        violations.append(f"Uppercase letters in .md filename — rename to lowercase: {hit}")
    return violations


def main():
    print("[INFO] Checking for forbidden spec paths and uppercase .md filenames...")

    violations = []
    violations.extend(check_forbidden_dirs())
    violations.extend(check_forbidden_files())
    violations.extend(check_uppercase_md())

    if violations:
        print("\n[FAIL] Violations detected:")
        for v in violations:
            print(f"  ::error::{v}")
        print("\nFixes:")
        print("  - Consolidated update home: 02-spec/14-update/")
        print("  - Markdown filenames must be all lowercase (e.g. readme.md).")
        sys.exit(1)

    print("[PASS] No forbidden paths or uppercase .md filenames detected.")
    sys.exit(0)


if __name__ == "__main__":
    main()
