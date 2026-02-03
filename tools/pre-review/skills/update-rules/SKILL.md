---
name: update-rules
description: Keeps `rules.md` current by fetching incremental PRs via grab-pr and piping them through form-rules to fold new evidence into the English ruleset. Trigger whenever a request mentions refreshing, regenerating, or updating rules/best practices with recent PRs.
---

# Update Rules Skill

Use this skill to keep `rules.md` up to date when new PR JSON records appear in `dataset/PR-unprocessed/`. Any instruction like “refresh the rules,” “regenerate best practices,” or “update guidance with recent PRs” should map here automatically. It is fully integrated: the runner first invokes the grab-pr fetcher (non-interactively) to ensure PR inputs are fresh, then hands those JSON batches to the same form-rules pipeline used during initialization. Records now contain structured hunks with line numbers, enclosing function/class, and before/after context; rules must be evaluated on this context rather than isolated lines. Only the English ruleset is updated.

## Inputs

- Template: `rule_template.md` (format, headings, tone).
- New PR data: every `*.json` under `dataset/PR-unprocessed/` (with `python_diffs` that include `raw_patch`, structured hunks, enclosing scope, and surrounding context).
- Existing corpus (for movement only): `dataset/PR-processed/` (do not reprocess files already here).

## What to read from each PR JSON
- `reason.description`
- `reason.commit_messages`
- `python_diffs` (Python files only; skip non-Python diffs entirely). Each diff provides file path, raw patch, structured hunks with line numbers/kinds, enclosing function/class (if resolvable), and before/after context. If context is missing (`context_missing=True` with `missing_reason` such as `network_timeout`), treat conclusions as low confidence and note the gap.

## Rule generation requirements (align with initialize)
- Keep rules mid-level, project-oriented, and conceptual: avoid library/framework/runtime/version names, concrete identifiers, and string literals; derive guidance from behavior and scope, not isolated lines or function-level specifics.
- Enforce the abstraction gate: hard-reject candidates tied to a single function/class/implementation path or unique API shape; require cross-module or multi-scenario applicability and contextual support from call flows, boundaries, defaults, validation order, and error semantics.
- Use contextual anchors from surrounding code (interfaces, data/default propagation, validation-before-mutation, compatibility/fallbacks, docs/version markers, and testing intent) as evidence; never rely on single-line triggers.
- Draft rules only when supported by aggregated patterns; keep them single-purpose and formatted per `rule_template.md`, with scenario + required/recommended behavior + engineering rationale, and severity set to MUST/SHOULD/MAY without weakening existing levels.

## Workflow
0) Refresh PR inputs: first check `dataset/PR-unprocessed/` for existing `*.json`. If present, use them directly (runner now reports the latest sequence id) and skip fetching. If the folder is empty, run `python tools/pre-review/skills/update-rules/runner.py` (calls `tools/pre-review/skills/update-rules/scripts/grapNew.py`) to fetch the latest Python PRs; it auto-backfills when none are new and prints when nothing needs updating.
1) Collect files: list all JSON files in `dataset/PR-unprocessed/` after the fetch. If none exist, stop—there is nothing to update.
2) Process files in explicit batches (10 files per batch, max 5 batches per invocation—stop cleanly at the limit and leave remaining files for the next run) to mirror initialize; for each batch:
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
   - Move the processed JSON from `dataset/PR-unprocessed/` to `dataset/PR-processed/` after updating rules (even if no rule change was needed).
   - Emit a batch log (`dialog/rule-log-00x.md`, using `templates/rulelog_template.md`) that reflects only the rules added/changed/removed in this batch; do not backfill or rewrite history from earlier batches or prior invocations.

## Writing & Editing Rules
- Keep rules single-purpose, code-level, and generalized (never PR-specific).
- Do not include non-Python diffs or references.
- Do not duplicate existing rules semantically.
- Do not alter severity without solid justification from the new PR.
- Keep category and subcategory titles as-is unless a genuinely new subcategory is necessary.
- Restrict edits to rules affected by the current invocation’s batches; do not reprocess or reinterpret historical batches/logs.

## Output
- Updated `rules.md` (English only) reflecting only rules touched in the current invocation. Bilingual output is optional; if produced, do not alter rule structure, refs, or severities.
- Per-batch `dialog/rule-log-00x.md` entries for the batches processed in this invocation only.

## Post-processing
- Ensure each processed PR JSON is relocated to `dataset/PR-processed/` to avoid reprocessing.

## Quality Checks
- `rules.md` remains aligned with `rule_template.md`.
- Each ref list uses real JSON filenames, sorted, ≤5 entries.
- No non-Python content introduced.
- No stylistic drift: maintain existing wording patterns and heading order.
