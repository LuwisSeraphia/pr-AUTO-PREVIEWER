---
name: form-rules
description: Form or update mid-level English rules by reading existing PR JSONs in the unprocessed folder, without relying on external scripts or runners. Trigger when asking to generate or update rules; If no PR files exist in the unprocessed folder, fetch pr via grab-pr skill first.
---

## Overview
Use this skill when PR records exist in `dataset/PR-unprocessed/` to generate or update `rules.md`.  
The goal is to extract **project-oriented general engineering guidance** from multiple PRs—more abstract than a single change, leaning toward method-level summarization, but still actionable.  
Avoid any concrete variable names, function names, or file paths. Focus on conceptual patterns rather than isolated identifiers.  
All actions are carried out manually per these instructions; do not invoke external runners or scripts.

This skill also **supports incremental updates**:
- If `rules.md` already contains content, try not to modify existing rules. Typically, only append new rules or extend existing rules based on new PR evidence; remove rules only if they conflict or are no longer applicable.  
- Users may optionally provide a custom rule reference mapping, which should **take precedence** over `templates/rule_ref.md`.

## Inputs
- Source PR JSON: `dataset/PR-unprocessed/*.json` (or user-specified folder if declared) ,If no PR files exist in the unprocessed folder, fetch pr via grab-pr skill first. 
- Templates/references: `templates/rule_template.md`, `templates/rulelog_template.md`, `templates/rule_ref.md`  
- Existing rules: `rules.md`  
- Optional user-provided rule reference mapping  
- Output logs: `dialog/rule-log-00x.md`

## Batch workflow
1) Discover inputs: list `dataset/PR-unprocessed/*.json`; stop if none exist.  
2) Batch processing:
   - Default 10 PRs per batch  
   - Respect smaller batch sizes requested by the user  
   - Max 10 per batch, up to 5 batches total (≤50 PRs)  
3) Per-PR analysis:
   - Read diffs with surrounding context (function/class scope, before/after lines)  
   - Determine **the problem addressed**, **risk mitigated**, or **behavior enforced**  
   - Ignore variable names; summarize conceptual patterns for method-level guidance  

4) Batch-level processing:
   - **Pattern extraction:** After reviewing the batch, list recurring themes or lessons (abstractly, e.g., validation order, default handling, error signaling)  
   - **Rule update / incremental merge:**
     - Existing rules: if a batch pattern matches an existing rule, append new PR filenames to its `(ref ...)` list (numeric sorted). Only modify text if necessary for correctness.  
     - New rules: only draft if batch patterns support them; follow `rule_template.md` and abstraction rules.  
     - Apply references: prioritize user-provided rule mapping first; fallback to `templates/rule_ref.md`. Record applied refs in batch logs.  
     - Immediately append or update `rules.md`; do not delay edits to later batches.

## Rule abstraction guidelines
- **Think**:  
> “Can future contributors apply this rule without seeing the original PR or specific code?” If not, the description must be refined.

- Rules should:
  - Apply across **multiple scenarios**, not tied to a single PR or code path  
  - Avoid literal identifiers (variables, functions, file paths)  
- Rules may:
  - Refer to concepts like “function inputs,” “returned values,” “configuration fields,” “error responses”  
  - Remain at an **engineering best-practice** level, methodologically applicable, not purely abstract  
- Avoid:
  - Directly echoing PR diffs with specific identifiers  
  - Narrow, implementation-specific guidance  
  - Instructions containing variable names

## Categories (lightweight)
- API behavior & defaults  
- Validation & error handling  
- Testing practices  
- Documentation & compatibility  

Strict classification not required.

## Severity
- MUST: correctness, safety, compatibility, or major maintenance risk  
- SHOULD: strong recommendation with long-term benefit  
- MAY: optional improvement or style guidance

## Rule drafting
- Follow `rule_template.md`  
- One rule per concern  
- Format: `[LEVEL] Title: Description (ref PR xxxx.json, …)`  
- References sorted numerically  
- Include references from `rule_ref.md` or user-provided mapping  
- Description: <abstract methodology/project code principles>: <generic, project-level engineering guidance>

## Outputs
- Incrementally update `rules.md` per batch (append new rules; extend `(ref ...)` lists of existing rules)  
- Batch logs `dialog/rule-log-00x.md`:
  - Batch index  
  - PRs covered  
  - Patterns identified  
  - Rules added / modified / skipped  
  - Applied rule_ref links  
- Move processed PR JSONs to `dataset/PR-processed/` after each batch

## Quality checks
- Rules remain actionable, mid-level, single-purpose, project-oriented  
- No literal identifiers  
- Only append or modify rules supported by batch evidence  
- Preserve category/subcategory structure; add subcategories only if necessary  
- Ref lists use real filenames, sorted; English-only rules  
- Do not reprocess prior batches or logs; ensure batch reproducibility.
