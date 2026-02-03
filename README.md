# AUTO previewer

AUTO previewer is a PR pre-review toolkit for Python repositories. It mines historical PRs, turns them into mid-tier review rules, and uses those rules to pre-screen new diffs. Everything runs locally with token-aware GitHub calls; you never have to clone the target repo.

---

## Architecture & Data Flow
AUTO previewer exposes five skills that cooperate to keep PR-derived rules in sync with local reviews:
- **Foundational skills**:  
  1. `grab-pr` harvests closed PRs, normalizes the Python-only diffs, and stages JSON in `dataset/PR-unprocessed/`.  
  2. `form-rules` consumes those JSON files to author/update `rules.md`, emit dialog logs, and archive processed PRs—this step is guided directly by the skill instructions (no runner or script to execute).
- **Functional skills** (built on the foundation):  
  3. `Initialize` orchestrates **grab-pr → form-rules** to bootstrap a fresh ruleset (deprecated—keep for reference only).  
  4. `update-rules` reuses the same chain for incremental refreshes (deprecated).  
  5. `preview` compares local diffs to the generated rules and renders a report.

The pipeline therefore looks like:
1. **PR harvesting (`grab-pr`)** populates `dataset/PR-unprocessed/`.
2. **Rule formation (`form-rules`)** converts batches of JSON into categorized MUST/SHOULD/MAY rules in `rules.md`, logging each batch and moving JSON to `dataset/PR-processed/`.
3. **Composite automation (`Initialize` / `update-rules`)** repeatedly runs steps 1–2 until the batch limits are satisfied.
4. **Local preview (`preview`)** inspects `git diff` against `rules.md`, generating a report with rule hits and suggestions.

Processed/unprocessed datasets stay synchronized automatically through this loop.

---

## Directory Map
```
.
├─ AGENTS.md                 # High-level behavior and reporting contract
├─ README.md                 # This document
├─ config.json               # Editable source-of-truth for repo + batch settings
├─ config.py                 # Loader/normalizer that merges defaults
├─ env.md                    # Runtime prerequisites (Python, git, tokens)
├─ dataset/
│  ├─ PR-unprocessed/        # Newly harvested PR JSON (Python diffs only)
│  ├─ PR-processed/          # Historical PR JSON that already fed rule-gen
│  └─ grab_pr_state.json     # Timestamp for incremental PR fetching
├─ dialog/                   # Batch rule logs (one per initialize/update run)
├─ rules.md                  # Generated review rules (empty until populated)
├─ templates/
│  ├─ report_template.md     # preview output structure
│  ├─ rule_template.md       # section layout for rules.md
│  ├─ rulelog_template.md    # per-batch log template
│  └─ rule_ref.md            # baseline references
└─ tools/pre-review/skills/
   ├─ grab-pr/               # PR harvesting skill (runner + scripts)
   ├─ form-rules/            # Rule formation skill (no fetching)
   ├─ Initialize/            # Composite skill: grab-pr + form-rules bootstrap
   ├─ update-rules/          # Composite skill: grab-pr + form-rules refresh
   ├─ preview/               # Local diff review
   ├─ skill-creator/         # Authoring guide for new skills
   └─ skill-installer/       # Installation helper for external skills
```

---

## Environment & Configuration
- Set `github.owner`, `github.repo`, and batching limits in `config.json`. `config.py` resolves relative paths and merges defaults; import it wherever configs are required.
- Provide a GitHub token through `github.token` or an environment variable (default `GITHUB_TOKEN`):
  ```bash
  export GITHUB_TOKEN=ghp_xxx   # only needed if config.json references token_env
  ```
- Python 3.8+ is required. Core dependencies are all from the standard library plus `pytest` and `hypothesis` for the test suite.

---

## Skills & Their Logic
AUTO previewer includes five skills: two **foundational** (atomic) capabilities—`grab-pr` and `form-rules`—plus three **functional** skills (`Initialize`, `update-rules`, `preview`) that build on top. Start by understanding the atomic skills; the higher-level ones simply automate their coordination.

### Foundational skills (atomic building blocks)
These run independently and define all data entering or exiting the rule pipeline.

#### grab-pr
- **Purpose:** Populate or refresh `dataset/PR-unprocessed/` with Python-only PR diffs.
- **Execution path:** `tools/pre-review/skills/grab-pr/runner.py` → `scripts/grab_pr.py`.
- **Flow:**
  1. Runner inspects `dataset/PR-unprocessed/`/`PR-processed/`, reports current counts, and always calls the fetcher (no manual cleanup needed).
  2. Fetcher loads config plus `dataset/grab_pr_state.json` for the last timestamp, then determines the strategy:
     - **Initial run (no timestamp):** pull latest closed PRs (up to `grab_max_records`).
     - **Incremental run:** fetch only PRs updated after the stored timestamp.
     - **Backfill:** if nothing new, walk backwards from the smallest known PR ID to fill historical gaps.
  3. Records are written only when at least one `.py` diff exists; duplicates are suppressed using the combined ID set from processed + unprocessed folders.
  4. Timestamp is updated after every run so the next fetch knows whether to look forward or backfill.

#### form-rules
- **Purpose:** Transform existing PR JSONs into mid-level rules without contacting GitHub.
- **Execution path:** Manual per the instructions in `tools/pre-review/skills/form-rules/SKILL.md` (there is intentionally no runner or script; the agent follows the documented workflow directly).
- **Flow:**
  1. Scan `dataset/PR-unprocessed/`; stop if empty.
  2. Process in strict batches of 10 files (up to 5 batches/run). Each batch runs the abstraction pipeline from `SKILL.md`: gather behavioral signals, reject implementation-specific findings, and cluster into categories/subcategories defined by `rule_template.md`.
  3. Append or update rules in `rules.md`, emit a batch log in `dialog/rule-log-00x.md`, and move the batch’s JSON to `dataset/PR-processed/`.
  4. Reference lists are capped at five PR IDs, severity tags must be MUST/SHOULD/MAY, and prose stays identifier-agnostic.

### Functional skills (automation built on the foundation)
These skills wire the atomic capabilities together (and optionally add reporting).

#### initialize (deprecated)
- **Role:** Historically bootstrapped the entire system by chaining **grab-pr → form-rules** until initial rules exist.
- **Behavior:** When invoked, it first ensures fresh PR data via grab-pr (if needed), then runs the form-rules batching pipeline. Prefer running `grab-pr` and manual `form-rules` steps directly; this runner remains only for backwards compatibility.

#### update-rules (deprecated)
- **Role:** Historically kept the ruleset current using the same composite chain (**grab-pr → form-rules**) but assumed a baseline already existed.
- **Behavior:** Pulls new/backfilled PRs, then immediately processes them with the form-rules batching workflow. Prefer invoking `grab-pr` followed by manual `form-rules`; this runner remains only so older automation continues working.

#### preview
- **Role:** Final-mile verification that compares local work to the current ruleset before a PR is opened.
- **Behavior:** Reads `rules.md`, runs `git diff --unified` (or accepts a provided diff), evaluates each hunk against the rules, and renders a markdown report via `templates/report_template.md` listing rule hits/violations plus remediation hints. Designed for developer-side pre-review before pushing changes.

### skill-creator & skill-installer
- Provide instructions and helpers for extending this toolkit. Use them when you need to add a new workflow or install a curated skill set.

---

## Typical Workflow
1. **Configure once:** edit `config.json`, set your token, and verify paths under `config.py`.
2. **Harvest PR data:**
   ```bash
   python tools/pre-review/skills/grab-pr/runner.py
   ```
   This populates/refreshes `dataset/PR-unprocessed/` without touching existing files.
3. **Generate or refresh rules:**
   - First run (needs both fetch + formation): preferred flow is to run `grab-pr`, then execute the manual `form-rules` workflow; the legacy `Initialize` runner still exists but is deprecated.
   - Incremental updates: same as above—run `grab-pr` if new data is needed, then follow the manual `form-rules` batching process. The legacy `update-rules` runner is deprecated.
   - Form-only pass: follow the `form-rules` skill manually (no runner exists)—apply the batching workflow described in `tools/pre-review/skills/form-rules/SKILL.md`.
   All options enforce the 10×5 batch limits, move processed JSONs to `PR-processed`, and emit `dialog/rule-log-00x.md`.


---

## Run Tips
- Keep `dataset/PR-unprocessed/` small by running `initialize`/`update-rules` soon after each `grab-pr` run; otherwise later batches will take longer.
- If you need to reprocess older PRs, rerun `grab-pr`; it automatically determines whether to fetch newer updates or backfill historical IDs.
- `rules.md` starts empty—run `initialize` at least once before using `preview`.
- Each rule batch writes a dialog log in `dialog/`; these logs are helpful for auditing what rules were added or modified.

With config and token in place, you can loop through harvest → rule update → preview to keep the rules relevant and catch regressions before opening a PR.
