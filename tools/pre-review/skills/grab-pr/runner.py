import sys
from pathlib import Path
from scripts import grab_pr

from config import load_config


CFG = load_config()
ROOT = Path(CFG["paths"]["project_root"])
NEW_PR_DIR = Path(CFG["paths"]["new_pr"])
PROCESSED_DIR = Path(CFG["paths"]["pr_records"])


def snapshot_unprocessed():
    if not NEW_PR_DIR.exists():
        return set()
    return {p.name for p in NEW_PR_DIR.glob("*.json")}


def latest_label(filenames):
    numbers = []
    for name in filenames:
        stem = name.rsplit(".", 1)[0]
        if stem.isdigit():
            numbers.append(int(stem))
    if numbers:
        return str(max(numbers))
    return max(filenames) if filenames else "none"


def main():
    existing = snapshot_unprocessed()
    processed_count = 0
    if PROCESSED_DIR.exists():
        processed_count = sum(1 for _ in PROCESSED_DIR.glob("*.json"))

    if existing:
        print(
            f"PR-unprocessed already has {len(existing)} file(s). "
            f"Latest sequence: {latest_label(existing)}. Fetching additional updates/backfill."
        )
    elif processed_count:
        print(
            f"PR-unprocessed is empty but PR-processed already has {processed_count} file(s). "
            "Checking for updates/backfill based on last timestamp."
        )
    else:
        print("No existing PR data detected. Fetching initial batch.")

    before = set(existing)
    print("\nCalling grab_pr.main() directly...")
    grab_pr.main()

    after = snapshot_unprocessed()
    new_files = sorted(after - before)

    if new_files:
        print(f"Fetched PR records: {', '.join(new_files)}")
    elif after:
        print("Fetch completed but no new PR files were added.")
    else:
        print("No PR records fetched.")

    print(f"Current PR-unprocessed file count: {len(after)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
