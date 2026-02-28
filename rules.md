# Coding Rules


## Runtime Behavior

### Factory Defaults
- [MUST] Validate factory-built values before assignment: When an attribute has a default factory, only invoke the factory if the caller omitted the argument, then run the attribute's validators (including cross-field validators) on the produced value before storing it; explicit arguments must still be validated immediately. This keeps validators observing the final state and preserves required-field errors. (ref PR 1498.json, 1499.json)

### Keyword-Only Semantics
- [MUST] Keep keyword-only alignment with dataclasses: `kw_only=True` on a class should only convert attributes declared on that class (unless `force_kw_only=True`), attribute-level `kw_only=False` always stays positional, and inheritance tests must ensure mixed hierarchies keep valid positional/default ordering. This prevents signature regressions as kw-only defaults evolve. (ref PR 1457.json)

### Slots Lifecycle
- [MUST] Break slotted reference cycles using official hooks: When rewriting slotted classes on Python 3.14+, clear descriptor metadata with `sys._clear_type_descriptors()` (falling back to mappingproxy hacks only when necessary) so cached properties and weakrefs don't leak the original base class. (ref PR 1446.json, 1459.json)

### Pre-init Hooks
- [MUST] Pass concrete initializer values into pre-init hooks: When generating `__init__`, feed the actual values provided by the caller—including positional defaults, factories, and keyword-only parameters—into `__attrs_pre_init__` rather than mirroring the signature, so hook logic receives the data that will end up on the instance. (ref PR 1428.json)

### Field Transformers
- [MUST] Apply field transformers before validation and materialize their output: Run `field_transformer` before performing mandatory-after-default checks, accept its reordering/removal decisions, and coerce any iterable (even generators) into a tuple so downstream validation and metadata recording see the transformed attribute set. (ref PR 1401.json, 1417.json)

### Dynamic Method Emission
- [SHOULD] Batch-generate dynamic methods and attach metadata once: Accumulate the scripts for generated dunder methods, compile/eval them in a single pass, and only then attach `__module__`/`__qualname__` to the resulting callables so filenames stay consistent and we avoid repeated compilation. (ref PR 1407.json)

### Converter Invocation
- [MUST] Route converters through structured descriptors when they need context: Promote converter callables into `Converter` objects that declare whether they need the partially built instance or the `Attribute`, register those objects when emitting `__init__`, and have helpers such as `pipe()` preserve their annotations so multi-argument conversions stay zero-overhead and type-aware. (ref PR 1267.json; rule_ref: Refactoring.Guru Code Smells > Primitive Obsession)

### Equality Generation
- [SHOULD] Emit per-attribute comparison chains: Have `_make_eq` compare each attribute (or its `eq_key`) individually instead of packing tuples so equality short-circuits on the first mismatch and avoids allocating intermediate tuples. (ref PR 1310.json; rule_ref: Refactoring.Guru Code Smells > Long Method)

### Frozen Exceptions
- [MUST] Delegate BaseException-managed attributes even on frozen classes: Allow `__cause__`, `__context__`, `__suppress_context__`, and `__notes__` to be set or deleted through `BaseException` so attrs-based exception types remain compatible with the runtime protocol despite frozen enforcement. (ref PR 1365.json; rule_ref: Refactoring.Guru Code Smells > Refused Bequest)

### Instance Copy Helpers
- [SHOULD] Prefer positional instance arguments for copy/evolve helpers: accept the source instance positionally, emit Python-native `TypeError`s for missing or extra positional arguments, and only fall back to keyword-based inst parameters with a deprecation warning so attribute names can safely reuse `inst` without collisions. (ref PR 1117.json)

## Data Serialization

### asdict / astuple Generation
- [MUST] Preserve atomic and subclass types during structuring: asdict/astuple should short-circuit for known atomic primitives, cache `type(value)` per field, and use `issubclass` instead of `isinstance` so subclasses of tuples, dicts, and numbers retain their concrete type in the serialized output while avoiding redundant attribute lookups. (ref PR 1463.json, 1469.json)

## Performance Tooling

### Benchmarks
- [SHOULD] Extend the benchmark suite whenever optimizing core helpers: before or after changing perf-sensitive helpers (e.g., asdict/astuple or cached properties on slotted classes), add focused benchmarks that cover both shortcut-heavy objects and more complicated instances so regressions are easy to detect. (ref PR 1464.json, 1489.json)
- [SHOULD] Tag high-cost suites with benchmark markers: Apply the `benchmark` marker (for Codspeed) to regression-heavy functional test classes so perf tooling captures them automatically instead of requiring piecemeal instrumentation. (ref PR 1299.json; rule_ref: Refactoring.Guru Code Smells > Shotgun Surgery)

## Class Construction

### Unicode Identifiers
- [MAY] Normalize provided identifiers before class creation: Normalize class and attribute names (e.g., NFKC) before passing them into `make_class` so any valid Unicode identifier accepted by Python also works for generated attrs types across interpreters. (ref PR 1406.json)

### Field Builder Parity
- [SHOULD] Keep next-generation field helpers feature-complete with legacy attribute factories: ensure parameters that carry metadata (like declared types) are accepted so dynamic class builders preserve the same information regardless of which helper initializes the attribute. (ref PR 1107.json; rule_ref: Refactoring.Guru Code Smells > Divergent Change)

## Typing & Tooling

### Pyright Baseline
- [SHOULD] Track Pyright feature releases in baseline tests: When pyright changes the diagnostics it emits or broadens accepted converter inputs, refresh the baseline fixtures (typed helpers, representative call sites, and expected message strings) so our dataclass-transform coverage mirrors the tool’s current behavior. (ref PR 1138.json, 1158.json)

### Baseline vs Tool-Specific Coverage
- [SHOULD] Keep baseline typing examples backend-neutral: scenarios that rely on mypy plugins or tool-specific behaviors belong in dedicated modules, while the shared baseline should only demonstrate features supported by every configured checker, and its assertions must be updated when dev dependencies (e.g., Python/pyright versions) change. (ref PR 1474.json, 1492.json)

### Validator Combinators
- [SHOULD] Provide type hints and tests for heterogeneous validators: combinators such as `attrs.validators.or_` must advertise overloads that accept validators with differing input types, and baseline typing examples should instantiate such mixed validators to guard the contract. (ref PR 1471.json, 1474.json)

### Deep Validator Flexibility
- [MUST] Let composite validators accept optional and iterable sub-validators: `deep_mapping` must allow either key or value validators to be omitted (but not both), both `deep_mapping` and `deep_iterable` should accept lists/tuples of validators by composing them with `and_`, and `optional` should treat tuples the same as lists when building its combined validator so tuple-based call sites and typing examples stay valid. (ref PR 1122.json, 1448.json, 1449.json)

### Forward References
- [MUST] Preserve forward references under `annotationlib`: when Python 3.14+ routes annotations through `annotationlib`, call `annotationlib.get_annotations()` (or request `Format.FORWARDREF` during resolution), add interpreter-gated tests, and ensure `resolve_types` succeeds before accessing fields so forward references stay loadable. (ref PR 1329.json, 1451.json)

### Type Resolution
- [SHOULD] Gate `resolve_types` calls with capability checks: Only invoke `attr.resolve_types()` after confirming the target is an attrs-managed class (for example via `attr.has`) so runtime helpers and type checkers agree on where type metadata exists. (ref PR 1141.json)

### Stub Accuracy
- [SHOULD] Encode tuple callables with variadic annotations: when a parameter accepts any-length tuples of callables (e.g., converter sequences), type stubs must use `tuple[T, ...]` instead of single-length tuples and add pyright coverage so tuple-of-converters produces no false positives. (ref PR 1461.json)

### Class Introspection
- [SHOULD] Surface effective class metadata for inspection: store derived decorator settings on `__attrs_props__`, expose them via `attrs.inspect()` (documenting it as experimental), and add typing examples/tests covering `ClassProps` enums so tooling and users can reason about generated methods. (ref PR 1454.json)

### Type Hint Resolution
- [SHOULD] Always request extended metadata from `typing.get_type_hints`: Once the supported Python baseline provides `include_extras`, pass it (along with the caller's globals/locals) and expose an opt-out flag so annotations that use `typing.Annotated` or similar helpers retain their metadata across interpreters without surprising callers that need bare types. (ref PR 1099.json, 1349.json; rule_ref: Refactoring.Guru Code Smells > Divergent Change)

### Sentinel Typing
- [MUST] Provide literal aliases for sentinel values: Export `Literal`-based aliases (for example `NothingType = Literal[_Nothing.NOTHING]`) through the public API so downstream typing can express sentinel usage without falling back to untyped primitives. (ref PR 1358.json; rule_ref: Refactoring.Guru Code Smells > Primitive Obsession)

## Tests & Validation

### String-Based Assertions
- [SHOULD] Match exact diagnostic strings that users see: when tests assert exception or tool output, align the expected text (and its punctuation) with the live code/tooling instead of relying on outdated copies, to avoid brittle failures as messages evolve. (ref PR 1473.json, 1492.json)

### Version-Specific Coverage
- [SHOULD] Gate interpreter-sensitive tests explicitly: add version-guarded suites or targeted xfails (with issue links) when behavior diverges across Python releases so CI noise stays actionable and forward-reference/cached-property expectations track upstream changes. (ref PR 1451.json, 1453.json)

### Version Gate Cleanup
- [SHOULD] Retire interpreter- or dependency-specific xfails once upstream support lands: when a runtime (e.g., CPython 3.14) or dependency regains compatibility, drop the lingering xfails/guards so CI actively exercises those paths and flags regressions early. (ref PR 1398.json, 1415.json)

## Documentation

### Sphinx Roles
- [MAY] Reference literals with Sphinx roles: when documenting booleans or sentinel objects, prefer `:data:` (e.g., `:data:\`True\``) over plain text so docs render correctly and stay consistent with the rest of the guide. (ref PR 1432.json)

### Sphinx Configuration
- [SHOULD] Keep `intersphinx_mapping` keyed and explicit: Define entries as `{alias: (url, inventory)}` instead of the deprecated `{url: None}` form so modern Sphinx releases resolve references without warnings when the syntax changes. (ref PR 1130.json)

### Validator Narratives
- [SHOULD] Keep validator docs aligned with real behavior: Docstrings must describe the actual comparison operator or constraint they enforce so readers don't have to inspect the source to know what fails. (ref PR 1423.json)

### API Canonicalization
- [SHOULD] Make the next-gen API docs the canonical entry point: Document `attrs.define()`/`attrs.field()` directly and link back to `attr.s`/`attr.ib` from there so readers learn the preferred surface once, while legacy names remain discoverable without duplicating the narrative. (ref PR 1316.json; rule_ref: Refactoring.Guru Code Smells > Divergent Change)
- [SHOULD] Remove references to parameters that no longer exist: As soon as keywords such as `cmp=` leave the runtime, scrub them from docstrings and argument lists so tutorials cannot instruct readers to use unsupported options. (ref PR 1355.json; rule_ref: Refactoring.Guru Code Smells > Speculative Generality)

### Documentation Hygiene
- [SHOULD] Keep module docstrings and import groups meaningful: Leave placeholder text out of user-facing docstrings and maintain blank-line separation between stdlib and project imports so docs stay professional and diff noise does not accumulate. (ref PR 1366.json; rule_ref: Refactoring.Guru Code Smells > Comments)

## Diagnostics

### User-Facing Text
- [SHOULD] Mention the conflicting argument in exception text: When rejecting attribute definitions (e.g., both annotation and explicit `type=`), include the attribute name in the error so users can immediately locate the offender. (ref PR 1410.json)

### Deprecation Signaling
- [SHOULD] Retire deprecation warnings for APIs that must remain available: when a helper stays to cover edge cases, drop unconditional warnings and instead document why an alternative is preferred so linters and users aren't flooded with noise they cannot act on. (ref PR 1119.json)
- [SHOULD] Emit DeprecationWarning at the entry points of integrations that are being removed: gate optional third-party validators or adapters with warnings (and update tests to expect them) so downstream projects have a clear migration window before the dependency is dropped. (ref PR 1120.json)
