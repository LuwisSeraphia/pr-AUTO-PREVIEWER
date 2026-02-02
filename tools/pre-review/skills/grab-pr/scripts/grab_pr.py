import json
import os
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def add_project_root(marker="config.py"):
    current = Path(__file__).resolve()
    for parent in (current.parent, *current.parents):
        if (parent / marker).exists():
            root = str(parent)
            if root not in sys.path:
                sys.path.insert(0, root)
            return


add_project_root()

from config import load_config  # noqa: E402

CFG = load_config()
OWNER = CFG["github"]["owner"]
REPO = CFG["github"]["repo"]
BASE_URL = "https://api.github.com"
OUT_DIR = Path(CFG["paths"]["new_pr"])
BATCH_DIR = Path(CFG["paths"]["dataset_dir"])
STATE_FILE = BATCH_DIR / "grab_pr_state.json"
PROCESSED_DIR = Path(CFG["paths"]["pr_records"])
BATCH_SIZE = CFG["batch"].get("initialize_per_page", 20)
GRAB_MAX_RECORDS = CFG["batch"].get("grab_max_records")
REQUEST_TIMEOUT = float(os.getenv("GITHUB_REQUEST_TIMEOUT", "30"))
MAX_RETRIES = int(os.getenv("GITHUB_REQUEST_RETRIES", "3"))
RETRY_DELAY = float(os.getenv("GITHUB_RETRY_DELAY", "2"))
CONTEXT_WINDOW = int(os.getenv("DIFF_CONTEXT_LINES", "5"))

TOKEN_ENV = CFG["github"].get("token_env", "GITHUB_TOKEN")
CONFIG_TOKEN = CFG["github"].get("token")
token = CONFIG_TOKEN or os.getenv(TOKEN_ENV)
HEADERS = {
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": CFG["github"].get("user_agent", "python-attrs-pr-scraper"),
}


def _build_session():
    session = requests.Session()
    retry = Retry(
        total=MAX_RETRIES,
        backoff_factor=RETRY_DELAY,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    headers = dict(HEADERS)
    if token:
        headers["Authorization"] = f"token {token}"
    session.headers.update(headers)
    return session


SESSION = _build_session()


def github_get(path, params=None, *, expect_json=True):
    url = f"{BASE_URL}{path}"
    resp = SESSION.get(url, params=params, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    return resp.json() if expect_json else resp.content


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


def parse_ts(ts):
    if not ts:
        return None
    if ts.endswith("Z"):
        ts = ts.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(ts)
    except ValueError:
        return None


def load_last_timestamp():
    if not STATE_FILE.exists():
        return None
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        ts_str = data.get("last_fetch_ts")
        return parse_ts(ts_str)
    except (json.JSONDecodeError, OSError):
        return None


def save_last_timestamp(ts):
    BATCH_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps({"last_fetch_ts": ts.isoformat()}), encoding="utf-8")


def existing_pr_numbers():
    ids = set()
    for directory in (OUT_DIR, PROCESSED_DIR):
        if not directory.exists():
            continue
        for path in directory.glob("*.json"):
            stem = path.stem
            if stem.isdigit():
                ids.add(int(stem))
    return ids


def build_context_lines(file_entry, window=CONTEXT_WINDOW):
    patch = file_entry.get("patch")
    if not patch:
        return ""
    return "\n".join(patch.splitlines()) + "\n"


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
        patch_text = build_context_lines(file_entry, CONTEXT_WINDOW)
        if not patch_text:
            continue
        python_diffs.append({"file": filename, "patch": patch_text})

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


def fetch_latest(limit, existing_ids):
    page = 1
    generated = 0

    while generated < limit:
        prs = github_get(
            f"/repos/{OWNER}/{REPO}/pulls",
            {"state": "closed", "sort": "updated", "direction": "desc", "per_page": BATCH_SIZE, "page": page},
        )
        if not prs:
            break

        for pr in prs:
            if generated >= limit:
                break
            number = pr.get("number")
            if number in existing_ids:
                continue
            print(f"Processing PR #{number}")
            record = process_pr(pr)
            if record:
                existing_ids.add(number)
                generated += 1

        if generated >= limit or len(prs) < BATCH_SIZE:
            break

        if not token:
            sleep_for = random.randint(30, 60)
            print(f"Sleeping for {sleep_for} seconds")
            time.sleep(sleep_for)
        page += 1

    return generated


def fetch_updated_since(last_ts, limit, existing_ids):
    page = 1
    generated = 0
    stop = False

    while generated < limit and not stop:
        prs = github_get(
            f"/repos/{OWNER}/{REPO}/pulls",
            {"state": "closed", "sort": "updated", "direction": "desc", "per_page": BATCH_SIZE, "page": page},
        )
        if not prs:
            break

        for pr in prs:
            updated_at = parse_ts(pr.get("updated_at"))
            if updated_at and updated_at <= last_ts:
                stop = True
                break
            number = pr.get("number")
            if number in existing_ids:
                continue
            print(f"Processing PR #{number} (updated after last timestamp)")
            record = process_pr(pr)
            if record:
                existing_ids.add(number)
                generated += 1
                if generated >= limit:
                    break

        if generated >= limit or stop or len(prs) < BATCH_SIZE:
            break

        if not token:
            sleep_for = random.randint(30, 60)
            print(f"Sleeping for {sleep_for} seconds")
            time.sleep(sleep_for)
        page += 1

    return generated


def fetch_single_pr(number):
    try:
        pr = github_get(f"/repos/{OWNER}/{REPO}/pulls/{number}")
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise
    if pr.get("state") != "closed":
        return None
    return pr


def backfill_before(start_number, limit, existing_ids):
    generated = 0
    current = start_number
    while current > 0 and generated < limit:
        if current in existing_ids:
            current -= 1
            continue
        pr = fetch_single_pr(current)
        if pr:
            print(f"Backfill processing PR #{current}")
            record = process_pr(pr)
            if record:
                existing_ids.add(current)
                generated += 1
        current -= 1
    return generated


def main():
    limit = GRAB_MAX_RECORDS if GRAB_MAX_RECORDS is not None else float("inf")
    existing_ids = existing_pr_numbers()
    last_ts = load_last_timestamp()
    now_ts = datetime.now(timezone.utc)

    if last_ts is None:
        print("No last timestamp found; fetching latest PRs.")
        fetched = fetch_latest(limit, existing_ids)
        print(f"Fetched {fetched} new PR records.")
        save_last_timestamp(now_ts)
        return

    print(f"Last fetch timestamp: {last_ts.isoformat()}. Checking for updates since then.")
    fetched = fetch_updated_since(last_ts, limit, existing_ids)
    if fetched:
        print(f"Fetched {fetched} PR(s) updated after last timestamp.")
        save_last_timestamp(now_ts)
        return

    print("No PRs updated after last timestamp; falling back to backfill.")
    min_existing = min(existing_ids) if existing_ids else None
    if min_existing is None:
        print("No existing PR records found; fetching latest.")
        fetched = fetch_latest(limit, existing_ids)
    else:
        start = max(min_existing - 1, 1)
        fetched = backfill_before(start, limit, existing_ids)
    print(f"Fetched {fetched} PR record(s) during backfill.")
    save_last_timestamp(now_ts)


if __name__ == "__main__":
    main()
