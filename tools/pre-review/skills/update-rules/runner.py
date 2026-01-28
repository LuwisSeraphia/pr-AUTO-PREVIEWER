import subprocess
import sys
from pathlib import Path


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
ROOT = Path(CFG["paths"]["project_root"])
SKILL_DIR = Path(__file__).resolve().parent
GRAP_NEW = SKILL_DIR / "scripts" / "grapNew.py"
NEW_PR_DIR = Path(CFG["paths"]["new_pr"])


def snapshot_new_pr_files():
    if not NEW_PR_DIR.exists():
        return set()
    return {p.name for p in NEW_PR_DIR.glob("*.json")}


def latest_pr_number(filenames):
    """Return the highest numeric PR id from filenames like 1234.json."""
    numbers = []
    for name in filenames:
        stem = name.rsplit(".", 1)[0]
        if stem.isdigit():
            numbers.append(int(stem))
    return max(numbers) if numbers else None


def run_grap_new():
    print(f"\n$ {sys.executable} {GRAP_NEW}")
    result = subprocess.run([sys.executable, str(GRAP_NEW)], cwd=ROOT)
    return result.returncode


def main():
    existing = snapshot_new_pr_files()
    if existing:
        latest = latest_pr_number(existing)
        latest_label = str(latest) if latest is not None else sorted(existing)[-1]
        print(
            f"Existing newPR files detected ({len(existing)}). "
            f"Using them for updates; latest sequence: {latest_label}."
        )
        print(f"Current newPR file count: {len(existing)}")
        return 0

    before = existing
    code = run_grap_new()
    if code != 0:
        print(f"grapNew exited with code {code}")
        return code

    after = snapshot_new_pr_files()
    new_files = sorted(after - before)
    total = len(after)

    if new_files:
        print(f"New PR record files: {', '.join(new_files)}")
    elif total == 0:
        print("No need to update: No PR records exist after running grapNew.")
    else:
        print("No new PR files generated in this run.")

    print(f"Current newPR file count: {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
