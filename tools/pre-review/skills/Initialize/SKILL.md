---
name: initialize
description: Generate fine-grained, actionable coding rules from PR JSON records (Python diffs with surrounding context and enclosing scopes), with strict MUST/SHOULD/MAY levels.
---

## Example

- Command: "Generate coding rules from PR JSON files in dataset/PR_records"
- Expected behavior: If `dataset/PR_records/` already contains JSON files, load them directly and produce `rules.md` (no fetch/approval). Only when the folder is empty, call `python tools/pre-review/skills/Initialize/runner.py` (loads config and executes `scripts/initialize.py` to fetch PR records).

# initialize skill

Use this skill to read `dataset/PR_records/*.json`, extract patterns from Python diffs/bodies/commits (with surrounding context and enclosing function/class info), and produce leveled coding rules in English. Rules must be specific, single-purpose, and numerous enough to cover each category robustly. Do **not** design rules that trigger on a single-line pattern without considering the enclosing scope and local context.

## Quick Workflow
1) Load all `.json` files under `dataset/PR_records/`.If there are no files in the folder, run `runner.py` of this skill to fetch PRs; if files already exist, load them directly and prepare to generate rules.
2) For each PR, keep `reason.description`, `reason.commit_messages`, and `python_diffs` (only `.py` files). Each `python_diffs` entry includes `raw_patch`, structured `hunks` with line numbers/kinds, enclosing scope, and before/after context. Rules should be judged on context + diff, not on isolated lines except they are simple or not related.
3) Aggregate signals (extend as needed; do not drop meaningful terms):
   - Terms: kw_only/force_kw_only/default/signature/order/init
   - Validation: None/typeerror/valueerror/assert/raise/invalid/conflict
   - Testing: pytest/raises/assert/test files
   - Docs: versionadded/versionchanged/changelog/docstring/example
   - Typing: annotation/Optional/Literal/Union/Protocol/overload/pyi/re-export
   - Compatibility: flag/toggle/legacy/backward/deprecated/fallback
4) Cluster signals into categories → subcategories (API & Defaults; Error Handling & Validation; Testing; Documentation & Versioning; Typing & Signatures; Compatibility & Flags). Each category must end up with ≥5 rules; if signals are sparse, split subcategories or narrow rule angles rather than reducing rule counts.
5) Assign necessity levels strictly:
   - MUST: Violations cause functional bugs, compatibility breaks, or severe maintainability risks.
   - SHOULD: Strongly recommended; clear long-term value but not immediately breaking.
   - MAY: Optional optimizations or stylistic guidance.
   Use NOT/SHOULD NOT/MUST NOT for prohibitions; do not inflate or deflate severity without evidence.
6) Draft rules (one concrete engineering norm per rule):
   - Format: `[LEVEL] Title: Description (ref PR xxxx.json, ...)`
   - Description must include: (a) applicable scenario, (b) the precise required/encouraged action, (c) the engineering rationale (maintainability/compatibility/readability/error defense/etc.).
   - Avoid merged or vague rules; keep each rule single-purpose and code-level.
   - Do **not** rely on single-line string/pattern matches; require surrounding context and scope to support the rule.
   - At most 10 refs, sorted, comma-separated, and only when the PR content genuinely supports the rule.
   - Keep small subcategories (≤10 rules per subcategory).
   - **Follow `rule_template.md` strictly for structure, style, and phrasing.**
7) Output:
   - `rules.md`: English, grouped by category → subcategory with headings.

## Prompting Hints (if using an LLM inline)
- Provide the model with aggregated snippets (not whole files) to stay within context.
- Include the required output structure and ref limits in the prompt.
- Ask the model to drop rules with zero supporting refs.

## Quality Checks
- Rules are actionable, single-purpose, and code-specific (not PR-specific or vague).
- Each category has ≥5 rules; refine subcategories or angles to meet the quota without padding.
- Levels follow the strict MUST/SHOULD/MAY criteria above; prohibitions are prefixed correctly.
- Descriptions state scenario, required action, and rationale explicitly.
- No non-Python diffs included.
- References are real,  sorted numeric.
- Generated rules follow `rule_template.md` structure, headings, and formatting exactly.
