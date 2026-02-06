# Batch 005 (PRs 1122-1158)
Processed files: 5

## Added Rules (++)
1. [SHOULD] Keep `intersphinx_mapping` keyed and explicit: Define entries as `{alias: (url, inventory)}` instead of the deprecated `{url: None}` form so modern Sphinx releases resolve references without warnings when the syntax changes. (ref PR 1130.json). [rule ref: Refactoring.Guru Code Smells > Divergent Change]
2. [SHOULD] Track Pyright feature releases in baseline tests: When pyright changes the diagnostics it emits or broadens accepted converter inputs, refresh the baseline fixtures (typed helpers, representative call sites, and expected message strings) so our dataclass-transform coverage mirrors the tool’s current behavior. (ref PR 1138.json, 1158.json). [rule ref: Refactoring.Guru Code Smells > Divergent Change]
3. [SHOULD] Gate `resolve_types` calls with capability checks: Only invoke `attr.resolve_types()` after confirming the target is an attrs-managed class (for example via `attr.has`) so runtime helpers and type checkers agree on where type metadata exists. (ref PR 1141.json). [rule ref: Refactoring.Guru Code Smells > Speculative Generality]

## Modified Rules (~)
1. [MUST] Let composite validators accept optional and iterable sub-validators: Added PR 1122.json to cover tuples passed into `optional` so tuple-based call sites keep working alongside the existing list support. (ref PR 1122.json, 1448.json, 1449.json). [rule ref: Refactoring.Guru Code Smells > Primitive Obsession]

## Removed Rules (--)
- None

## Notes
- 5 PR JSONs (1122, 1130, 1138, 1141, 1158) were analyzed and moved to `dataset/PR-processed/`.
- Pyright-related changes were treated as a shared theme to avoid duplicating guidance across multiple tooling rules.
