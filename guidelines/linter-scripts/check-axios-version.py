#!/usr/bin/env python3
"""
Axios Version Safeguard (Cross-Platform Python)
==============================================
Validates that Axios is pinned to an approved safe version
and not using any range symbols (^, ~, >=, *).

Blocked versions: 1.14.1, 0.30.4
Approved versions: 1.14.0, 0.30.3

Usage:
    python linter-scripts/check-axios-version.py
"""

import json
import os
import sys

BLOCKED_VERSIONS = {"1.14.1", "0.30.4"}
APPROVED_VERSIONS = {"1.14.0", "0.30.3"}
RANGE_PREFIXES = ("^", "~", ">=", ">", "<=", "<", "*")


def main():
    pkg_path = os.path.join(os.getcwd(), "package.json")
    if not os.path.exists(pkg_path):
        print("[INFO] No package.json found. Skipping Axios check.")
        sys.exit(0)

    try:
        with open(pkg_path, "r", encoding="utf-8") as f:
            pkg = json.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to parse package.json: {e}")
        sys.exit(1)

    deps = pkg.get("dependencies", {})
    dev_deps = pkg.get("devDependencies", {})
    current = deps.get("axios") or dev_deps.get("axios")

    if not current:
        print("[INFO] Axios is not declared in package.json.")
        sys.exit(0)

    print(f"[INFO] Axios version in package.json: {current}")

    # Check for range symbols or latest
    if current.startswith(RANGE_PREFIXES) or current in ("*", "latest"):
        print(f"[FAIL] Axios version uses a range symbol or tag: {current}")
        print('       Fix: Use an exact version like "axios": "1.14.0"')
        sys.exit(1)

    # Check blocked versions
    if current in BLOCKED_VERSIONS:
        print(f"[FAIL] Axios version {current} is BLOCKED (known security vulnerability)")
        print(f"       Approved versions: {', '.join(sorted(APPROVED_VERSIONS))}")
        sys.exit(1)

    # Check approved versions
    if current in APPROVED_VERSIONS:
        print(f"[PASS] Axios {current} is an approved safe version.")
        sys.exit(0)
    else:
        print(f"[WARNING] Axios {current} is not in the approved list ({', '.join(sorted(APPROVED_VERSIONS))})")
        print("          This version has not been verified. Please review 02-spec/01-app/axios-version-control/")
        sys.exit(1)


if __name__ == "__main__":
    main()
