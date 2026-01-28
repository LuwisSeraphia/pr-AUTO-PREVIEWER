# Environment

Minimum setup to run the AUTO previewer tools:

- Python: 3.11+ (uses stdlib only: `json`, `urllib`, `pathlib`, `subprocess`, `datetime`, `time`, `random`, etc.).
- Git: required for `git diff` input to the preview skill (local uncommitted changes).
- Shell utilities: standard Unix shell (bash/zsh) to run the scripts.
- GitHub token: export `GITHUB_TOKEN` (or the name set in `config.json` under `github.token_env`) for API calls in `tools/pre-review/skills/Initialize/scripts/initialize.py` and related scripts.

No third-party Python packages are required beyond the standard library.
