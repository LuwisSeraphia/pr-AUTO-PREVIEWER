# Coding Rules

## API & Defaults
### Dynamic Class Behavior
- [MUST] Refresh abstract method metadata after dynamically constructing or patching classes derived from ABCs, guarding calls with runtime version checks when helper APIs are only available, so generated classes drop abstract status only when implementations exist; keep slot-specific branches consistent and cover with version-gated tests for concrete versus abstract instantiation. (ref PR 1001.json)
### Validator Composition
- [SHOULD] Provide composable validators (including logical inversion) that validate wrapped validators' exception contracts, support custom messages, and expose meaningful representations while coercing exception type inputs to tuples; validate provided exception types as Exception subclasses to fail fast on misuse. (ref PR 1010.json)
### Hash Configuration & Aliases
- [SHOULD] Expose hash configuration aliases that align with external specifications (e.g., PEP 681), prioritizing the alias when both are provided, and ensure docs, typing examples, and runtime behavior agree on precedence for generated `__hash__` decisions. (ref PR 1065.json)
### Annotation Handling
- [SHOULD] Treat `Final` annotations (typing and typing_extensions) as class variables when collecting attributes, keeping them out of generated field sets across supported Python versions, and gate behavior with version-aware tests. (ref PR 1066.json)
### Filtering APIs
- [SHOULD] Allow include/exclude filters to accept field-name strings in addition to types and Attribute objects, splitting inputs by type and name so filters remain declarative while rejecting unexpected types via tests and version markers. (ref PR 1068.json)
### Generic Introspection
- [SHOULD] Support specialized generic classes when resolving attrs metadata, reusing the origin’s cached attributes and raising clear errors for non-attrs generics; cache resolved attrs on specialized classes to avoid repeated lookups. (ref PR 1079.json)
### Frozen Exceptions
- [MUST] Permit setting BaseException mutation hooks (`__cause__`, `__context__`, `__traceback__`) on frozen exception types while keeping other attributes immutable, so exception handling frameworks can attach context without breaking freeze guarantees. (ref PR 1081.json)

## Compatibility & Fallback Strategy
### Serialization Evolution
- [MUST] Persist instance state as attribute-name-keyed mappings and, during restoration, assign only attributes still defined to tolerate added or removed fields across versions; skip absent entries instead of relying on positional order to avoid resurrecting stale state in slotted objects. (ref PR 1009.json)
### Runtime Version Boundaries
- [MUST] Centralize version feature flags and use them to guard behavior changes and test expectations when upstream APIs shift between Python releases, updating compatibility constants alongside consuming tests. (ref PR 1001.json, 1033.json)
### Deprecation Signaling and Packaging Alignment
- [SHOULD] Emit import-time deprecation warnings on runtimes slated for removal and align distribution metadata (including wheel targets) to supported versions, inviting feedback before final drops. (ref PR 1017.json, 1005.json)

## Test Design & Coverage Strategy
### Shared Parametrization
- [SHOULD] Replace repeated boolean parametrizations with fixtures that supply parameter values, letting tests request slots or frozen variants implicitly while keeping decorator stacks shallow and ensuring subjects accept fixture-provided parameters. (ref PR 1002.json)
### Version-Scoped Testing
- [SHOULD] Use skip or expectation guards and dynamic match strings to isolate runtime-specific behaviors so suites stay stable across interpreter versions, reusing shared fixtures where possible. (ref PR 1001.json, 1033.json)
### Type Checker Baselines
- [SHOULD] Maintain static type-checker baselines that cover field aliasing and generated initializers, asserting expected diagnostic outputs to keep dataclass_transform compatibility stable. (ref PR 1063.json)

## Documentation & Build Management
### Docs Tooling & Release Notes
- [SHOULD] Enable Markdown/MyST parsing and changelog draft rendering via explicit Sphinx extensions with project-root-aware configuration, and include the required documentation extras alongside extension settings. (ref PR 1016.json, 1053.json)
### Test/Docs Dependency Segregation
- [SHOULD] Expose test and coverage tooling through dedicated extras (e.g., parallel test runners with CPU detection support and coverage packages for subprocess tracing) to keep CI dependencies explicit and reproducible, and update long-description content types to match the source format when switching markup. (ref PR 1011.json, 1053.json)
### Release Packaging & API Documentation
- [SHOULD] Keep distribution long descriptions aligned with Markdown changelog content by extracting current-release sections for package indexes, and clarify API docs so helper factories (e.g., `make_class`) specify structured field inputs instead of bare names, preventing misuse. (ref PR 1067.json, 1075.json)
