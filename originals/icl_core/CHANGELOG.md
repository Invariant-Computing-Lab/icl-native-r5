# Changelog

## 0.1.0 — 2026-10-10

New hand-written lexer/parser, lexical/type/effect checking, typed canonical OCIR, independent tree interpreter and stack VM, bounded execution, deterministic PRNG checkpoint/replay, nominal observer/recovery values, explicit local policy adapter, tensor graph registry and six CLI subcommands. Added more than the required semantic/adversarial/generated fixtures and eight executable demos.

Preserved old ISC16/runtime/Trace Kernel behavior separately. Reused `finite_recovery.py` byte-for-byte as `icl/legacy_afc.py`; 2,044 finite state comparisons independently check the new witness protocol against this bounded legacy implementation.

Development failures were found and corrected before freeze: minimum Int64 literal handling, mismatched bounds diagnostics, seeded generator builtin-name collision, duplicate generated source/argument cases, malformed metadata values, unsafe compiled-budget override, checkpoint authority preservation, canonical record evaluation/replay identity, and non-Boolean host approval fields. See development findings and root review logs; initial failures are not silently presented as successful runs.

Unsupported: first-class functions/closures, user-defined generics, record type annotations, async/concurrency, native LLVM/WASM codegen, general symbolic/inverse solver, GPNT/DCT/SFT arithmetic replacement, untrusted-host isolation, external-effect rollback, production sandbox/security certification, clinical validity and universal research claims.
