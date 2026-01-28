# Coding Rules

## API & Defaults
### Converters & Class Methods
- [MUST] Guard false-y converters: When wrapping field converters, compare to `None` rather than relying on truthiness so false-y converter instances are still wrapped and invoked correctly, avoiding misrouting to converter callables. (ref 1374.json)
- [SHOULD] Pipe returns plain callables: `attr.converters.pipe` should return a plain callable (with preserved annotations) when the pipeline contains only callables, and only wrap in `Converter` when an actual `Converter` is present to keep call signatures consistent. (ref 1380.json)
- [MUST] Preserve user-defined `__replace__`: Auto-add `__replace__` for Python 3.13+ only when the class lacks one, mirroring `attrs.evolve` semantics so `copy.replace` works without clobbering user implementations. (ref 1383.json)
- [SHOULD] Normalize Unicode identifiers: Normalize class and attribute names to NFKC in `make_class` so Unicode identifiers behave like native class definitions and kwargs binding works predictably. (ref 1406.json)

### Serialization & Generation
- [MUST] Treat atomic types as terminals in serialization: In `asdict`/`astuple`, short-circuit known atomic types and use subclass checks for containers so atomic subclasses retain type identity and recursion skips unnecessary conversions. (ref 1463.json, 1469.json)
- [SHOULD] Compile generated methods once: Cache and evaluate generated method scripts (repr/hash/init/eq) in a single batch and reuse shared helpers like `__ne__` to reduce repeated compilation and keep debug metadata stable. (ref 1407.json)

## Error Handling & Validation
### Init Ordering & Hooks
- [MUST] Run transformers before order checks: Apply `field_transformer` output before enforcing mandatory-after-default ordering so custom reordering can resolve or surface ordering errors against the transformed layout. (ref 1401.json)
- [MUST] Pass actual init values to `__attrs_pre_init__`: Populate `__attrs_pre_init__` with the concrete values (including kw-only and default/factory outputs) in declared order instead of reusing the raw signature string, ensuring hook logic sees real inputs. (ref 1428.json)
- [MUST] Validate factory outputs after required args: For fields with default factories, validate required fields first, then call the factory only when the arg is missing, validate the factory result, and only then assign (with converters) to prevent validators observing incomplete state. (ref 1498.json, 1499.json)
- [SHOULD] Respect per-field `kw_only=False`: When using class-level `kw_only`, leave attributes that explicitly set `kw_only=False` positional (unless `force_kw_only` is enabled) to match dataclass semantics and avoid surprising API breaks. (ref 1457.json)

### Nested Validators
- [MUST] Require at least one mapping validator: `deep_mapping` must raise if neither key nor value validators are provided, and treat mapping/key/value validators as optional so `None` is skipped while still enforcing provided validators. (ref 1448.json)
- [SHOULD] Combine iterable validators: Allow list/tuple validators for `deep_iterable`/`deep_mapping` by composing them with `and_`, ensuring every supplied validator runs on members, containers, and mappings consistently. (ref 1449.json)

## Testing
### Static Analysis Baselines
- [SHOULD] Refresh Pyright expectations with upstream changes: Update stored diagnostics when Pyright message formats or signatures change to keep baseline tests meaningful and avoid stale false positives. (ref 1381.json, 1492.json)
- [SHOULD] Add typing regressions for new stub shapes: When widening stub support (e.g., converter tuples), add targeted Pyright tests to guard against future false positives. (ref 1461.json)

### Regression Coverage
- [MUST] Cover false-y converter handling: Add regression tests for converters whose `__bool__` returns `False` to ensure wrapper creation and invocation paths stay correct. (ref 1374.json)
- [SHOULD] Exercise callable-only converter pipelines: Test `pipe` when mixing Converter instances and plain callables, including annotation propagation, to lock in return-type behavior. (ref 1380.json)
- [SHOULD] Verify generator field transformers: Add tests ensuring generator-based `field_transformer` hooks still register fields and metadata correctly. (ref 1417.json)
- [SHOULD] Test Unicode class/attribute names: Include cases with normalized and unnormalized Unicode identifiers in `make_class` to confirm instantiation and repr work as expected. (ref 1406.json)
- [SHOULD] Guard copy.replace integration: Add copy.replace tests on Python 3.13+ covering auto-added `__replace__` and preservation of user-defined implementations. (ref 1383.json)

## Documentation & Versioning
### Accuracy & Roles
- [SHOULD] Keep validator docs precise: Document the exact operator/behavior a validator uses (e.g., `gt` uses `operator.gt`) to avoid misleading guidance. (ref 1423.json)
- [SHOULD] Use explicit roles for literals: Render booleans and literals with proper Sphinx roles (e.g., `:data:\`True\``/`:data:\`False\``) for consistent docs output. (ref 1432.json)
- [SHOULD] Name conflicting attributes in errors: When rejecting combined type annotation and `type=` usage, include the attribute name in the error text to speed debugging. (ref 1410.json)

### Version Metadata & Messaging
- [MUST] Record version markers for new parameters: Add `versionadded`/`versionchanged` notes when introducing options like `resolve_types` or `force_kw_only`, and describe their default behaviors and guidance. (ref 1390.json, 1457.json)
- [SHOULD] Document auto `__replace__` support: Note the Python 3.13+ `copy.replace` integration and when attrs injects `__replace__`, including version metadata. (ref 1383.json)

## Typing & Signatures
### Converter & Validator Types
- [MUST] Type converters with self/field correctly: Allow converters marked `takes_self`/`takes_field` to accept the owning instance/field in their call signatures so static analysis matches runtime usage. (ref 1382.json)
- [SHOULD] Accept union types in `instance_of`: Treat PEP 604 unions the same as tuples for validator typing to keep annotations and runtime validators aligned. (ref 1385.json)
- [SHOULD] Distinguish pipe return types in stubs: Overloads for `converters.pipe` should return a callable when only callables are provided and a `Converter` when any converter is present, keeping `val`/`return` annotations intact. (ref 1380.json)
- [SHOULD] Broaden `or_` overloads: Provide overloads (plus `Any` fallback) that allow heterogeneous validators without assuming identical input types. (ref 1471.json)
- [MUST] Represent converter tuples with ellipsis: Stub `field(converter=...)` tuples as `tuple[_ConverterType, ...]` to satisfy static checkers and avoid false errors. (ref 1461.json)

### Forward References & Protocols
- [SHOULD] Mark `AttrsInstance` runtime-checkable: Decorate the protocol so `isinstance` checks succeed for dynamic typing integrations. (ref 1389.json)
- [MUST] Resolve forward refs on 3.14+: Use annotationlib forward-ref formatting and honor `resolve_types=True` to materialize string annotations and PEP 749 references correctly. (ref 1390.json, 1451.json)
- [SHOULD] Separate baseline vs mypy-specific examples: Keep shared typing examples tool-agnostic and isolate mypy-only cases to prevent cross-tool leakage of plugin assumptions. (ref 1474.json)

## Compatibility & Flags
### Python Compatibility & Memory
- [MUST] Clear type descriptors for slotted classes on 3.14: Call `sys._clear_type_descriptors` (when available) after slot class creation to break reference cycles and prevent leaks. (ref 1459.json)
- [SHOULD] Drop stale xfails as deps catch up: Remove version-pinned xfails (e.g., cloudpickle on 3.14) once upstream fixes land to surface real regressions. (ref 1398.json)
- [SHOULD] Use annotationlib for forward refs: On Python 3.14+, request forward-ref formatted annotations to keep deferred evaluation working with new annotation semantics. (ref 1451.json)
- [SHOULD] Expose build properties for introspection: Populate `__attrs_props__`/`ClassProps` (including slotted base refs) so downstream tooling can reliably inspect effective decorator flags without guessing. (ref 1454.json)
- [SHOULD] Align `kw_only` defaults with dataclasses: Apply `kw_only` only to attributes on the defining class by default, reserving `force_kw_only` for legacy behavior to maintain cross-library expectations. (ref 1457.json)
- [SHOULD] Support generator field transformers: Materialize generator-based transformers to tuples so hooks that yield attributes remain compatible with field registration. (ref 1417.json)
