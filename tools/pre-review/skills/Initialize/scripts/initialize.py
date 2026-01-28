import json
import os
import random
import re
import socket
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def add_project_root(marker="config.py"):
    """Ensure the repository root (where config.py lives) is on sys.path."""
    current = Path(__file__).resolve()
    for parent in (current.parent, *current.parents):
        if (parent / marker).exists():
            root = str(parent)
            if root not in sys.path:
                sys.path.insert(0, root)
            return


add_project_root()

from config import load_config

CFG = load_config()
OWNER = CFG["github"]["owner"]
REPO = CFG["github"]["repo"]
BASE_URL = "https://api.github.com"
OUT_DIR = Path(CFG["paths"]["pr_records"])
BATCH_SIZE = CFG["batch"].get("initialize_per_page", 20)
MAX_INITIALIZE = CFG["batch"].get("initialize_max_records")

token = os.getenv(CFG["github"].get("token_env", "GITHUB_TOKEN"))
HEADERS = {
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": CFG["github"].get("user_agent", "python-attrs-pr-scraper"),
}
if token:
    HEADERS["Authorization"] = f"token {token}"

CONTEXT_WINDOW = 30  # lines above/below diffs
FETCH_TIMEOUT = 10   # seconds per file fetch
_FILE_CACHE = {}


def github_get(path, params=None):
    url = f"{BASE_URL}{path}"
    if params:
        url = f"{url}?{urlencode(params)}"
    req = Request(url, headers=HEADERS)
    try:
        with urlopen(req) as resp:
            return json.load(resp)
    except HTTPError as exc:
        print(f"HTTP error {exc.code} for {url}")
    except URLError as exc:
        print(f"URL error for {url}: {exc.reason}")
    return None


def fetch_paginated(path, per_page=100):
    page = 1
    items = []
    while True:
        data = github_get(path, {"per_page": per_page, "page": page})
        if not data:
            break
        items.extend(data)
        if len(data) < per_page:
            break
        page += 1
    return items


def clean_patch(patch):
    """Parse a patch into structured hunks with line numbers."""
    hunks = []
    current = None
    new_line_no = None
    for line in patch.splitlines():
        if line.startswith("@@"):
            m = re.search(r"\+(\d+)", line)
            new_line_no = int(m.group(1)) if m else None
            current = {"header": line, "changes": []}
            hunks.append(current)
            continue
        if current is None:
            continue
        if line.startswith("+"):
            if new_line_no is not None:
                current["changes"].append(
                    {"kind": "add", "line": new_line_no, "content": line[1:]}
                )
                new_line_no += 1
        elif line.startswith("-"):
            current["changes"].append({"kind": "del", "line": None, "content": line[1:]})
        else:
            if new_line_no is not None:
                current["changes"].append(
                    {"kind": "ctx", "line": new_line_no, "content": line[1:]}
                )
                new_line_no += 1
    return hunks


def find_enclosing_scope(lines, line_no):
    """Find nearest enclosing def/class name above the line_no (1-based)."""
    idx = max(line_no - 1, 0)
    for i in range(idx, -1, -1):
        stripped = lines[i].lstrip()
        m_func = re.match(r"(async\s+)?def\s+([\w_]+)", stripped)
        m_cls = re.match(r"class\s+([\w_]+)", stripped)
        if m_func:
            return m_func.group(2)
        if m_cls:
            return m_cls.group(1)
    return None


def compute_line_bounds(hunks, window):
    """Compute min/max lines needed based on hunks with line numbers."""
    line_numbers = [c["line"] for h in hunks for c in h["changes"] if c.get("line")]
    if not line_numbers:
        return None
    lo = max(min(line_numbers) - window, 1)
    hi = max(line_numbers) + window
    return lo, hi


def fetch_file_contents(file_entry, hunks, window=CONTEXT_WINDOW, timeout=FETCH_TIMEOUT):
    """
    Fetch partial file contents around needed lines.
    Returns (lines, missing_reason).
    """
    url = file_entry.get("raw_url")
    if not url:
        return None, "no_raw_url"
    if url in _FILE_CACHE:
        return _FILE_CACHE[url]

    bounds = compute_line_bounds(hunks, window)
    if bounds is None:
        return None, "no_line_numbers"
    start_line, end_line = bounds

    req = Request(url, headers=HEADERS)
    lines = []
    try:
        with urlopen(req, timeout=timeout) as resp:
            for idx, raw_line in enumerate(resp, start=1):
                if idx < start_line:
                    continue
                if idx > end_line:
                    break
                lines.append(raw_line.decode("utf-8", errors="replace").rstrip("\n"))
    except (socket.timeout, TimeoutError):
        return None, "network_timeout"
    except (HTTPError, URLError):
        return None, "network_error"
    except Exception:
        return None, "network_error"

    _FILE_CACHE[url] = (lines, None)
    return lines, None


def enrich_hunks_with_context(hunks, file_lines, missing_reason=None, context_window=CONTEXT_WINDOW):
    """Attach context and enclosing scope to hunks."""
    if not hunks:
        return []
    for hunk in hunks:
        line_candidates = [c["line"] for c in hunk["changes"] if c["line"]]
        anchor = (min(line_candidates) if line_candidates else 1) - 1
        if file_lines:
            start = max(anchor - context_window, 0)
            end = min(anchor + context_window + 1, len(file_lines))
            hunk["context_before"] = file_lines[start:anchor]
            hunk["context_after"] = file_lines[anchor:end]
            hunk["enclosing"] = find_enclosing_scope(file_lines, anchor + 1)
            hunk["context_missing"] = False
            hunk["missing_reason"] = None
        else:
            hunk["context_before"] = []
            hunk["context_after"] = []
            hunk["enclosing"] = None
            hunk["context_missing"] = True
            hunk["missing_reason"] = missing_reason or "unavailable"
    return hunks


def process_pr(pr):
    number = pr.get("number")
    title = pr.get("title", "")
    author = pr.get("user", {}).get("login", "")
    description = pr.get("body") or ""

    files = fetch_paginated(f"/repos/{OWNER}/{REPO}/pulls/{number}/files")
    commits = fetch_paginated(f"/repos/{OWNER}/{REPO}/pulls/{number}/commits")

    commit_messages = [c.get("commit", {}).get("message", "") for c in commits if c.get("commit")]
    python_diffs = []

    for file_entry in files:
        filename = file_entry.get("filename", "")
        if not filename.endswith(".py"):
            continue
        patch = file_entry.get("patch")
        if not patch:
            continue
        hunks = clean_patch(patch)
        legacy_changes = [
            line
            for line in patch.splitlines()
            if line.startswith(("+", "-")) and not line.startswith(("+++", "---"))
        ]
        file_lines, missing_reason = fetch_file_contents(file_entry, hunks)
        enriched = enrich_hunks_with_context(hunks, file_lines, missing_reason=missing_reason)
        python_diffs.append(
            {
                "file": filename,
                "raw_patch": patch,
                "changes": legacy_changes,
                "hunks": enriched,
            }
        )

    if not python_diffs:
        return None

    record = {
        "pr_number": number,
        "title": title,
        "author": author,
        "reason": {
            "description": description,
            "commit_messages": commit_messages,
        },
        "python_diffs": python_diffs,
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUT_DIR / f"{number}.json", "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)
    return record


def main():
    page = 1
    processed_records = 0
    while processed_records < MAX_INITIALIZE:
        prs = github_get(
            f"/repos/{OWNER}/{REPO}/pulls",
            {"state": "closed", "per_page": BATCH_SIZE, "page": page},
        )
        if not prs:
            break

        for pr in prs:
            if processed_records >= MAX_INITIALIZE:
                break
            print(f"Processing PR #{pr.get('number')}")
            record = process_pr(pr)
            if record:
                processed_records += 1

        if processed_records >= MAX_INITIALIZE or len(prs) < BATCH_SIZE:
            break

        if not token:
            sleep_for = random.randint(30, 60)
            print(f"Sleeping for {sleep_for} seconds")
            time.sleep(sleep_for)
        page += 1


if __name__ == "__main__":
    main()
