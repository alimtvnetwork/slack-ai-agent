#!/usr/bin/env python3
"""
Runner Dispatch Anti-Patterns Guard (Cross-Platform Python)
===========================================================
Fails CI if run.sh or run.ps1 reintroduce forbidden dispatch anti-patterns
in the fix-repo dispatch region.

Spec: 02-spec/15-distribution-and-runner/06-fix-repo-forwarding.md

Usage:
    python linter-scripts/check-runner-dispatch-antipatterns.py
"""

import os
import re
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SH_PATH = os.path.join(REPO_ROOT, "run.sh")
PS_PATH = os.path.join(REPO_ROOT, "run.ps1")


def check_run_sh() -> list[str]:
    violations = []
    if not os.path.exists(SH_PATH):
        return ["run.sh is missing"]

    with open(SH_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract fix-repo block if present
    match = re.search(r"fix-repo\)(.*?);;", content, re.DOTALL)
    if match:
        block = match.group(1)
        # Check for forbidden inline logic instead of script forwarding
        if "curl " in block and "scripts/fix-repo" not in block:
            violations.append("run.sh fix-repo branch contains forbidden direct curl calls instead of delegating to scripts/fix-repo/")
    return violations


def check_run_ps1() -> list[str]:
    violations = []
    if not os.path.exists(PS_PATH):
        return ["run.ps1 is missing"]

    with open(PS_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    match = re.search(r'"fix-repo"\s*\{(.*?)\}', content, re.DOTALL)
    if match:
        block = match.group(1)
        if "Invoke-WebRequest" in block and "scripts/fix-repo" not in block and "scripts\\fix-repo" not in block:
            violations.append("run.ps1 fix-repo branch contains forbidden direct Invoke-WebRequest instead of delegating to scripts/fix-repo/")
    return violations


def main():
    print("[INFO] Checking runner dispatch patterns in run.sh and run.ps1...")
    violations = []
    violations.extend(check_run_sh())
    violations.extend(check_run_ps1())

    if violations:
        print("\n[FAIL] Runner dispatch anti-patterns detected:")
        for v in violations:
            print(f"  ::error::{v}")
        sys.exit(1)

    print("[PASS] Runner dispatch patterns verified successfully.")
    sys.exit(0)


if __name__ == "__main__":
    main()
