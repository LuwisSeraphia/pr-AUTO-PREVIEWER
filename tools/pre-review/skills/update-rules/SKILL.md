---
name: update-rules
description: Incrementally update the English coding rules in rules.md using context-enriched PR JSON records from dataset/newPR by merging refs into existing rules or drafting new rules per rule_template.md, then moving processed PR files into dataset/PR_records.
---

# Update Rules Skill

Use this skill to keep `rules.md` up to date when new PR JSON records appear in `dataset/newPR/`. Records now contain structured hunks with line numbers, enclosing function/class, and before/after context; rules must be evaluated on this context rather than isolated lines. Only the English ruleset is updated. The runner now drives a non-interactive `grapNew` fetch step before reviewing PR records.

## Inputs
- Authoritative rules: `rules.md` (English; preserve structure and ordering).
- Template: `rule_template.md` (format, headings, tone).
- New PR data: every `*.json` under `dataset/newPR/` (with `python_diffs` that include `raw_patch`, structured hunks, enclosing scope, and surrounding context).
- Existing corpus (for movement only): `dataset/PR_records/` (do not reprocess files already here).

## What to read from each PR JSON
- `reason.description`
- `reason.commit_messages`
- `python_diffs` (Python files only; skip non-Python diffs entirely). Each diff provides file path, raw patch, structured hunks with line numbers/kinds, enclosing function/class (if resolvable), and before/after context. If context is missing (`context_missing=True` with `missing_reason` such as `network_timeout`), treat conclusions as low confidence and note the gap.

## Workflow
0) Refresh PR inputs: first check `dataset/newPR/` for existing `*.json`. If present, use them directly (runner now reports the latest sequence id) and skip fetching. If the folder is empty, run `python tools/pre-review/skills/update-rules/runner.py` (calls `tools/pre-review/skills/update-rules/scripts/grapNew.py`) to fetch the latest Python PRs; it auto-backfills when none are new and prints when nothing needs updating.
1) Collect files: list all JSON files in `dataset/newPR/` after the fetch. If none exist, stop—there is nothing to update.
2) For each file (process independently):
   - Load the three allowed fields above, using the provided context (enclosing scope + before/after snippets) when assessing rule alignment.
   - Derive signals from Python diffs only; ignore non-Python changes.
   - Determine mapping:
     - Case A (matches existing rule): find the most relevant existing rule in `rules.md`. Add the PR filename to that rule’s `(ref ...)` list (max 5 refs, sorted numerically). Do not rewrite, broaden, or weaken the rule unless required for correctness; avoid single-line pattern rules—require contextual evidence.
     - Case B (new rule): draft a single-purpose rule that:
       * Fits an existing category → subcategory; create a new subcategory only if none fits (avoid new top-level categories unless unavoidable).
       * Uses MUST/SHOULD/MAY severities per current definitions; do not change levels without strong evidence.
       * Follows `rule_template.md` formatting and phrasing exactly.
       * States scenario, required/encouraged action, and engineering rationale.
       * Uses real PR filename(s) in `(ref ...)`, ≤5 refs, numeric sort.
       * Avoids single-line string/pattern triggers; rules must depend on context and scope where applicable.
   - Edit `rules.md` only; preserve existing headings, ordering, and style.
   - Move the processed JSON from `dataset/newPR/` to `dataset/PR_records/` after updating rules (even if no rule change was needed).

## Writing & Editing Rules
- Keep rules single-purpose, code-level, and generalized (never PR-specific).
- Do not include non-Python diffs or references.
- Do not duplicate existing rules semantically.
- Do not alter severity without solid justification from the new PR.
- Keep category and subcategory titles as-is unless a genuinely new subcategory is necessary.

## Output
- Updated `rules.md` (English only). Bilingual output is optional; if produced, do not alter rule structure, refs, or severities.

## Post-processing
- Ensure each processed PR JSON is relocated to `dataset/PR_records/` to avoid reprocessing.

## Quality Checks
- `rules.md` remains aligned with `rule_template.md`.
- Each ref list uses real JSON filenames, sorted, ≤5 entries.
- No non-Python content introduced.
- No stylistic drift: maintain existing wording patterns and heading order.
