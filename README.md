# AUTO previewer

AUTO previewer is a PR pre-review toolkit for Python repositories. It mines historical PRs, turns them into mid-tier review rules, and uses those rules to pre-screen new diffs. Everything runs locally with token-aware GitHub calls; you never have to clone the target repo.

---

## Architecture & Data Flow
AUTO previewer now centers on three operational skills (plus two meta helpers) that keep PR-derived rules aligned with local development:
- `grab-pr` harvests closed PRs, normalizes their Python diffs, and stages JSON in `dataset/PR-unprocessed/`.
- `form-rules` consumes those JSON files to author/update `rules.md`, emit dialog logs, and archive processed PRs—this step is always manual per the skill instructions (no runner to invoke).
- `preview` compares local diffs to the generated rules and renders a report.
- `skill-creator` documents how to design future skills; `skill-installer` installs curated skills. They do not touch datasets directly but round out the tooling story.
- Legacy composites `Initialize` and `update-rules` still exist on disk for reference, yet the recommended flow is to call `grab-pr` and then follow the `form-rules` process directly.

The pipeline therefore looks like:
1. **PR harvesting (`grab-pr`)** populates `dataset/PR-unprocessed/`.
2. **Rule formation (`form-rules`)** converts batches of JSON into categorized MUST/SHOULD/MAY rules in `rules.md`, logging each batch and moving JSON to `dataset/PR-processed/`.
3. **Local preview (`preview`)** inspects `git diff` against `rules.md`, generating a report with rule hits and suggestions.

Processed/unprocessed datasets stay synchronized automatically through `grab-pr` + `form-rules`; repeating those steps is preferred over the deprecated composite runners.

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
   ├─ Initialize/            # *Composite skill: grab-pr + form-rules bootstrap
   ├─ update-rules/          # *Composite skill: grab-pr + form-rules refresh
   ├─ preview/               # Local pr review
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
AUTO previewer currently exposes three operational skills—`grab-pr`, `form-rules`, and `preview`—plus two meta helpers (`skill-creator`, `skill-installer`). The first two control every byte that flows into or out of `rules.md`; `preview` consumes that artifact to review local work. Understanding these atomic skills is enough to run the whole system; composite runners are deprecated.

### grab-pr
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

### form-rules
- **Purpose:** Transform existing PR JSONs into mid-level rules without contacting GitHub.
- **Execution path:** Manual per the instructions in `tools/pre-review/skills/form-rules/SKILL.md` (there is intentionally no runner or script; the agent follows the documented workflow directly).
- **Flow:**
  1. Scan `dataset/PR-unprocessed/`; stop if empty.
  2. Process in strict batches of 10 files (up to 5 batches/run). Each batch runs the abstraction pipeline from `SKILL.md`: gather behavioral signals, reject implementation-specific findings, and cluster into categories/subcategories defined by `rule_template.md`.
  3. Append or update rules in `rules.md`, emit a batch log in `dialog/rule-log-00x.md`, and move the batch’s JSON to `dataset/PR-processed/`.
  4. Reference lists are capped at five PR IDs, severity tags must be MUST/SHOULD/MAY, and prose stays identifier-agnostic.

### preview
- **Role:** Final-mile verification that compares local work to the current ruleset before a PR is opened.
- **Behavior:** Reads `rules.md`, runs `git diff --unified` (or accepts a provided diff), evaluates each hunk against the rules, and renders a markdown report via `templates/report_template.md` listing rule hits/violations plus remediation hints. Designed for developer-side pre-review before pushing changes.

### Meta skills
- **skill-creator:** Reference guide for designing new skills; use it whenever you need bespoke workflows or integrations.
- **skill-installer:** Automates installing curated skills (including private repos) into `$CODEX_HOME/skills`.

### Legacy composite runners
`Initialize` and `update-rules` still live under `tools/pre-review/skills/`, but they only chain `grab-pr → form-rules`. They remain for backward compatibility; new workflows should invoke `grab-pr`, follow the manual `form-rules` batching instructions, and then run `preview` as needed.

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
   - Incremental updates: same as above—run `grab-pr` if new data is needed（state `update` if needed）, then follow the manual `form-rules` batching process. The legacy `update-rules` runner is deprecated.
   - Form-only pass: follow the `form-rules` skill manually (no runner exists)—apply the batching workflow described in `tools/pre-review/skills/form-rules/SKILL.md`.
   All options enforce the 10×5 batch limits, move processed JSONs to `PR-processed`, and emit `dialog/rule-log-00x.md`.


---

## Prompt Engineering Playbook
You rarely need to micromanage individual scripts—Codex understands task-level prompts and dispatches the proper skills automatically. Practical patterns:
- **Batch rule formation:** e.g., type `form rules according to the latest 20 records` and the assistant will harvest counts, follow the `form-rules` batching guide, and move JSONs when done.
- **One-shot refresh & preview:** prompts like `grab the newest PRs, rebuild rules, then preview my current diff` chain `grab-pr → form-rules → preview` without further guidance.
- **Ad-hoc analysis:** requests such as `summarize drift since the last three batches and flag missing rule_refs` make the agent inspect `dialog/` logs and `rules.md`.

When doing prompt design, remember:
- Mention skill names (grab-pr, form-rules, preview) or desired outcomes so the agent triggers the right workflows.
- Provide batch sizes or PR counts inline to control runtime cost.
- Custom institutional heuristics belong in `templates/rule_ref.md`; you can extend that file with your own smells or references, and the assistant will cite them via `rule_ref` when authoring rules.

---

## Run Tips
- Keep `dataset/PR-unprocessed/` small by running the `form-rules` workflow shortly after each `grab-pr`; otherwise later batches will take longer. (If you rely on the legacy composites, trigger them soon after harvesting.)
- If you need to reprocess older PRs, rerun `grab-pr`; it automatically determines whether to fetch newer updates or backfill historical IDs.
- `rules.md` starts empty—complete at least one `grab-pr` + `form-rules` cycle before using `preview`.
- Each rule batch writes a dialog log in `dialog/`; these logs are helpful for auditing what rules were added or modified.


With config and token in place, you can loop through harvest → rule update → preview to keep the rules relevant and catch regressions before opening a PR.


