import json
import os
import random
import re
import socket
import sys
import time
from datetime import datetime, timedelta, timezone
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
OUT_DIR = Path(CFG["paths"]["new_pr"])
PR_RECORDS_DIR = Path(CFG["paths"]["pr_records"])
SEARCH_BATCH_SIZE = CFG["batch"].get("search_batch_size", 50)
SEARCH_SLEEP_SECONDS = CFG["batch"].get("search_sleep_seconds", 2)
DEFAULT_BACKFILL_COUNT = 20
NEWEST_LOOK = None  # Tracks the date string used for PR search
LAST_READ_PR = None  # Bookmark for backfill mode

token = os.getenv(CFG["github"].get("token_env", "GITHUB_TOKEN"))
NO_TOKEN = not bool(token)
_warned_no_token = False
HEADERS = {
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": CFG["github"].get("user_agent", "python-attrs-pr-scraper"),
}
if token:
    HEADERS["Authorization"] = f"token {token}"

CONTEXT_WINDOW = 30  # lines above/below diffs
FETCH_TIMEOUT = 10   # seconds per file fetch
_FILE_CACHE = {}


def github_get(path, params=None, quiet_404=False):
    url = f"{BASE_URL}{path}"
    if params:
        url = f"{url}?{urlencode(params)}"
    req = Request(url, headers=HEADERS)
    try:
        with urlopen(req) as resp:
            return json.load(resp)
    except HTTPError as exc:
        if exc.code == 404 and quiet_404:
            return None
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


def fetch_file_contents(file_entry):
    """Fetch full file contents for context; return lines list or None on failure."""
    url = file_entry.get("raw_url")
    if not url:
        return None
    req = Request(url, headers=HEADERS)
    try:
        with urlopen(req) as resp:
            text = resp.read().decode("utf-8", errors="replace")
            return text.splitlines()
    except (HTTPError, URLError):
        return None


def enrich_hunks_with_context(hunks, file_lines, context_window=5):
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
        else:
            hunk["context_before"] = []
            hunk["context_after"] = []
            hunk["enclosing"] = None
            hunk["context_missing"] = True
    return hunks


def start_of_yesterday_utc():
    today = datetime.now(timezone.utc).date()
    start_of_yesterday = today - timedelta(days=1)
    return start_of_yesterday.strftime("%Y-%m-%d")


def fetch_recent_prs(since_date, per_page=SEARCH_BATCH_SIZE):
    global _warned_no_token
    results = []
    page = 1
    query = f"repo:{OWNER}/{REPO} is:pr created:>={since_date}"

    while True:
        params = {
            "q": query,
            "sort": "created",
            "order": "asc",
            "per_page": per_page,
            "page": page,
        }
        data = github_get("/search/issues", params)
        if not data:
            break

        items = data.get("items") or []
        if not items:
            break

        results.extend(items)
        if len(items) < per_page:
            break

        if NO_TOKEN:
            if not _warned_no_token:
                print("No available token detected,run the following command: export GITHUB_TOKEN=<your_token_here>")
                _warned_no_token = True
            sleep_for = random.randint(30, 60)
            print(f"token unavailable, waiting for {sleep_for} seconds.")
            time.sleep(sleep_for)
        else:
            time.sleep(SEARCH_SLEEP_SECONDS)
        page += 1

    return results


def process_pr(pr_info, allow_missing=False):
    number = pr_info.get("number")
    if not number:
        return None

    print(f"Processing PR #{number}")
    pr_detail = github_get(f"/repos/{OWNER}/{REPO}/pulls/{number}", quiet_404=allow_missing)
    if not pr_detail:
        return None

    title = pr_detail.get("title", "")
    author = pr_detail.get("user", {}).get("login", "")
    description = pr_detail.get("body") or ""

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

    return {
        "pr_number": number,
        "title": title,
        "author": author,
        "created_at": pr_detail.get("created_at", ""),
        "reason": {
            "description": description,
            "commit_messages": commit_messages,
        },
        "python_diffs": python_diffs,
    }


def save_record(record):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"{record['pr_number']}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)
    # Small pause to be gentle with the API.
    time.sleep(1)
    return record["pr_number"]


def init_last_read_pr():
    """Initialize LAST_READ_PR lazily from existing PR_records filenames."""
    global LAST_READ_PR
    if LAST_READ_PR is not None:
        return
    if not os.path.isdir(PR_RECORDS_DIR):
        return
    candidates = []
    for name in os.listdir(PR_RECORDS_DIR):
        if not name.endswith(".json"):
            continue
        base = name[:-5]
        if base.isdigit():
            candidates.append(int(base))
    if candidates:
        LAST_READ_PR = min(candidates)


def backfill_prs(count):
    """Backfill historical PRs starting from the bookmark and moving backwards."""
    global LAST_READ_PR
    init_last_read_pr()
    if LAST_READ_PR is None:
        print("No bookmark available to backfill from.")
        return []

    start_pr = LAST_READ_PR - 1
    processed = []
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for pr_number in range(start_pr, start_pr - count, -1):
        if pr_number <= 0:
            break
        record = process_pr({"number": pr_number}, allow_missing=True)
        if not record:
            continue
        pr_num = save_record(record)
        processed.append(pr_num)

    if processed:
        LAST_READ_PR = min(processed)
        print(f"Backfill complete. Updated LAST_READ_PR to {LAST_READ_PR}.")
    else:
        print("Backfill completed with no PRs processed.")
    return processed


def process_recent_prs(pr_list):
    processed = []
    for pr_info in pr_list:
        record = process_pr(pr_info)
        if not record:
            continue
        pr_num = save_record(record)
        processed.append(pr_num)
    return processed


def main(backfill_count=DEFAULT_BACKFILL_COUNT):
    global NEWEST_LOOK
    if NEWEST_LOOK is None:
        NEWEST_LOOK = start_of_yesterday_utc()
    now_utc = datetime.now(timezone.utc)
    NEWEST_LOOK = now_utc.date().strftime("%Y-%m-%d")
    print(f"Lookup date set to {NEWEST_LOOK} (UTC timestamp: {now_utc.strftime('%Y-%m-%dT%H:%M:%SZ')})")

    print(f"Fetching PRs created since {NEWEST_LOOK}")
    recent_prs = fetch_recent_prs(NEWEST_LOOK)

    recent_processed = process_recent_prs(recent_prs) if recent_prs else []
    if recent_processed:
        print(f"Fetched {len(recent_processed)} new PR record(s): {', '.join(map(str, recent_processed))}")
        return

    print("No latest PRs found. Attempting to backfill older PRs automatically.")
    backfilled = backfill_prs(backfill_count)
    if backfilled:
        print(f"Backfilled PRs: {', '.join(map(str, backfilled))}")
    else:
        print("No backfilled PRs.")


if __name__ == "__main__":
    main()
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
