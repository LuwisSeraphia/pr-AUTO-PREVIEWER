---
name: initialize
description: Runs the full grab-pr plus form-rules pipeline to bootstrap the project’s mid-level ruleset from scratch. Trigger whenever a request asks to bootstrap/initialize rules, start from past PRs end-to-end, or otherwise derive guidance in one go.
---

## Overview
This skill drives the full bootstrap loop automatically: it invokes the grab-pr fetcher when fresh PR data is needed, feeds the resulting JSON batches into the form-rules pipeline, and writes both `rules.md` and the per-batch dialog logs. Any fuzzy request like “bootstrap/initialize project rules,” “derive guidance from earlier PRs,” or “start from scratch with rules” should route here, since it guarantees the grab-pr → form-rules chain runs without further prompts. Once PR records exist locally, it continues directly with form-rules to extract signals from Python diffs and surrounding context, incrementally generating tiered coding rules in English.  
Generated rules are **project-oriented and mid-level**: they avoid project/tool/version-specific details (no library names, runtime versions, framework labels), avoid concrete identifiers or string literals, and stay conceptual. Rules must be derived from contextual behavior and scope rather than single-line patterns, pass a read → abstract → qualify pipeline, and reject any function-level or implementation-specific notes that cannot generalize across modules or scenarios.

## Example
- **Command:** “Generate coding rules from PR JSON files in `dataset/PR-unprocessed`.”
- **Expected behavior:**  
  If `dataset/PR-unprocessed/` already contains JSON files, load them directly and generate/update `rules.md` without fetching or approval.  
  Only when the folder is empty should the skill invoke `tools/pre-review/skills/Initialize/runner.py` (load config and run `scripts/initialize.py`) to fetch PR records remotely, then process them in batches.

## Inputs (for candidate rule generation)
- **Baseline reference:**  
  Load links from `templates/rule_ref.md` and combine common style guides to form mid-level guidance on module boundaries, API behavior, error semantics, validation order, and test depth. Exclude lint-level syntax checks.
- **Project conventions:**  
  For each PR diff, mine repeated cross-file and cross-commit patterns (e.g., initialization/default propagation order, validation-before-mutation, error semantics, test fixture design, documentation/version markers) and merge them with the baseline into mid-level guidance.
- **Context anchors:**  
  Bind candidate rules to scope and nearby call flows (function/class/module boundaries, control paths) so rules are behavior-driven, not isolated token matches.
- **Abstraction guardrails:**  
  Rules should be neither too generic nor too specific; favor mid-level principles (interface contracts, validation sequencing, fallback/compatibility paths, documentation requirements). Before drafting, condense signals into behavioral patterns, design intent, and engineering trade-offs that can span modules or features. Discard anything tied to a single function/class/component, any implicit implementation path, or patterns that reveal specific API shapes.

## Workflow
1. **Input readiness:**  
   If PR fetching is needed, use `runner.py` to download into `dataset/PR-unprocessed/`.  
   Process in fixed batches: 10 files per batch, at most 5 batches per invocation (50 JSONs total).  after reaching batch limit（50 json files），Stop cleanly at the batch limit, leave remaining files for the next run.  
   Each batch must fit within token limits (summarization allowed; skipping is not).  
   After each batch, append new rules to `rules.md` (modify existing rules only on conflict), then move processed files to `dataset/PR-processed/`, which is retained as a historical signal store.
2. **Per-PR analysis:**  
   Derive signals from context and diffs, not isolated lines (unless trivial or irrelevant); no rule drafting occurs before abstraction.
3. **Pre-abstraction & Rule Rejection Gate:**  
   - Summarize evidence into three buckets: **behavioral patterns** (observable flows and contracts), **design intent** (stated goals/constraints), and **engineering trade-offs** (explicit compromises or priority choices).  
   - Hard-reject candidates that stay tied to a single function/method, identifier, or implementation detail—even if well-supported.  
   - Keep only patterns that plausibly apply across multiple modules, components, or scenarios; discard function-level/class-level/implementation-path-specific observations.  
   - **Drop candidate rules** outright when any of the following hold: the abstraction still maps to a single mechanism or component; it reveals a unique API shape or internal structure; it prescribes a specific implementation path rather than an engineering constraint; it cannot stand outside the current PR scenario.
4. **Signal aggregation (prioritize mid-level behavior):**
   - **Interfaces & flow:** module interfaces, responsibilities, call order, data/default propagation, boundary conditions.
   - **Error handling:** guards, validation-before-mutation, error semantics (as rationale), recovery paths.
   - **Testing intent:** coverage goals, scenarios, parameterization scope, fixtures/cases; syntax details are contextual only.
   - **Documentation signals:** docstrings, versionadded/versionchanged/deprecated notes, changelogs/news fragments, usage examples.
   - **Compatibility & fallback:** feature flags, legacy fallbacks, runtime constraints, degradation strategies.
   - **Secondary/contextual hints:** signatures, parameter types, specific exception classes, exact test syntax—supporting evidence only.
5. **Clustering:**  
   Group signals by category → subcategory into mid-level, generalizable rules:
   - API & default behavior  
   - Error handling & validation order  
   - Test design & coverage strategy  
   - Documentation & version management  
   - Compatibility & fallback strategy  
   Keep rules actionable, single-purpose, and avoid padding.
   Reject any rule that lacks cross-module representativeness or cannot be reused beyond the originating change.
6. **Severity assignment:**
   - **MUST:** Violations cause functional errors, compatibility breaks, or severe maintainability risk.
   - **SHOULD:** Strongly recommended with clear long-term value.
   - **MAY:** Optional optimizations or guidance.  
   Use NOT / SHOULD NOT / MUST NOT for prohibitions ; do not change severity without evidence.
7. **Rule drafting:**
   - Draft only from abstracted patterns that survived the rejection gate; combine baseline references with observed PR patterns into contextual, mid-level guidance; avoid lint-level points.
   - **Format:** `[LEVEL] Title: Description (ref PR xxxx.json, …)`
   - **Description must include:** scenario, required/recommended behavior, and engineering rationale.
   - One rule per engineering concern; use conceptual terms only (e.g., “constructor parameters”, “field metadata”, “compatibility guards”, “shared test configuration”).
   - Emphasize constraints, ordering, boundaries, and trade-offs; exclude implementation notes, function-specific mandates, or “how to build” instructions. If wording implies a unique internal structure or single implementation path, discard instead of publishing.
   - Require contextual support; avoid single-line triggers.
   - Limit references and cite only when supported by PR content.
   - Strictly follow `rule_template.md` structure and style.
8. **Outputs:**
   - `rules.md`: English, grouped by category → subcategory.
   - `dialog/rule-log-00x.md`: One per batch (even if no changes), strictly following `templates/rulelog_template.md`, listing processed file ranges and rule status (++, --, ~).

## Quality checks
- Rules are actionable, single-purpose, and project-oriented.
- Rules must pass the abstraction and rejection gate; discard any candidate that remains implementation-specific or non-generalizable.
- Prefer appending; modify or delete only on direct conflict. Incremental merging is required.
- Batch reproducibility: preserve intermediate signals; follow the batch loop strictly.
- Produce a rule log per batch, even with no changes.
- Adjust subcategories to meet rule counts without padding.
- Enforce MUST / SHOULD / MAY usage; prohibited prefixes are disallowed.
- Clear scenarios, behaviors, and rationales; real references, numerically ordered.
- Strict adherence to `rule_template.md`.

## Coverage expectations
- Multiple mid-level rules per major category; aggregate repeated patterns across PRs.
- Expand subcategories as needed to cover API contracts/defaults, validation and fallback order, runtime compatibility, testing strategy, and documentation/versioning for public interfaces.
- Keep language conceptual and behavior-driven, independent of specific tools or version numbers.
