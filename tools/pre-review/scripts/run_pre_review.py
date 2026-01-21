#!/usr/bin/env python3
"""
MR pre-review script for CI that evaluates Python changes in merge requests.
- Rule A: block when added Python lines exceed threshold.
- Rule B: block when Ruff fails on changed Python files.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Tuple


REPO_ROOT = Path(__file__).resolve().parents[3]
OUT_PATH = REPO_ROOT / "tools" / "pre-review" / "out" / "rule_results.json"
MAX_EVIDENCE_CHARS = 2000


def resolve_target_branch() -> str:
    """Resolve target branch: MR target, then default branch, otherwise main."""
    env = os.environ
    return (
        env.get("CI_MERGE_REQUEST_TARGET_BRANCH_NAME")
        or env.get("CI_DEFAULT_BRANCH")
        or "main"
    )


def resolve_commit() -> str:
    """Get current commit SHA (prefer env var, fallback to git)."""
    env_sha = os.environ.get("CI_COMMIT_SHA")
    if env_sha:
        return env_sha
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else "unknown"


def run_command(cmd: List[str]) -> Tuple[int, str, str]:
    """Run a command in repo root and return exit code, stdout, stderr."""
    try:
        result = subprocess.run(
            cmd, cwd=REPO_ROOT, capture_output=True, text=True, check=False
        )
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError as exc:
        return 127, "", f"{exc}"
    except Exception as exc:  # pragma: no cover - defensive
        return 1, "", f"{exc}"


def git_fetch(branch: str) -> Tuple[bool, str]:
    """Fetch target branch; return error message on failure."""
    code, out, err = run_command(["git", "fetch", "origin", branch])
    if code != 0:
        return False, f"git fetch failed (exit {code}): {err or out}"
    return True, ""


def git_diff(branch: str) -> Tuple[str, str]:
    """Get diff from target branch to HEAD (0-context for line counting)."""
    code, out, err = run_command(["git", "diff", "--unified=0", f"origin/{branch}...HEAD"])
    if code != 0:
        return "", f"git diff failed (exit {code}): {err or out}"
    return out, ""


def parse_threshold() -> Tuple[int, str]:
    """Parse threshold env var and return value plus source flag."""
    raw = os.environ.get("PRE_REVIEW_MAX_ADDED_PY_LINES")
    if raw is None:
        return 200, "default"
    try:
        return int(raw), "env"
    except ValueError:
        return 200, "invalid_env"


def count_added_python_lines(diff_text: str) -> Tuple[int, Counter]:
    """Count added Python lines in diff and aggregate per file."""
    total = 0
    per_file: Counter[str] = Counter()
    current_file: str | None = None

    for line in diff_text.splitlines():
        if line.startswith("+++ "):
            path = line[4:].strip()
            if path.startswith("b/"):
                path = path[2:]
            current_file = None if path == "/dev/null" else path
            continue
        if not (line.startswith("+") and not line.startswith("+++")):
            continue
        if current_file and current_file.endswith(".py"):
            # Ignore blank added lines to reduce noise.
            if line.strip() == "+":
                continue
            per_file[current_file] += 1
            total += 1
    return total, per_file


def extract_changed_python_files(diff_text: str) -> Tuple[List[str], List[str]]:
    """Extract changed Python files from diff, separating existing/missing."""
    files = set()
    for line in diff_text.splitlines():
        if not line.startswith("+++ "):
            continue
        path = line[4:].strip()
        if path.startswith("b/"):
            path = path[2:]
        if path == "/dev/null":
            continue
        if path.endswith(".py"):
            files.add(path)
    existing, missing = [], []
    for path in sorted(files):
        full = REPO_ROOT / path
        if full.exists():
            existing.append(path)
        else:
            missing.append(path)
    return existing, missing


def truncate(text: str, limit: int = MAX_EVIDENCE_CHARS) -> str:
    """Trim text to a max length to keep artifacts bounded."""
    if len(text) <= limit:
        return text
    return text[:limit] + "\n... (truncated)"


def run_ruff(py_files: Iterable[str]) -> Tuple[bool, dict]:
    """Run Ruff on changed Python files; return pass flag and details."""
    files = list(py_files)
    if not files:
        return True, {"files_checked": [], "note": "No Python files in diff"}
    code, out, err = run_command(["ruff", "check", *files])
    details = {
        "files_checked": files,
        "return_code": code,
        "stdout": truncate(out),
        "stderr": truncate(err),
    }
    return code == 0, details


def build_summary(rules: List[dict]) -> dict:
    """Summarize overall status and exit code from rule results."""
    blocked = any(not r.get("passed") and r.get("severity") == "block" for r in rules)
    return {
        "passed": not blocked,
        "blocked": blocked,
        "exit_code": 1 if blocked else 0,
    }


def write_results(payload: dict) -> None:
    """Write review results to JSON file."""
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)


def error_rules(message: str) -> List[dict]:
    """Produce blocking rule results when a critical step fails."""
    return [
        {
            "id": "MR_ADDED_PY_LINES",
            "passed": False,
            "severity": "block",
            "details": {"error": message},
        },
        {
            "id": "RUFF",
            "passed": False,
            "severity": "block",
            "details": {"error": message},
        },
    ]


def main() -> int:
    """Entry point: execute rules, emit report, and return exit code."""
    target_branch = resolve_target_branch()
    commit = resolve_commit()
    try:
        rules: List[dict] = []
        ok, fetch_err = git_fetch(target_branch)
        if not ok:
            rules = error_rules(fetch_err)
        else:
            diff_text, diff_err = git_diff(target_branch)
            if diff_err:
                rules = error_rules(diff_err)
            else:
                threshold, threshold_source = parse_threshold()
                added_total, per_file = count_added_python_lines(diff_text)
                top_counts = per_file.most_common(10)
                rules.append(
                    {
                        "id": "MR_ADDED_PY_LINES",
                        "passed": added_total <= threshold,
                        "severity": "block",
                        "details": {
                            "threshold": threshold,
                            "threshold_source": threshold_source,
                            "added_py_lines_total": added_total,
                            "top_files_by_added_lines": top_counts,
                        },
                    }
                )

                changed_py_files, missing_py_files = extract_changed_python_files(diff_text)
                ruff_passed, ruff_details = run_ruff(changed_py_files)
                if missing_py_files:
                    ruff_details["skipped_missing"] = missing_py_files
                rules.append(
                    {
                        "id": "RUFF",
                        "passed": ruff_passed,
                        "severity": "block",
                        "details": ruff_details,
                    }
                )
    except Exception as exc:  # pragma: no cover - defensive
        rules = error_rules(f"Unexpected error: {exc}")

    payload = {
        "summary": build_summary(rules),
        "rules": rules,
        "meta": {
            "target_branch": target_branch,
            "commit": commit,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
    }

    write_results(payload)

    print(f"Target branch: {target_branch}")
    for rule in rules:
        status = "PASS" if rule.get("passed") else "FAIL"
        rid = rule.get("id")
        if rid == "MR_ADDED_PY_LINES":
            details = rule.get("details", {})
            print(
                f"{rid}: {status} (added {details.get('added_py_lines_total', '?')}"
                f"/{details.get('threshold', '?')})"
            )
        elif rid == "RUFF":
            files = rule.get("details", {}).get("files_checked", [])
            print(f"{rid}: {status} (files: {len(files)})")
        else:
            print(f"{rid}: {status}")

    return payload["summary"]["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
