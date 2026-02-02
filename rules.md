# Coding Rules

## Attribute Construction & Defaults
### Value Normalization Order
- [MUST] Run attribute converters before validators: Attribute definitions that expose a `convert` hook must normalize incoming values before any validator logic executes so that validators and downstream consumers see canonical data, and conversion errors surface deterministically. (ref PR 27.json)
- [MUST] Enforce default initialization for non-init attributes: Attributes excluded from `__init__` (`init=False`) but given defaults or factories must still be assigned automatically and must not be accepted as constructor arguments, ensuring hidden state remains consistent regardless of caller-provided kwargs ordering. (ref PR 32.json)

### Nullable Attribute Contracts
- [SHOULD] Provide dedicated optional validators for nullable fields: When an attribute may legitimately be `None`, wrap its validator in an optional adaptor that bypasses validation for `None` but still enforces type/interface rules for real values, and cover both paths—including subclass/interface acceptance and failure cases—in tests. (ref PR 16.json, PR 17.json)

## Representation & Introspection
### Dunder Behavior
- [MUST] Derive `__repr__` names from the runtime class hierarchy: Generated `__repr__` implementations must inspect the actual instance class (including subclasses without extra attrs) to derive the displayed qualified name so that redecorated or dynamically generated subclasses produce accurate representations. (ref PR 20.json)

## Validation & Runtime Efficiency
### Validator Execution
- [SHOULD] Iterate over cached `__attrs_attrs__` when validating: Validator runs should traverse the stored attribute metadata rather than recomputing `fields()` each time, preserving the original attribute order and avoiding redundant work on every initialization. (ref PR 29.json)

## Data Model Compatibility
### Slots Parity
- [SHOULD] Maintain feature parity between slot classes and regular classes: When introducing `slots=True` support, ensure all generated dunder methods, validation, inheritance flows, and helper APIs (`fields`, `asdict`, `make_class`, parametrized tests) exercise both slot-backed and dict-backed variants so behavior stays consistent regardless of storage model. (ref PR 35.json)
