# Operational semantics and evidence scope

Status: **NEW_IMPLEMENTATION**, finite ICL-Core 0.1. This is an operational
description of executable behavior, not a machine-checked semantics or a general
soundness theorem. The implementation may be revised when a differential test
exposes a discrepancy; such a fix is not retrospective evidence for untested cases.

## Evaluation and control flow

The source path is lexer/parser → explicit module resolution → static checker →
OCIR validation → selected execution backend. The tree backend recursively walks
the AST. The compiler lowers the checked AST to a JSON bytecode stream, and the VM
executes it through a program counter, operand stacks, call frames, and lexical
scope stacks. The VM never delegates control flow or expression evaluation to the
tree evaluator. Both backends share checked scalar arithmetic, tensor/metadata
built-ins, runtime value checks, and resource accounting.

Arguments, list/tuple items, and binary expression operands evaluate left to
right. Record field expressions evaluate in lexicographic field-name order,
independent of their written order; canonical JSON sorting therefore preserves
PRNG/effect order across source and restored OCIR. `&&` evaluates
its right operand only when the left is true; `||` evaluates its right operand
only when the left is false. Boolean conditions are strict. A new function frame
contains parameter bindings; its body introduces a child lexical scope. Branch
blocks and each entered loop body introduce fresh child scopes. Return exits the
entire function, including nested scopes. A loop's declared bound counts body
entries; condition checks are also charged against the global execution budget.

The checker examines all function bodies and both branches, including unreachable
source portions. Effect reporting is consequently conservative and module-wide,
not a path-sensitive prediction of what one invocation will execute. Calls to
`request_effect` record required effect `policy_request`; calls to `random_int`
record `prng`. No user effect declarations or polymorphic effect types exist.

Function values and arguments are ordinary finite data. Source mutation changes a
binding; source offers no shared mutable heap reference. VM loads copy values,
and built-ins construct their result data. Lists and tuples share JSON array
representation but not static type. Record field compatibility is structural for
inferred local record types. Tensor shapes are validated both statically where
known and by consuming runtime operations.

## Numerical interpretation

Int64 operations check the signed range `[-2^63, 2^63-1]`; overflow does not wrap.
Division truncates toward zero. For integers, remainder is `a - trunc(a/b)*b`.
Float64 uses the host's finite double-precision arithmetic and elementary
functions. Zero division and nonfinite results are errors. There is no promise of
bitwise floating-point reproducibility across different host math libraries.
The OCIR numeric comparison policy declares `atol=1e-6` and `rtol=1e-5` for numeric
conformance comparisons; these tolerances do not modify source `==` semantics.

Tensor multiplication, reductions, activations, normalization, and softmax run in
the shared finite primitive registry. Normalization and softmax process the final
dimension in row-sized groups. Softmax subtracts the row maximum before
exponentiation. Normalization uses `(x-mean)/sqrt(variance+1e-5)`.

## Observer/context metadata

`represent(v,o,f,u)` constructs a value plus observer identifier, frame, unit,
source-content hash, and a local-computation provenance record. `repr_add(a,b)`
checks equal observer identifiers, equal frames, and equal units at runtime.
It rejects mismatches with `OBSERVER_MISMATCH`, `FRAME_MISMATCH`, or
`UNIT_MISMATCH`. The checker checks value types but does not prove equality of
these runtime metadata strings. There is no implicit alignment or conversion.

The only registered conversion is `affine_translation_v1`, implemented as numeric
addition of an explicitly supplied offset followed by recording the destination
frame and conversion metadata. Other protocol strings fail with `NEEDS_EVIDENCE`.
This is not a physical calibration system: no external measurement validates the
offset, units, frame identity, or observer identity. Metadata hashes verify
content relationships within this local protocol, not the truth of observations.

## Recovery and witness cost

`observe_mod(x,m,o)` requires positive integer `m` and observes `x mod m`. It marks
the representation as ambiguous and removes the source-content hash. Many
integers produce the same observation. `recover_without_witness` therefore fails
with `NON_IDENTIFIABLE`; the runtime does not infer a unique hidden integer.

`make_witness(x,m)` stores the quotient `x // m`, positive modulus, remainder, and
an unkeyed SHA-256 checksum. `recover(rep,w)` checks the witness tag/checksum and
consistency of modulus and remainder, then reconstructs `quotient*m + remainder`
with Int64 validation. It returns an `Exact[Int64]` value whose scope is
`declared_integer_modulo_protocol`. This claim is limited to the supplied witness
and measurement protocol. It does not recover discarded information without
auxiliary storage or demonstrate a general inverse for arbitrary measurements.

The returned `witness_bytes` reports the constructor's canonical UTF-8 payload
length after the checksum is added but before the `payload_bytes` field itself is
inserted. It therefore excludes its own counter field, Python object overhead,
checkpoint/trace overhead, and transport framing. Report it as measured witness
payload cost under this convention, not total storage or zero-cost recovery.
The witness checksum does not authenticate the producer or prevent a party from
rewriting both payload and checksum. `approx(v,e)` similarly carries a declared
nonnegative Float64 error bound without independently verifying it.

## Policy, PRNG, and trace

`request_effect(action,payload)` consults a separate host policy. Only action
`journal` can be permitted. It requires an entry with `allow: true`; if that entry
has `human_required: true`, it also requires `human_approved: true`. An allowed
request appends an in-memory event with `external_executed: false` and decision
`ALLOWED_LOCAL_JOURNAL`. All other requests fail. No request performs filesystem,
network, process, device, or privileged host operations.

Each fresh runtime starts its deterministic PRNG state at `1` and updates it by
`state = (1103515245*state + 12345) mod 2^31`. `random_int(n)` returns `state mod n`
for positive `n`. This simple reproducible generator is not cryptographic and is
not guaranteed to be unbiased for arbitrary ranges. The VM serializes its state
in checkpoints.

Trace events use `clock_mode: logical`, a deterministic run identifier, sequential
steps, operation identifiers, input/output hashes, state references, and optional
effect/error/recovery fields. They are logical execution evidence, not wall-clock
timings or signed attestation. VM `BC:*` events hash actual pre/post call frames,
lexical locals, operand stacks, loop counters, program counters, and PRNG state;
the final return event also hashes the returned value. Effect events populate the
request and decision fields. Tree expression events hash visible scope/PRNG input
and computed values; tree statement events are execution markers and need not
contain a value payload. Not every optional trace field is populated by every
operation.

The two engines have different execution granularity, trace format details, and
step counts. Conformance compares computed results and relevant failure behavior,
not equality of tree and VM trace hashes. Equal stateful replay traces are tested
for repeated execution within the VM implementation. Hashing intermediate state
can itself be computationally expensive and is not a zero-overhead guarantee.

## Checkpoints and resource limits

VM checkpoint schema `icl-vm-checkpoint/1` contains the bytecode identity hash,
call frames, lexical locals/mutability tables, operand stacks, loop counters,
instruction pointers, accumulated steps/trace/effects, PRNG state, resource limits,
policy audit metadata, and an integrity checksum. A paused result has
`halted: false`, `value: null`, and `checkpoint`; completion has `halted: true`.
`stop_after` bounds additional VM instruction steps before pausing.

Resume verifies integrity, bytecode identity, bounded structural fields and stored
accounting; it restores the state and continues the same accumulated trace.
Resource limits may only remain equal or tighten. The trusted host must supply the
same policy independently on resume; omission means default-deny `{}`. Stored
policy data is never adopted as authority. Program arguments are already in the
stored frames; at the higher-level API, the declared entry argument contract must
still be supplied and validated. Checkpoints are implementation-specific and not
a general cross-version continuation interchange standard.

| Runtime limit | Default maximum | Meaning |
|---|---:|---|
| `max_steps` | 100000 | Engine-accounted logical steps |
| `max_stack` | 128 | User-function call depth |
| `max_items` | 100000 | Checked finite value item budget |
| `max_output` | 1000000 | Checked serialized/string output size budget |
| `max_tensor` | 4096 | Tensor element count |

Host settings may reduce these defaults. Value nesting has an additional depth
bound of 128. Source has a 1 MB limit, at most 100000 tokens, and numeric tokens
have a 128-character limit. Expression parser nesting is bounded at 150.
These checks do not constitute an operating-system memory limit or a CPU timeout;
one tensor primitive can perform many scalar operations under one language call.

## What the comparisons establish

The independent dispatch and control-flow implementations catch different classes
of parser/lowering/scope/branch bugs. They are not independent implementations of
every primitive: shared arithmetic, tensor functions, nominal metadata validation,
and some runtime helpers can introduce correlated errors. Passing differential
tests therefore does not establish formal soundness, general equivalence, correct
physical semantics, or correctness on all inputs. Negative/error outcomes and
unsupported cases must remain visible rather than be reclassified as success.
