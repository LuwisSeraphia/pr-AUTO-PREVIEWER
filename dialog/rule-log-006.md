# Batch 006 (PRs 1099-1120)
Processed files: 5

## Added Rules (++)
1. [SHOULD] Instance Copy Helpers: Prefer positional instance arguments for copy helpers, raise native `TypeError`s on bad positional usage, and only warn when falling back to keyword-based instances so attributes named like the original parameter remain usable. (ref PR 1117.json)
2. [SHOULD] Field Builder Parity: Keep next-gen field helpers feature-complete with legacy factories by accepting metadata parameters (e.g., declared types) so dynamic class builders see consistent attribute definitions. (ref PR 1107.json; rule ref: Refactoring.Guru Code Smells > Divergent Change)
3. [SHOULD] Deprecation Signaling — retire redundant warnings: Drop unconditional deprecation warnings for helpers that must remain available and document the distinction instead. (ref PR 1119.json)
4. [SHOULD] Deprecation Signaling — warn when integrations are actually leaving: Emit entry-point DeprecationWarnings when third-party adapters/validators are being removed and cover them in tests. (ref PR 1120.json)

## Modified Rules (~)
1. [SHOULD] Type Hint Resolution: Added PR 1099.json and clarified that callers get an opt-out flag while `typing.get_type_hints(..., include_extras=True)` remains the default on supported interpreters. (ref PR 1099.json, 1349.json; rule ref: Refactoring.Guru Code Smells > Divergent Change)

## Removed Rules (--)
- None

## Notes
- Processed PR JSONs: 1099, 1107, 1117, 1119, 1120 (moved to `dataset/PR-processed/`).
- Deprecation signaling now has two complementary rules to distinguish “quiet but supported” helpers from integrations that are truly going away.
