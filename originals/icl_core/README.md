# Invariant Cognition Language — ICL-Core 0.1.0

A real finite language/toolchain owned by the OCIL/OCIR research programme and consumed by Invariant OS. This release is a **NEW_IMPLEMENTATION**, with one unchanged, attributed legacy AFC helper. It is not the old Runtime Console or ISC16 renamed.

## Offline installation

The runtime uses only Python 3.11+ standard library. Given the delivered wheel:

```bash
python -m venv .venv
.venv/bin/pip install --no-index --no-deps invariant_cognition_language-0.1.0-py3-none-any.whl
.venv/bin/icl test --json
.venv/bin/icl run examples/02_collision_sideinfo.icl --json
```

To build from source in an environment already containing setuptools and wheel:

```bash
python -m pip wheel --no-index --no-deps --no-build-isolation . -w dist
```

No runtime dependency download, network fallback, shell execution, or external service is used. NumPy is an independent test/model host dependency only; it is not imported by the language runtime. The package includes explicit schema/token vocab resources.

## Program and Python API

```text
module demo;
fn square(x: Int64) -> Int64 { return x * x; }
fn main() -> Int64 {
  var n = 0;
  while n < 3 limit 3 { n = n + 1; }
  return square(n);
}
```

```python
from icl.api import compile_source, run_source, run_ocir, dumps_ocir, loads_ocir
ocir = compile_source(source)
value = run_source(source, engine="vm")["value"]
assert value == run_source(source, engine="tree")["value"]
roundtripped = loads_ocir(dumps_ocir(ocir))
paused = run_ocir(ocir, stop_after=8)
resumed = run_ocir(roundtripped, checkpoint=paused["checkpoint"])
```

`icl check`, `run`, `compile`, `inspect`, `replay`, and `test` each support `--help` and JSON output. Diagnostics go to stderr with nonzero exit status. `compile` requires an explicit `-o` path. Imports use an explicit JSON module→source-text map via `--module-map`; there is no filesystem module search. See `examples/module_map.json` and `examples/08_module_main.icl`.

## Execution and trust scope

The tree interpreter and stack VM independently implement expression/control flow, while sharing checked primitive arithmetic and the builtin registry. Consequently differential success cannot exclude correlated primitive bugs. Eight NumPy comparisons separately exercise tensor graphs. Formal progress/preservation proofs and OS-level sandbox isolation are NOT_RUN.

Inputs, outputs, bounds, OCIR identity, version and checksums are checked. Record field evaluation is lexicographic by field name to preserve canonical serialization semantics, including PRNG/effects. Float tolerance is declared before tests, not chosen after outcomes. Observer/frame/unit compatibility is enforced at runtime; no dependent-type proof is claimed. Recovery is exact only for the explicit integer-modulo witness protocol. A checksum is not proof that a witness came from a trusted source.

Only an in-memory journal effect may be granted by strict Boolean fields in an independently supplied host policy. No email/network/filesystem/shell adapter exists. A model cannot generate a capability; replay ignores embedded authority unless it matches separately supplied trusted policy. The CLI itself can read specified inputs and write specified artifacts; that is distinct from language program capabilities.

## Reproduction

```bash
PYTHONPATH=. python tests/run_acceptance.py
PYTHONPATH=. python -m unittest discover -s tests -p test_vm_replay.py -v
PYTHONPATH=. python tests/run_demos.py
PYTHONPATH=. python tests/legacy_afc_comparison.py
```

The acceptance runner requires NumPy for independent graph parity. The original historical frozen studies and negative results are not rerun or modified. `SCIENCE_TO_CODE_TRACE.json` maps actual sources to design/code/tests and marks conceptual or deferred items. `LANGUAGE_HANDOFF.json` pins the final grammar/schema/source snapshot used by the native model. Its status must be `CONFORMANCE_PASSED` before training.
