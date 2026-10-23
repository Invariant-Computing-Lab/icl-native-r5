# ICL-Core acceptance tests

Run from a checkout with NumPy available:

```sh
python tests/run_acceptance.py
```

`FIXTURE_MANIFEST.json` provides each named source file, expected result or error,
arguments, explicit module map, trusted host policy, and resource bounds. The
`.icl` files themselves contain executable source rather than pseudocode. Fixtures
that require a module map or policy should be run through this manifest/runner;
those inputs intentionally are not authority literals in the source language.

The runner executes 77 manually authored programs and 1,008 seeded programs across
12 structural families on the independent tree interpreter and bytecode VM. Both
engines are additionally compared with separately calculated expected values;
matching engine bugs alone do not yield a pass. Shared scalar and builtin
primitives remain a known dependence between engines.

39 separately named hostile programs check type, nominal metadata, provenance,
policy, observer/frame/unit, recovery, numeric, shape, resource, lexer, import,
and host-evaluation failures. Another 30 contract checks cover serialization,
checksum/schema/opcode rejection, rehashed checkpoint policy forgery, PRNG replay,
a fresh-process restart, trace fields/state hashes, finite Float64 bit roundtrip,
source-line diagnostics, and input metadata validation. 19 CLI subprocess checks
cover all six subcommands, help, exit streams, module maps, checkpoint replay,
symlink input rejection, and a compressed archive with traversal name and 8 MB
expansion data. The CLI has no archive extractor; the archive is rejected as a
source file, and this does not claim the existence of a secure general extractor.

Eight NumPy reference graphs cover affine matmul/add, ReLU, tanh, reshape, row
normalization, softmax, a two-layer MLP, and residual-normalization-softmax. Oracle
code uses NumPy directly, never runtime tensor builtins. Float64 atol and rtol were
both fixed at 1e-10 before the first run. Integral equality is exact.

Evidence is written under `evidence/`. `DIFFERENTIAL_CASES.jsonl` contains every
seeded source, arguments, independent expected value, both engine outputs, and
AST pretty-print roundtrip decision. `TEST_RESULTS.json` summarizes observed
results. `DEVELOPMENT_FINDINGS.json` distinguishes corrected implementation bugs
from corrected test-harness errors; it is an issue log, not a reconstructed raw
execution log.

These tests establish finite implemented conformance, not universal correctness,
production sandbox isolation, general observer identifiability, or clinical
validity. The rank-deficient tests are explicitly small linear counterexamples;
the exact recovery test is only the declared integer-modulo witness protocol.
