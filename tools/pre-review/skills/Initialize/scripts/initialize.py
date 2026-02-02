import json
import os
import random
import re
import sys
import time
from pathlib import Path
import socket
from urllib.parse import urlencode
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

from config import load_config


CFG = load_config()
OWNER = CFG["github"]["owner"]
REPO = CFG["github"]["repo"]
BASE_URL = "https://api.github.com"
OUT_DIR = Path(CFG["paths"]["new_pr"])
BATCH_SIZE = CFG["batch"].get("initialize_per_page", 20)
MAX_INITIALIZE = CFG["batch"].get("grab_max_records")
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
  # gh handles auth; token kept for compatibility


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


def github_get(path, params=None, *, accept=None, expect_json=True):
    url = f"{BASE_URL}{path}"
    headers = {}
    if accept:
        headers["Accept"] = accept
    t_start = time.perf_counter()
    resp = SESSION.get(url, params=params, headers=headers, timeout=REQUEST_TIMEOUT)
    t_fetch = time.perf_counter()
    # print(
    #     f"[http] url={resp.url} status={resp.status_code} "
    #     f"fetch_s={t_fetch - t_start:.3f}"
    # )
    resp.raise_for_status()
    if expect_json:
        data = resp.json()
    else:
        data = resp.content
    t_done = time.perf_counter()
    # print(
    #     f"[http] url={resp.url} parse_s={t_done - t_fetch:.3f} total_s={t_done - t_start:.3f}"
    # )
    return data

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


_file_cache = {}
def build_context_lines(file_entry, window=CONTEXT_WINDOW):
    patch = file_entry.get("patch")
    if not patch:
        return ""

    # Merge diff +上下文为单块输出，保留原有符号和顺序
    merged = "\n".join(patch.splitlines()) + "\n"
    return merged


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
        python_diffs.append({
            "file": filename,
            "patch": patch_text,
        })

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
    generated_records = 0  # count only successfully written JSON records
    limit = MAX_INITIALIZE if MAX_INITIALIZE is not None else float("inf")

    while generated_records < limit:
        prs = github_get(
            f"/repos/{OWNER}/{REPO}/pulls",
            {"state": "closed", "per_page": BATCH_SIZE, "page": page},
        )
        if not prs:
            break

        for pr in prs:
            if generated_records >= limit:
                break
            print(f"Processing PR #{pr.get('number')}")
            record = process_pr(pr)
            if record:
                generated_records += 1

        if generated_records >= limit or len(prs) < BATCH_SIZE:
            break

        if not token:
            sleep_for = random.randint(30, 60)
            print(f"Sleeping for {sleep_for} seconds")
            time.sleep(sleep_for)
        page += 1

if __name__ == "__main__":
    main()
