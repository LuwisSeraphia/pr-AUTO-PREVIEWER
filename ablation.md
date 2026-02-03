<CLUSTER 1>
file:{1499.json,1498.json,1492.json,1489.json,1474.json}
- <Group 1> (baseline): Generate rules using only the template, no abstraction requirement, no rule_ref link.
--- 1499.json: In `_attrs_to_init_script`, fill `pre_init_args` with actual parameter names and validate factory outputs right after invoking `_INIT_FACTORY_PAT` so cross-field validators and converters observe the final values.
--- 1498.json: Keep the new `tests/test_factory_validation_order.py` coverage that asserts required-field validators run before default factories to prevent regressions in factory execution order.
--- 1492.json: Adjust `tests/test_pyright.py::test_pyright_baseline` to match the latest pyright diagnostic string (drop `SupportsTrunc`) or the suite will fail on updated toolchains.
--- 1489.json: Extend `bench/test_benchmarks.py` with `TestCachedProperties` cases that time cached properties on slotted/unslotted classes so future caching optimizations have numbers.
--- 1474.json: Move general typing samples into `typing-examples/baseline_examples.py` and keep mypy-specific cases in `typing-examples/mypy_examples.py` so tool-dependent behavior stops leaking into the shared baseline.

- <Group 2> (template + abstraction): Generate rules using the template and the abstraction requirements (avoid variable names, generalize rules), but do NOT use rule_ref links.
--- 1499.json: Default factories must only run when the caller omits a value, and the produced data has to pass the attribute’s validators before it is stored so cross-field checks see the final state.
--- 1498.json: Cross-field validators should execute after every derived default has been computed, otherwise they compare stale values and raise false alarms.
--- 1492.json: Baseline typing smoke tests need to mirror the exact diagnostics reported by the active type checker so dependency bumps do not create noise.
--- 1489.json: Whenever optimizing cached helpers, add benchmarks that cover both slotted and unslotted objects to quantify wins and regressions.
--- 1474.json: Keep platform-agnostic typing scenarios in a shared baseline module and relocate checker-specific behaviors to their own files to avoid leaking proprietary assumptions.

- <Group 3> (template + abstraction + rule_ref): Generate rules using template, abstraction requirements, and incorporate rule_ref links (from templates/rule_ref.md or user-provided map) when applicable.
--- 1499.json: Initialization helpers must feed caller-provided or factory-generated values through their validators before persisting them so every hook observes the canonical state. [rule ref: SEI CERT Python Coding Standard - https://wiki.sei.cmu.edu/confluence/display/python]
--- 1498.json: Cross-field validators belong at the end of the default-provision pipeline so comparisons always use concrete data instead of sentinel placeholders. [rule ref: Refactoring.Guru Code Smells - https://refactoring.guru/refactoring/smells]
--- 1492.json: When toolchains evolve, refresh baseline diagnostics to match the new messages, otherwise the suite masks real regressions behind brittle string asserts. [rule ref: Martin Fowler Code Smell Catalogue - https://martinfowler.com/bliki/CodeSmell.html]
--- 1489.json: Embed representative benchmarks whenever touching cached attributes to prevent “mystery slowdowns” that would otherwise qualify as a performance smell. [rule ref: Refactoring.Guru Code Smells - https://refactoring.guru/refactoring/smells]
--- 1474.json: Separate checker-neutral and checker-specific typing suites so rule sets stay orthogonal and easier to reason about across tooling. [rule ref: SEI CERT Python Coding Standard - https://wiki.sei.cmu.edu/confluence/display/python]

------------------------------------------------------------------------
<CLUSTER 2>
file:{1473.json,1471.json,1469.json,1464.json,1463.json}
- <Group 1> (baseline): Generate rules using only the template, no abstraction requirement, no rule_ref link.
--- 1473.json: Update every `pytest.raises(..., match=...)` in `tests/test_make.py`, `tests/test_next_gen.py`, and `tests/test_setattr.py` to drop the trailing punctuation so the regex matches the new ValueError wording.
--- 1471.json: Add a `ValidatedInconsistentOr` example that passes a mixture of numeric and string validators into `attrs.validators.or_` to prove heterogenous overloads type-check.
--- 1469.json: Cache `type(v)` inside `astuple`, short-circuit `_ATOMIC_TYPES`, and swap `isinstance` for `issubclass` so tuple subclasses keep their concrete type when serialized.
--- 1464.json: Add `test_asdict_complicated`, `test_astuple_complicated`, and atomic-field benchmarks that repeatedly call `attrs.asdict/astuple` so perf changes have stress tests.
--- 1463.json: Introduce `_ATOMIC_TYPES` in `asdict` and short-circuit recursion for those primitives, ensuring subclasses of builtins retain their exact class when unstructuring.

- <Group 2> (template + abstraction): Generate rules using the template and the abstraction requirements (avoid variable names, generalize rules), but do NOT use rule_ref links.
--- 1473.json: Tests that assert exception text should mirror the exact wording users see; loosen overly specific regexes when punctuation or spacing changes.
--- 1471.json: Provide typing fixtures that demonstrate validator combinators accepting heterogeneous callable signatures so overloads stay honest.
--- 1469.json: When serializing objects to tuples, detect atomic primitives up front and base decisions on the cached type so subclass identities survive the conversion.
--- 1464.json: Pair every optimization of structuring helpers with benchmarks that cover shortcut-heavy instances and more complex, nested ones.
--- 1463.json: Treat atomic primitives as already-structured data inside `asdict` so recursion is avoided and subclasses retain their original type.

- <Group 3> (template + abstraction + rule_ref): Generate rules using template, abstraction requirements, and incorporate rule_ref links (from templates/rule_ref.md or user-provided map) when applicable.
--- 1473.json: Keep assertion strings synchronized with user-facing errors so diagnostics stay trustworthy across releases. [rule ref: SEI CERT Python Coding Standard - https://wiki.sei.cmu.edu/confluence/display/python]
--- 1471.json: Validator combinators must advertise and test mixed input shapes; otherwise they turn into unclear contracts that smell of leaky abstractions. [rule ref: Refactoring.Guru Code Smells - https://refactoring.guru/refactoring/smells]
--- 1469.json: Basing recursion decisions on cached types ensures tuple/dict subclasses remain intact, preventing hard-to-debug behavioral drift. [rule ref: SEI CERT Python Coding Standard - https://wiki.sei.cmu.edu/confluence/display/python]
--- 1464.json: Performance work demands benchmark coverage for both hot paths and worst cases so future contributors avoid reintroducing systemic smells. [rule ref: Martin Fowler Code Smell Catalogue - https://martinfowler.com/bliki/CodeSmell.html]
--- 1463.json: Recognize and short-circuit atomic primitives when structuring data to avoid needless work and to respect user-defined numeric/string subclasses. [rule ref: Refactoring.Guru Code Smells - https://refactoring.guru/refactoring/smells]

------------------------------------------------------------------------
<CLUSTER 3>
file:{1390.json,1389.json,1385.json,1383.json,1382.json}
- <Group 1> (baseline): Generate rules using only the template, no abstraction requirement, no rule_ref link.
--- 1390.json: Wire `resolve_types` through `_ClassBuilder`, `attrs.define`, and `tests/test_next_gen.py` so decorators can opt into calling `attrs.resolve_types()` automatically.
--- 1389.json: Mark `AttrsInstance` as `@runtime_checkable` so `isinstance(obj, AttrsInstance)` works at runtime when Protocols are used.
--- 1385.json: Extend `tests/typing_example.py::Validated` to accept `attrs.validators.instance_of(int | C | str)` so union syntax is supported without tuples.
--- 1383.json: Move `evolve` into `_make.py`, expose it via `attr.__all__`, and auto-install `__replace__` on CPython 3.13+ so `copy.replace()` works on attrs classes.
--- 1382.json: Add typing coverage for converters that set `takes_self=True` and/or `takes_field=True`, ensuring `attrs.Converter` call signatures accept the extra parameters.

- <Group 2> (template + abstraction): Generate rules using the template and the abstraction requirements (avoid variable names, generalize rules), but do NOT use rule_ref links.
--- 1390.json: Decorators should offer an option to resolve forward-referenced annotations automatically so users do not have to call helper APIs by hand.
--- 1389.json: Protocols that developers expect to use in `isinstance` checks must be decorated with `runtime_checkable` to keep runtime checks legal.
--- 1385.json: Validator helpers ought to accept native union syntax in addition to tuple arguments so type hinting stays modern.
--- 1383.json: When newer runtimes introduce `copy.replace`, attrs classes should surface a compatible `__replace__` so built-in copy helpers keep working.
--- 1382.json: Converter factories need type signatures that cover self-aware and field-aware callables, otherwise static analysis rejects legitimate converters.

- <Group 3> (template + abstraction + rule_ref): Generate rules using template, abstraction requirements, and incorporate rule_ref links (from templates/rule_ref.md or user-provided map) when applicable.
--- 1390.json: Provide an opt-in switch that resolves forward references as soon as the decorator finishes so consumers never interact with string annotations at runtime. [rule ref: SEI CERT Python Coding Standard - https://wiki.sei.cmu.edu/confluence/display/python]
--- 1389.json: Any Protocol meant for runtime checks must be annotated with `runtime_checkable` to avoid undefined behavior when `isinstance` is used. [rule ref: SEI CERT Python Coding Standard - https://wiki.sei.cmu.edu/confluence/display/python]
--- 1385.json: Validation helpers should track modern union syntax, otherwise the API surface advertises stale patterns—a classic smell. [rule ref: Refactoring.Guru Code Smells - https://refactoring.guru/refactoring/smells]
--- 1383.json: Mirror emerging platform features (like `copy.replace`) so attrs instances integrate with the native toolbox and do not accrue design debt. [rule ref: Martin Fowler Code Smell Catalogue - https://martinfowler.com/bliki/CodeSmell.html]
--- 1382.json: Document and type converters that capture `self` or `field` metadata to keep static analysis aligned with runtime behavior. [rule ref: SEI CERT Python Coding Standard - https://wiki.sei.cmu.edu/confluence/display/python]

------------------------------------------------------------------------
<Summary>
The form-rules skill enforces a disciplined workflow: batching PR JSON inputs, abstracting each lesson into project-wide guidance, and (when required) citing established references from `templates/rule_ref.md`. Comparing the groups shows that these constraints matter—without them (Group 1) the “rules” devolve into file-specific notes, while abstraction alone (Group 2) yields reusable guidance but lacks traceability. Adding rule references (Group 3) ties each recommendation to widely recognized sources, which clarifies intent, signals severity, and makes the resulting guidance easier to defend during reviews.
