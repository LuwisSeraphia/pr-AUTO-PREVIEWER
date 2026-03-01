import copy
import json
from pathlib import Path


DEFAULT_CONFIG = {
    "github": {
        "owner": "python-attrs",
        "repo": "attrs",
        "token": "...",
        "token_env": "GITHUB_TOKEN",
        "user_agent": "python-attrs-pr-scraper",
    },
    "paths": {
        "project_root": ".",
        "dataset_dir": "dataset",
        "pr_records": "dataset/PR-processed",
        "new_pr": "dataset/PR-unprocessed",
    },
    "batch": {
        "initialize_per_page": 20,
        "grab_max_records": 50,
        "search_batch_size": 50,
        "search_sleep_seconds": 2,
    },
}


def _merge(base: dict, override: dict):
    for key, val in override.items():
        if key.startswith("_"):
            continue  # ignore inline comments in config.json
        if isinstance(val, dict) and isinstance(base.get(key), dict):
            _merge(base[key], val)
        else:
            base[key] = val



def load_config() -> dict:
    """Load config.json and merge with defaults, resolving paths to absolute."""
    cfg = copy.deepcopy(DEFAULT_CONFIG)
    root = Path(__file__).resolve().parent
    cfg_path = root / "config.json"
    if cfg_path.exists():
        data = json.loads(cfg_path.read_text(encoding="utf-8"))
        _merge(cfg, data)

    project_root = Path(cfg["paths"].get("project_root", "."))
    if not project_root.is_absolute():
        project_root = (root / project_root).resolve()
    cfg["paths"]["project_root"] = str(project_root)

    for key in ("dataset_dir", "pr_records", "new_pr"):
        raw = Path(cfg["paths"].get(key, ""))
        if not raw.is_absolute():
            raw = project_root / raw
        cfg["paths"][key] = str(raw.resolve())

    return cfg
