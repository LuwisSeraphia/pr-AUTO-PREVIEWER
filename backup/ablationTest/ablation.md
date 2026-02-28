Scoring legend: <total/10 (Correctness+Feasibility+Contextless Readability)>

<CLUSTER 1>
file:{1299.json,1310.json,1349.json,1355.json,1358.json}
- <Group 1> (baseline): Generate rules using only the template, no abstraction requirement, no rule_ref link.
--- 1299.json:<5/10 (3+1+1)> Add `@pytest.mark.benchmark()` to `TestFunctional` so Codspeed captures the suite's performance.
--- 1310.json:<4/10 (2+1+1)> Rewrite `_make_eq` to emit chained `self.attr == other.attr` comparisons and update the float strategy to ban NaN inputs for consistent equality semantics.
--- 1349.json:<5/10 (3+1+1)> Drop the `PY_3_9_PLUS` guard and always pass `include_extras` to `typing.get_type_hints`, removing the unused compat constant.
--- 1355.json:<4/10 (2+1+1)> Update the next-gen docs so `attrs.define` / `attrs.field` no longer mention the removed `cmp=` argument.
--- 1358.json:<4/10 (2+1+1)> Export `NothingType = Literal[_Nothing.NOTHING]` via both public `__all__` lists so downstream type annotations can target the sentinel.

- <Group 2> (template + abstraction): Generate rules using the template and the abstraction requirements (avoid variable names, generalize rules), but do NOT use rule_ref links.
--- 1299.json:<10/10 (4+3+3)> [SHOULD] Benchmark high-cost regression suites: Tag performance-heavy functional tests with a benchmark marker so performance tooling can collect timing data without manual instrumentation. (ref 1299.json)
--- 1310.json:<9/10 (4+2+3)> [MUST] Generate equality as per-attribute comparisons: Build synthesized equality functions that compare each attribute (or its comparison key) individually to short-circuit mismatches instead of packing tuples. (ref 1310.json)
--- 1349.json:<9/10 (4+3+2)> [SHOULD] Preserve extended typing metadata: When resolving annotations, request extras unconditionally once the supported Python floor guarantees availability so metadata like Annotated survives. (ref 1349.json)
--- 1355.json:<8/10 (3+3+2)> [SHOULD] Keep narrative docs synchronized with actual signatures: Remove references to deprecated keyword arguments as soon as the runtime stops accepting them. (ref 1355.json)
--- 1358.json:<9/10 (4+2+3)> [MUST] Provide explicit typing hooks for sentinels: Offer Literal-based aliases for sentinel objects so integrators can express them in type annotations. (ref 1358.json)

- <Group 3> (template + abstraction + rule_ref): Generate rules using template, abstraction requirements, and incorporate rule_ref links (from templates/rule_ref.md or user-provided map) when applicable.
--- 1299.json:<10/10 (4+3+3)> [SHOULD] Benchmark-critical suites use dedicated markers: Centralize performance instrumentation via suite-level benchmark tags to avoid editing dozens of tests when enabling Codspeed. (ref 1299.json; rule_ref: Refactoring.Guru Code Smells > Shotgun Surgery) [ref:highly relate]
--- 1310.json:<9/10 (4+2+3)> [MUST] Equality builders compare attributes independently: Emit chained per-attribute comparisons (or eq_key invocations) rather than bloated tuple packing so equality stays fast and readable. (ref 1310.json; rule_ref: Refactoring.Guru Code Smells > Long Method) [ref:low relate]
--- 1349.json:<10/10 (4+3+3)> [SHOULD] Retire obsolete compat layers once baselines rise: Remove unused version flags and always call type-hint resolvers with extras to prevent divergent handling of annotations. (ref 1349.json; rule_ref: Refactoring.Guru Code Smells > Divergent Change) [ref:highly relate]
--- 1355.json:<9/10 (4+3+2)> [SHOULD] Eliminate documentation for dead parameters promptly: Avoid confusing readers with options that no longer exist; leaving them behind is speculative generality. (ref 1355.json; rule_ref: Refactoring.Guru Code Smells > Speculative Generality) [ref:low relate]
--- 1358.json:<10/10 (4+3+3)> [MUST] Publish type-safe sentinel descriptors: Supply dedicated Literal aliases for sentinel objects instead of forcing consumers to treat them as primitives, addressing primitive obsession. (ref 1358.json; rule_ref: Refactoring.Guru Code Smells > Primitive Obsession) [ref:highly relate]

------------------------------------------------------------------------
<CLUSTER 2>
file:{1365.json,1366.json,1372.json,1373.json,1374.json}
- <Group 1> (baseline): Generate rules using only the template, no abstraction requirement, no rule_ref link.
--- 1365.json:<5/10 (3+1+1)> Allow frozen exception instances to update BaseException-managed fields (`__cause__`, `__context__`, `__suppress_context__`, `__notes__`) by delegating those names to the base type and extend the regression test accordingly.
--- 1366.json:<4/10 (2+1+1)> Insert a blank line between stdlib imports in `setup.py` and adjust the validators module docstring text to read "Commonly useful validators. xxyyzz".
--- 1372.json:<5/10 (3+1+1)> Teach `converters.optional` to accept Converter instances, wrapping them so takes_self/takes_field semantics and type annotations survive, and add regression tests for optional pipes.
--- 1373.json:<4/10 (2+1+1)> Uncomment the converter sections in `tests/typing_example.py` so optional/to-bool usages are real code that type-checks under attr.s.
--- 1374.json:<5/10 (3+1+1)> Switch the converter check in `_attrs_to_init_script` to `is not None` so false-y converter objects still get wrapped in `Converter`, adding a test that exercises a custom converter with `__bool__` returning False.

- <Group 2> (template + abstraction): Generate rules using the template and the abstraction requirements (avoid variable names, generalize rules), but do NOT use rule_ref links.
--- 1365.json:<9/10 (4+3+2)> [MUST] Honor BaseException mutability rules on frozen types: Even when a dataclass-like exception is frozen, allow the runtime to set and delete `__cause__`, `__context__`, `__suppress_context__`, and `__notes__`. (ref 1365.json)
--- 1366.json:<8/10 (3+3+2)> [SHOULD] Keep module docstrings meaningful and import blocks readable: Ensure explanatory headers remain human language (no placeholders) and keep standard-library imports visually separated. (ref 1366.json)
--- 1372.json:<10/10 (4+3+3)> [MUST] Propagate converter context through optional wrappers: Optional converters must detect wrapped Converter objects so they can forward self/field context and typing metadata while still bypassing None inputs. (ref 1372.json)
--- 1373.json:<8/10 (3+2+3)> [SHOULD] Execute typing fixtures as real code: Example modules that guard stubs should instantiate converter patterns instead of leaving them commented out, ensuring the type checker verifies real scenarios. (ref 1373.json)
--- 1374.json:<10/10 (4+3+3)> [MUST] Check converters explicitly against None: When coercing converters to Converter objects, use identity comparisons so false-y callables aren't skipped. (ref 1374.json)

- <Group 3> (template + abstraction + rule_ref): Generate rules using template, abstraction requirements, and incorporate rule_ref links (from templates/rule_ref.md or user-provided map) when applicable.
--- 1365.json:<10/10 (4+3+3)> [MUST] Frozen exceptions must not refuse BaseException’s special state: Permit cause/context/suppress_context/notes to mutate even under frozen enforcement so subclasses don’t “refuse the bequest.” (ref 1365.json; rule_ref: Refactoring.Guru Code Smells > Refused Bequest) [ref:highly relate]
--- 1366.json:<9/10 (3+3+3)> [SHOULD] Keep documentation text purposeful: Avoid inserting nonsense into module docstrings and maintain clean import grouping to prevent confusing commentary, per the “Comments” smell guidance. (ref 1366.json; rule_ref: Refactoring.Guru Code Smells > Comments) [ref:low relate]
--- 1372.json:<10/10 (4+3+3)> [MUST] Extend optional converters like a proper library hook: Treat Converter instances as first-class inputs so optional wrappers behave as complete extensions rather than incomplete library classes. (ref 1372.json; rule_ref: Refactoring.Guru Code Smells > Incomplete Library Class) [ref:highly relate]
--- 1373.json:<9/10 (4+2+3)> [SHOULD] Replace commented examples with executable ones: Keeping converter demos as real code avoids speculative generality and ensures typing coverage stays current. (ref 1373.json; rule_ref: Refactoring.Guru Code Smells > Speculative Generality) [ref:low relate]
--- 1374.json:<10/10 (4+3+3)> [MUST] Use explicit sentinel checks when wrapping converters: Depending on truthiness to detect the absence of a converter is a form of primitive obsession; compare to None directly. (ref 1374.json; rule_ref: Refactoring.Guru Code Smells > Primitive Obsession) [ref:highly relate]

------------------------------------------------------------------------
<CLUSTER 3>
file:{1398.json,1406.json,1410.json,1415.json,1423.json}
- <Group 1> (baseline): Generate rules using only the template, no abstraction requirement, no rule_ref link.
--- 1398.json:<5/10 (3+1+1)> Remove the `PY_3_14_PLUS` import and the `xfail` marker from `TestCloudpickleCompat` because cloudpickle now supports Python 3.14.
--- 1406.json:<5/10 (3+1+1)> Normalize the class name passed to `make_class` with `unicodedata.normalize("NFKC", ...)` and add tests proving unicode identifiers work before/after normalization.
--- 1410.json:<5/10 (3+1+1)> Update the ValueError raised when both a type annotation and `type=` argument are provided so it mentions the offending attribute name, and assert the new message in tests.
--- 1415.json:<5/10 (3+1+1)> Drop the Python 3.14-specific import/xfail guard around the annotation forward-reference tests so they execute normally.
--- 1423.json:<4/10 (2+1+1)> Fix the `attrs.validators.gt` docstring to say it uses `operator.gt` instead of `operator.ge`.

- <Group 2> (template + abstraction): Generate rules using the template and the abstraction requirements (avoid variable names, generalize rules), but do NOT use rule_ref links.
--- 1398.json:<9/10 (4+3+2)> [SHOULD] Retire obsolete expected-failure markers as soon as upstream dependencies support the new runtime so compatibility suites actually run. (ref 1398.json)
--- 1406.json:<10/10 (4+3+3)> [MUST] Normalize dynamically generated identifiers: When constructing classes programmatically, canonicalize class and attribute names to Unicode NFKC before code generation. (ref 1406.json)
--- 1410.json:<9/10 (4+2+3)> [SHOULD] Include attribute names in conflicting type errors so users immediately know which field specified both an annotation and an explicit type. (ref 1410.json)
--- 1415.json:<9/10 (4+3+2)> [SHOULD] Remove temporary skips/xfails once the targeted interpreter stabilizes so annotation tests continue to validate behavior. (ref 1415.json)
--- 1423.json:<8/10 (3+2+3)> [SHOULD] Keep validator documentation aligned with the actual operator they call to avoid misleading API consumers. (ref 1423.json)

- <Group 3> (template + abstraction + rule_ref): Generate rules using template, abstraction requirements, and incorporate rule_ref links (from templates/rule_ref.md or user-provided map) when applicable.
--- 1398.json:<10/10 (4+3+3)> [SHOULD] Remove stale xfails once dependency support ships; continuing to expect failure is speculative generality that hides regressions. (ref 1398.json; rule_ref: Refactoring.Guru Code Smells > Speculative Generality) [ref:low relate]
--- 1406.json:<10/10 (4+3+3)> [MUST] Normalize unicode identifiers up front so callers don’t face divergent change across code paths that manually normalize names. (ref 1406.json; rule_ref: Refactoring.Guru Code Smells > Divergent Change) [ref:highly relate]
--- 1410.json:<9/10 (4+2+3)> [SHOULD] Provide context-rich error messages instead of anonymous primitives; naming the conflicting attribute prevents primitive obsession around debugging. (ref 1410.json; rule_ref: Refactoring.Guru Code Smells > Primitive Obsession) [ref:low relate]
--- 1415.json:<10/10 (4+3+3)> [SHOULD] Delete temporary xfails once they’re no longer needed to avoid creating dead code paths in the test suite. (ref 1415.json; rule_ref: Refactoring.Guru Code Smells > Dead Code) [ref:highly relate]
--- 1423.json:<9/10 (4+2+3)> [SHOULD] Keep documentation text accurate; mismatched operator names in validator descriptions are exactly the kind of misleading comment smell to avoid. (ref 1423.json; rule_ref: Refactoring.Guru Code Smells > Comments) [ref:no relation]


conclusion:The skill requirements (template format, abstraction, severity tagging, and per-rule refs) force each rule to become reusable guidance instead of a literal restatement of a PR diff. Once I had to write with abstraction, variable names disappeared, the intent became clearer, and the ref list kept provenance obvious. Adding rule_ref links in Group 3 further anchored each rule to a well-known code-smell rationale, which made it easier to justify the recommendation and relate it to broader engineering practice rather than just this repository.
