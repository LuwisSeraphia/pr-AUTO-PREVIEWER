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
SCRIPT = Path(__file__).resolve().parent / "scripts" / "initialize.py"


def main():
    cmd = [sys.executable, str(SCRIPT)]
    print(f"$ {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=ROOT)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
