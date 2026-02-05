---
name: preview
description: Review given pr records against existing rules in rules.md, surface issues with exact rule references and severities, and output a README-formatted report using report_template.md.
---

# Preview Skill

Use this skill to evaluate local, uncommitted changes from `git diff` with enriched context (file path, enclosing function/class when available, and surrounding code) against the current English ruleset and produce a README-formatted report. Do not assume single lines carry full semantics—judgments must use context + diff. When context cannot be resolved, call it out and lower confidence.

## Inputs
- Raw `git diff` output (uncommitted local changes; include file paths and hunks). Collect enclosing scope and a small before/after window per hunk when possible.
- Authoritative rules: `rules.md` (English; do not modify).
- Template reference: `report_template.md` in this skill folder.

## What to read from the diff
- File paths and hunks from the raw `git diff`.
- Python files only; ignore non-Python diffs.
- Enclosing function/class for each hunk when it can be derived, plus surrounding context lines; if unavailable, mark the hunk as context-missing and carry through `missing_reason` (e.g., `network_timeout`).

## Workflow
1) Load `rules.md` and keep category/subcategory order intact for referencing rule numbers (use 1-based numbering within each subcategory as they appear).
2) Parse the provided raw `git diff`, considering only Python file hunks, and attempt to enrich each with enclosing scope + before/after context. If context is missing, note the limitation in findings.
3) For each Python diff hunk, assess compliance with `rules.md`:
   - If a change violates a rule, record the exact rule (category, subcategory, rule number, title) and its severity (MUST/SHOULD/MAY) from `rules.md`.
   - Base conclusions on the enriched context + diff, not on single-line patterns.
   - Do not invent issues; if clean, note the absence of findings.
   - Provide concrete suggestions tied to the observed diff (e.g., required action to comply with the rule).
4) Populate a report following `report_template.md` into a README-style output (named `README.md` in the working directory or returned as content). Include:
   - File path and status (`clean` or `issues-found`).
   - Summary (concise).
   - Findings list with `[SEVERITY] Rule "<title>" (Category > Subcategory, rule #n)` plus description, location, suggestion, and `(ref <file path>)`.
   - If context is missing for a hunk, explicitly warn that results may be low-confidence for that section (e.g., “该文件上下文获取失败，当前判断可能不准确”).
   - Additional Notes (omit if empty).
5) Do **not** edit `rules.md`, or other rule files in this skill.

## Severity and Referencing
- Use the severity specified in the matched rule (do not downgrade/upgrade).
- Rule numbering: count rules as they appear within their subcategory (1-based). If unclear, reference by title and severity.
- Always include the PR filename in `(ref ...)` for each finding.

## Output
- A README-formatted report using `report_template.md`. If no issues, set `Status: clean` and leave Findings empty except for a note that no issues were found.

## Quality Checks
- No non-Python diffs considered.
- Findings map directly to existing `rules.md` entries; no fabricated rules.
- Suggestions are actionable and specific to the observed diffs and their context.
- Warn explicitly when context is missing; do not claim high confidence without it.
- Keep wording and tone consistent with the template; avoid stylistic drift.
