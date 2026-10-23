# Security boundary and non-claims

Status: **NEW_IMPLEMENTATION**, research prototype. This package is a finite
language/runtime with explicit validation and demonstrated negative tests. It is
**not a production sandbox**, verified kernel, hardened multi-tenant executor,
cryptographic authorization protocol, or proof of secure arbitrary code execution.

## Trusted and untrusted inputs

Treat source text, JSON arguments, imported source strings, serialized OCIR,
bytecode, model-generated programs, checkpoints, witness/provenance records, and
metadata as untrusted data. Parsing, static checks, structural validation,
resource guards, and operation-specific runtime validation narrow the accepted
subset. The implementation code, Python process, installed dependencies, selected
schema, and explicitly supplied host policy remain part of the trusted computing
base. Compromise of that host is outside the demonstrated boundary.

The language exposes no filesystem, socket, process, shell, dynamic evaluation,
Python object, importlib, or FFI primitive. Module resolution receives an explicit
bounded mapping of module names to source strings. It does not search the host
filesystem or network. These language-level restrictions do not isolate a buggy
Python implementation from its host process.

CLI file reads/writes are host operations requested by the person invoking the
CLI. They are not permissions granted to an ICL program. Read paths reject
symlinks and require bounded regular UTF-8 files, but this check is not a complete
filesystem containment or race-resistant policy. Output paths are host-selected
paths. Run hostile workloads in a separately restricted process/container with
operating-system CPU, memory, filesystem, and network controls; this package does
not install those controls or claim they were production-audited.

## Authority and effects

Authority is supplied only by the trusted host `policy` argument or CLI
`--policy` file. The source, OCIR, a nominal `Capability`, witness, provenance
hash, model output, or checkpoint cannot grant permission. `Capability` is a
reserved type spelling whose runtime boundary rejects value instances in v0.1.
Provenance fields and observer identities are descriptive data.

The sole permitted action is an **in-memory local journal event**. To allow
`request_effect("journal", payload)`, the host policy must explicitly set
`journal.allow` to Boolean true. When `human_required` is true, the host must also
set `human_approved` true. Every event records `external_executed: false`.
Unsupported actions and absent grants are denied. These approval flags are
host-supplied test/policy inputs, not an implementation of a human approval UI or
verification that an actual human consented.

No language effect sends a message, writes a file, changes a permission, executes
a command, contacts a service, controls a device, or performs a privileged host
operation. An allowed journal event must not be reported as evidence that any such
external action occurred.

## Checksums, checkpoints, and provenance

Canonical SHA-256 hashes detect accidental content changes and identify exact
bytes/structures under the local serialization convention. All these hashes are
**unkeyed**. They are not signatures, message authentication codes, identities,
proof of authorship, authorization credentials, tamper-proof storage, or factual
verification. Anyone controlling a payload can recompute its checksum.

Checkpoint replay validates stored state structure and bytecode identity, and
requires the independently supplied trusted host policy to equal the checkpoint's
policy audit metadata. Omitted host policy means `{}`; the runtime never restores
grants from a checkpoint. The regression suite includes a checkpoint whose
attacker-controlled policy and checksum were both rewritten; that checkpoint
cannot supply a grant when replayed under the default host policy.

Structural checks and hashes do not establish that every otherwise well-formed
checkpoint state originated from an earlier authorized execution. There is no
secret signing key, authenticated snapshot store, general state-transition proof,
anti-rollback counter, or freshness guarantee. A changed executable with a newly
computed identity is a different executable, not cryptographically detected
malice. Use a separate trusted transport/store or signing design if provenance or
adversarial authenticity is required.

Witness checks ensure consistency of the declared integer-modulo recovery data.
They do not authenticate a measurement or witness producer. `provenance(id)` is
explicitly marked `verified: false`. Observer/frame/unit string comparisons do not
authenticate observer identities or establish physical calibration.

## Validation and resource boundaries

The supported public source/OCIR path performs parsing, type checking, metadata
validation, duplicate JSON key rejection, schema/hash compatibility checks,
recomputed operation/effect validation, and execution guards. Unknown opcodes and
operators, invalid pointers/counts, malformed type signatures, stack underflow,
out-of-range indices, mismatched frames/units, and finite numeric violations fail
with ICL diagnostics on the tested paths. The bytecode backend does not execute
generated Python source and does not expose arbitrary callables.

Runtime limits restrict logical fuel, call depth, finite values, tensor sizes,
and checked output sizes. They do not precisely account for Python allocation,
CPU time, serialization overhead, all transient copies, or every scalar operation
inside a tensor primitive. Bounds are not a guarantee against denial of service
in a shared host process. The host needs independent memory/time cancellation
controls for that threat model.

The source/OCIR API is the supported semantic boundary. Direct low-level helper or
bytecode calls do not add a theorem that arbitrary handcrafted bytecode has all
source-language typing invariants. Dynamic checks reject documented malformed
cases; this finite adversarial suite is evidence about those cases only.

## Independence and reporting discipline

The tree evaluator and VM have independent control flow and storage mechanisms,
but share arithmetic, built-ins, numeric checks, and metadata helpers. A shared
primitive bug can pass a differential comparison. Neither the test count nor a
content hash establishes general security, soundness, physical validity, or model
capability. Trace hashes are reproducibility/integrity evidence, not signed
attestation. The PRNG is deterministic and unsuitable for cryptographic secrets.

Mark an unavailable or unexecuted security/effect/model scenario `NOT_RUN`.
Preserve denials and negative results. Any future integration that turns journal
requests into real host effects requires a new reviewed boundary and cannot
inherit an unqualified security claim from this prototype.
