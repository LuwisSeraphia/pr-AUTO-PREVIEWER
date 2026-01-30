'''
THIS FILE IS FOR PERSONALIZED MODIFICATION BASED ON THE ORIGINAL FILE dataset/grapNew.py 
SUPPORT PERSONIZED UPDATE RULES AS NEEDED.
'''
import json
import os
import random
import re
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
CONTEXT_WINDOW = int(os.getenv("DIFF_CONTEXT_LINES", "20"))

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


def build_context_lines(file_entry, window=CONTEXT_WINDOW):
    """Fetch up to window lines around the first changed hunk."""
    url = file_entry.get("raw_url")
    patch = file_entry.get("patch")
    if not url or not patch:
        return []

    try:
        with urlopen(Request(url, headers=HEADERS)) as resp:
            file_lines = resp.read().decode("utf-8", errors="replace").splitlines()
    except (HTTPError, URLError):
        return []

    starts = []
    for line in patch.splitlines():
        if line.startswith("@@"):
            m = re.search(r"\+(\d+)", line)
            if m:
                starts.append(int(m.group(1)))
    anchor = min(starts) if starts else 1
    lo = max(anchor - 1 - window, 0)
    hi = min(anchor - 1 + window + 1, len(file_lines))
    return [f" {text}" for text in file_lines[lo:hi]]


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

        # Respect GitHub search API rate limits (30 req/min).
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
        legacy_changes = [
            line
            for line in patch.splitlines()
            if line.startswith(("+", "-")) and not line.startswith(("+++", "---"))
        ]
        python_diffs.append(
            {
                "file": filename,
                "changes": legacy_changes,
                "context": build_context_lines(file_entry),
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


def init_last_read_pr():
    """Initialize LAST_READ_PR lazily from existing PR-processed filenames."""
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
        return

    start_pr = LAST_READ_PR - 1
    processed = []
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for pr_number in range(start_pr, start_pr - count, -1):
        if pr_number <= 0:
            break
        # 404s are expected when walking backwards because PR numbers are sparse.
        record = process_pr({"number": pr_number}, allow_missing=True)
        if not record:
            continue
        out_path = OUT_DIR / f"{record['pr_number']}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False, indent=2)
        time.sleep(1)
        processed.append(pr_number)

    if processed:
        LAST_READ_PR = min(processed)
        print(f"Backfill complete. Updated LAST_READ_PR to {LAST_READ_PR}.")
    else:
        print("Backfill completed with no PRs processed.")


def main():
    global NEWEST_LOOK
    # Initialize search start to yesterday if not set, then bump to today's date for this run.
    if NEWEST_LOOK is None:
        NEWEST_LOOK = start_of_yesterday_utc()
    now_utc = datetime.now(timezone.utc)
    NEWEST_LOOK = now_utc.date().strftime("%Y-%m-%d")
    print(f"Lookup date set to {NEWEST_LOOK} (UTC timestamp: {now_utc.strftime('%Y-%m-%dT%H:%M:%SZ')})")

    print(f"Fetching PRs created since {NEWEST_LOOK}")
    recent_prs = fetch_recent_prs(NEWEST_LOOK)

    if not recent_prs:
        print("No latest PRs found.")
        choice = input("No new PRs found. Do you want to backfill PRs from history? (y/n) ").strip().lower()
        if choice != "y":
            return
        num_input = input("How many PRs to backfill? (default 20): ").strip()
        backfill_count = 20
        if num_input:
            try:
                parsed = int(num_input)
                if parsed > 0:
                    backfill_count = parsed
            except ValueError:
                print("Invalid number, using default 20.")
        backfill_prs(backfill_count)
        return

    os.makedirs(OUT_DIR, exist_ok=True)

    for pr_info in recent_prs:
        record = process_pr(pr_info)
        if not record:
            continue
        out_path = os.path.join(OUT_DIR, f"{record['pr_number']}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False, indent=2)
        # Small pause to be gentle with the API.
        time.sleep(1)


if __name__ == "__main__":
    main()
