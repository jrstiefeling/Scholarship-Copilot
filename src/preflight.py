"""
preflight.py — sanity checks before running Scholarship Copilot scripts.

Checks:
1) Required environment variables
2) Required local credential files
3) Placeholder values in config files
"""

from __future__ import annotations

import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT / "config"
CREDENTIALS_DIR = ROOT / "credentials"

PROFILE_PATH = CONFIG_DIR / "profile.json"
GOOGLE_IDS_PATH = CONFIG_DIR / "google_ids.json"
CREDS_PATH = CREDENTIALS_DIR / "credentials.json"
TOKEN_PATH = CREDENTIALS_DIR / "token.json"

REQUIRED_ENV = ["BRAVE_API_KEY", "ANTHROPIC_API_KEY"]


def check_env_vars() -> list[str]:
    issues: list[str] = []
    for key in REQUIRED_ENV:
        value = os.getenv(key, "").strip()
        if not value or value.startswith("REPLACE_"):
            issues.append(f"Missing env var: {key}")
    return issues


def check_local_files() -> list[str]:
    issues: list[str] = []
    if not CREDS_PATH.exists():
        issues.append(f"Missing file: {CREDS_PATH}")
    if not TOKEN_PATH.exists():
        issues.append(f"Missing file: {TOKEN_PATH}")
    return issues


def check_json_placeholders() -> list[str]:
    issues: list[str] = []

    if not PROFILE_PATH.exists():
        issues.append(f"Missing file: {PROFILE_PATH}")
    else:
        profile = json.loads(PROFILE_PATH.read_text())
        first_name = str(profile.get("student", {}).get("first_name", "")).strip()
        if not first_name or first_name.startswith("STUDENT_"):
            issues.append("profile.json still has placeholder student first name")

    if not GOOGLE_IDS_PATH.exists():
        issues.append(f"Missing file: {GOOGLE_IDS_PATH}")
    else:
        ids = json.loads(GOOGLE_IDS_PATH.read_text())
        spreadsheet_id = str(ids.get("spreadsheet_id", ""))
        drafts_folder_id = str(ids.get("drafts_folder_id", ""))
        if spreadsheet_id.startswith("REPLACE_") or not spreadsheet_id:
            issues.append("google_ids.json has placeholder spreadsheet_id")
        if drafts_folder_id.startswith("REPLACE_") or not drafts_folder_id:
            issues.append("google_ids.json has placeholder drafts_folder_id")

    return issues


def main() -> int:
    print("Scholarship Copilot preflight\n")
    all_issues = check_env_vars() + check_local_files() + check_json_placeholders()
    if all_issues:
        print("Preflight failed. Fix the following:")
        for issue in all_issues:
            print(f"- {issue}")
        return 1

    print("Preflight passed. You can run the workflow scripts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
