---
name: form-rules
description: Generate and append mid-level English coding rules from existing PR JSONs in dataset/PR-unprocessed, mirroring initialize’s rule-creation guidance (no fetching).
---

## Overview
Use this skill when PR records already exist in `dataset/PR-unprocessed/` and you need to derive/update `rules.md` without fetching new data. It mirrors initialize’s rule-generation pipeline: mid-level, project-oriented rules only, with strict abstraction/rejection gates and batch limits.

## Inputs
- Source PR JSONs: `dataset/PR-unprocessed/*.json` (Python diffs only; skip non-Python).
- Templates/references: `templates/rule_template.md`, `templates/rulelog_template.md`, `templates/rule_ref.md`.
- Existing rules: `rules.md`.
- Output logs: `dialog/rule-log-00x.md`.

## Batch workflow (same as initialize, minus fetching)
1) Discover inputs: list `dataset/PR-unprocessed/*.json`. If none, stop (nothing to form).
2) Process in fixed batches: 10 files per batch, at most 5 batches per invocation (50 JSONs total). Stop cleanly at the limit; leave remaining files for the next run. Each batch must fit token limits (summaries allowed; no skipping).
3) Per-PR analysis (Python diffs only):
   - Derive signals from context and diffs together (enclosing scope, surrounding lines); avoid single-line triggers.
   - Summarize evidence into **behavioral patterns**, **design intent**, **engineering trade-offs**.
4) Abstraction & rejection gate (initialize rules):
   - Hard-reject candidates tied to a single function/class/implementation path or unique API shape; require cross-module or multi-scenario applicability.
   - Keep mid-level, project-oriented guidance: avoid library/framework/runtime names, concrete identifiers, string literals, or implementation recipes.
   - Favor behavior-driven constraints: interface contracts, defaults/propagation, validation-before-mutation, error semantics/rationales, fallback/compatibility, testing intent, docs/version markers. Secondary hints (signatures, exception classes, syntax) are evidence only.
5) Clustering (category → subcategory):
   - API & default behavior
   - Error handling & validation order
   - Test design & coverage strategy
   - Documentation & version management
   - Compatibility & fallback strategy
   Keep rules single-purpose and generalizable; reject anything that cannot stand outside the originating change.
6) Severity (unchanged from initialize):
   - MUST: functional errors/compatibility breaks/severe maintainability risk
   - SHOULD: strongly recommended, clear long-term value
   - MAY: optional optimizations/guidance
   Use NOT/SHOULD NOT/MUST NOT for prohibitions; do not weaken existing severities without evidence.
7) Rule drafting (strictly follow `rule_template.md`):
   - Format: `[LEVEL] Title: Description (ref PR xxxx.json, …)` with ≤5 refs, numeric sorted.
   - Description includes scenario + required/recommended behavior + engineering rationale.
   - One rule per concern; conceptual terms only (e.g., “constructor parameters”, “field metadata”, “compatibility guards”, “shared test configuration”).
   - Require contextual support; avoid single-line triggers; no implementation-path prescriptions.
8) Editing outputs:
   - Append/merge into `rules.md`; modify existing rules only on direct conflict, never dilute.
   - Emit `dialog/rule-log-00x.md` for each batch per `rulelog_template.md` (++, --, ~). Produce a log even if no rules changed.
   - Move processed JSONs to `dataset/PR-processed/` after each batch (historical store).

## Quality checks
- Rules remain actionable, mid-level, single-purpose, and project-oriented; no library/version/identifier leakage.
- Abstraction gate enforced; non-generalizable or implementation-specific candidates are dropped.
- Category structure preserved; new subcategories only if necessary.
- Ref lists real filenames, sorted, ≤5; English-only rules.
- Batch reproducibility: follow batch limits; do not reprocess prior batches/logs.
