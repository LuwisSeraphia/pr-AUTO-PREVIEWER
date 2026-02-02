---
name: grab-pr
description: Incrementally fetch closed GitHub PRs (Python-only diffs) into dataset/PR-unprocessed; each run evaluates existing PR IDs and the last fetch timestamp to decide between pulling new updates or backfilling older PRs—no manual backups or directory cleanup required.
---

## Overview
Use this skill to download PR patch records (JSON) from the configured GitHub repo. It tracks a last-fetch timestamp to avoid re-downloading; when no timestamp exists it grabs the latest batch, when one exists it fetches only updates since that time (with a count), and if no updates exist it backfills older PR numbers before the smallest existing record. Runs no longer stop just because `dataset/PR-unprocessed/` already contains files—the timestamp and lowest PR number determine whether to fetch new updates or backfill older history.

## Workflow
1) Trigger via `runner.py`. It reports counts in `dataset/PR-unprocessed/` and `dataset/PR-processed/`, then always invokes `scripts/grab_pr.py`, so reruns reuse existing data without backup/cleanup steps.
2) `grab_pr.py` uses config-driven settings (owner, repo, token, batch size, grab_max_records) to pull closed PRs from GitHub, collect Python file patches (context merged like `initialize.py`), and write JSONs to `dataset/PR-unprocessed/`. It maintains `dataset/grab_pr_state.json` with a last-fetch timestamp:
   - No timestamp: `fetch_latest` grabs the newest closed PRs until reaching `grab_max_records`.
   - Timestamp present: `fetch_updated_since` only downloads PRs whose `updated_at` is newer than the saved timestamp.
   - If no newer PRs exist: `backfill_before` starts from the smallest recorded PR number minus one and walks backward to fill historical gaps.
3) During every run it aggregates existing PR numbers from both processed/unprocessed folders to avoid regenerating JSON files, and updates `grab_pr_state.json` to the current timestamp once work completes.
4) JSON shape matches initialize output (pr_number/title/author/reason/python_diffs with merged patch text). No non-Python files are stored.

## Notes
- Respects `config.py` paths and batch settings (`initialize_per_page`, `grab_max_records`).  
- Network calls rely on the configured token if present; unauthenticated mode sleeps between pages to avoid rate limits.
- Do not reprocess or move files here; downstream skills handle processing.
