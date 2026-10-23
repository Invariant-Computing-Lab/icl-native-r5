# ICL-Core 0.1 language specification

Status: **NEW_IMPLEMENTATION**. This document describes the finite implementation
in this package, not an established OCIL language standard or a claim that older
Invariant Computing prototypes already implemented these semantics. The executable
sources in `icl/frontend.py`, `icl/checker.py`, `icl/runtime.py`, `icl/api.py`,
`icl/interpreter.py`, and `icl/vm.py` are the implementation reference.

## Program structure

Every source begins with `module NAME;`, followed by zero or more `import NAME;`
declarations and one or more named function declarations. Function parameters and
return types require annotations. Local `let` and `var` annotations are optional.
The entry function defaults to `main` and may receive explicitly supplied JSON
arguments through the host API. There are no ambient command-line arguments or
environment variables inside the language.

```icl
module demo;

fn square(x: Int64) -> Int64 {
    return x * x;
}

fn main() -> Int64 {
    var i: Int64 = 0;
    var total: Int64 = 0;
    while i < 4 limit 4 {
        total = total + square(i);
        i = i + 1;
    }
    return total;
}
```

This program returns `14`. An assignment changes a previously declared `var`.
Parameters and `let` bindings are immutable. Blocks create lexical scopes; an
inner declaration can shadow an outer binding, including a function parameter.
Duplicate declarations in the same body scope are rejected. Assignments search
outward and update the nearest visible mutable binding. Calls evaluate arguments
from left to right and use fresh function environments. Recursive named calls are
supported within the configured call-depth and execution budgets.

Imports are resolved only from the host-supplied `module_map` mapping names to
source strings. Imported declarations are called as `module.function(...)`.
Missing modules, declaration/name mismatches, and import cycles are rejected.
Import declarations do not read files, search packages, fetch URLs, or load Python.
The loader accepts at most 64 map entries and an active import nesting depth of 32.

## Lexical and expression syntax

See `grammar.ebnf` for the concrete grammar. Identifiers use ASCII letters,
underscores, and subsequent digits. Keywords are `module`, `import`, `fn`, `let`,
`var`, `if`, `else`, `while`, `limit`, `return`, `true`, and `false`. Comments run
from `//` to the end of a line. Strings use double quotes and JSON-style escapes.
Source must be UTF-8 text. Raw format/surrogate Unicode characters and unsupported
control characters are rejected; decoded unpaired surrogate strings are rejected.

The precedence table is ordered from weakest to strongest. Operators on each
binary row associate left to right.

| Operators | Meaning |
|---|---|
| `\|\|` | Short-circuit Boolean disjunction |
| `&&` | Short-circuit Boolean conjunction |
| `==`, `!=` | Same-type equality or inequality |
| `<`, `<=`, `>`, `>=` | Ordered scalar comparison |
| `+`, `-` | Numeric addition/subtraction; `+` also joins two strings |
| `*`, `/`, `%` | Numeric multiplication/division/remainder |
| unary `!`, unary `-` | Boolean negation; numeric negation |
| call, `[index]`, `.field` | Named call; indexing; record field selection |

Literal examples are `12`, `1.5`, `2e3`, `true`, `"text"`, `[1, 2]`,
`(1, "x")`, and `{count: 1, label: "x"}`. There is no null literal or empty
tuple. A one-element parenthesized expression is grouping, not a tuple.
Empty lists parse but fail type checking because contextual empty-list typing is
not implemented. Empty records may be inferred internally. Record field names
are identifiers, and duplicate literal fields are rejected. Record field
expressions evaluate in lexicographic field-name order, independent of their
written order. This explicit rule preserves behavior when canonical JSON sorts
the AST's field mapping, including fields that consume PRNG state.

## Types and finite data model

| Type | Implemented behavior |
|---|---|
| `Int64` | Signed 64-bit integers, checked overflow |
| `Float64` | Finite host double-precision values; NaN/Infinity rejected |
| `Bool` | `true` and `false`; no implicit numeric conversion |
| `String` | Unicode string, bounded serialized output |
| `List[T]` | Homogeneous finite list; bounds-checked integer indexing |
| `Tuple[T1,T2,...]` | Fixed heterogeneous tuple; literal integer indexing |
| inferred record | Named fields and structural field access |
| `Tensor[d1,...]` | Dense Float64 tensor of literal positive shape, rank 1–3 |
| `Option[T]`, `Result[T]` | Tagged values through the finite constructors below |
| `Representation[T]` | Value with explicit observer, frame, unit, and provenance metadata |
| `Exact[T]`, `Approx[T]` | Scoped recovery result or explicitly declared approximation bound |
| `Observer`, `Context`, `ProvenanceRef`, `RecoveryWitness` | Nominal metadata records |
| `Capability` | Reserved nominal spelling; no constructible transferable authority value |

The bracket notation above denotes built-in type constructors. User-defined
generic functions, type parameters, generic declarations, type aliases, and
user-defined algebraic data types are **not implemented**. Record types are
inferred for local expressions; record annotations in source-level parameter,
return, or local type syntax are **not implemented**. Records can therefore be
constructed and inspected within a function without being advertised as general
annotated record APIs. Lists and tuples serialize as JSON arrays, while their
static types remain distinct.

Both operands of arithmetic/comparison must have compatible types; there is no
implicit Int64/Float64 promotion. `to_float` performs an explicit conversion and
can lose integer precision. Integer division truncates toward zero and the
remainder is consistent with that quotient. Zero divisors fail. Minimum Int64
`-9223372036854775808` is supported. Float operations must remain finite; results
are not interval arithmetic or formally verified numerical bounds.

Tensor shapes are concrete rather than symbolic. Shape literals and matching
element counts are checked; matrix multiplication requires two rank-2 tensors
with matching inner dimensions. Default maximum tensor size is 4096 elements.
The tensor layer is a small host implementation, with no language-level automatic
differentiation, broadcasting, GPU execution, or arbitrary-rank tensors.

## Built-in operations

The runtime registry is the authoritative finite list. Arguments are positional.
`N` below means one consistent numeric type, and `T` indicates a supported value
type rather than user-definable generics.

| Family | Operations and contracts |
|---|---|
| Scalars | `len(String or List[T]) -> Int64`; `abs(N) -> N`; `min(N,N) -> N`; `max(N,N) -> N`; `to_float(Int64) -> Float64` |
| Tensor creation | `tensor(List[Float64], literal_shape) -> Tensor[...]`; `reshape(tensor, literal_shape)` preserves element count |
| Tensor arithmetic | `matmul(a,b)`; same-shape `add(a,b)`, `sub(a,b)`, `mul(a,b)` |
| Tensor transforms | `relu(a)`, `tanh(a)`, `normalize(a)`, `softmax(a)`; `sum(a) -> Float64` |
| Option/Result | `some(value)`, `none_int()`, `ok(value)`, `err_int(String)`, `unwrap(value)`, `is_some(option)` |
| Metadata | `observer(String)`, `context(frame:String,unit:String)`, `provenance(String)` |
| Representations | `represent(value,observer:String,frame:String,unit:String)`, `repr_value(rep)`, numeric `repr_add(a,b)` |
| Explicit conversion | `convert_frame(rep,new_frame:String,offset:N,protocol:String)`; only `"affine_translation_v1"` |
| Recovery | `observe_mod(x:Int64,m:Int64,observer:String)`, `make_witness(x:Int64,m:Int64)`, `recover(rep,witness)`, `recover_without_witness(rep)`, `exact_value(exact)` |
| Approximation | `approx(value:Float64,error_bound:Float64)`, `approx_value(approx)` |
| Effects | `request_effect(action:String,payload:String) -> Bool` |
| Deterministic random | `random_int(positive_range:Int64) -> Int64` |

`unwrap` on None/Err fails; it does not invent a default. `is_some` accepts an
Option. `none_int` and `err_int` intentionally cover Int64 only. Normalization and
softmax operate over rows of the final tensor dimension; normalization uses
epsilon `1e-5`. Metadata constructors do not establish external facts or confer
authority. `approx` records a caller-declared nonnegative bound; it does not prove
that bound against an unavailable exact value.

## Control flow and unsupported features

`if condition { ... } else { ... }` requires a Bool condition; `else` is optional.
An else-if requires an explicit nested block. `while condition limit N { ... }`
requires a literal integer `N` from 0 through 100000. Exceeding this body-iteration
budget fails even if more global steps remain. The checker conservatively
requires every function to return on all paths; a return only inside a loop does
not satisfy this condition.

There are no first-class functions, lambdas, closures, function values, methods,
dynamic dispatch, exceptions in source, `for`, `break`, `continue`, mutation of
individual list/record elements, user heap references, async/concurrency, files,
sockets, shell/FFI access, dynamic code evaluation, or implicit package discovery.
There is no general proof of type soundness, termination, equivalence, or recovery.
The tests establish only the documented finite fixtures and executed comparisons.

## Public toolchain

`compile_source` parses, resolves explicit modules, checks types, and emits OCIR
version `0.1.0`. `dumps_ocir` and `loads_ocir` validate canonical JSON persistence;
`validate_ocir` verifies schema identity, content integrity, AST structure,
recomputed typing/effects, and program identity. `run_source` and `run_ocir` select
the `tree` or `vm` backend. VM checkpoints use `stop_after` and `checkpoint`.
Tree checkpoint/replay is explicitly unsupported.

CLI commands are `icl check`, `icl compile -o FILE`, `icl run`, `icl inspect`,
`icl replay`, and `icl test`. JSON is the default output; the CLI's `test` command
is a three-fixture smoke test and is not the complete acceptance suite. Source
imports still require an explicit JSON `--module-map` file. A `--policy` file is a
trusted host input, not part of executable authority. See `SEMANTICS.md` and
`SECURITY_BOUNDARY.md` before interpreting traces, recovery, or policy results.
