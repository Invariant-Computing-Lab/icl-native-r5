# ICL-Native R5 — Model Card

## Identity and actual task
New random-initialized, **2774-parameter**, bounded semantic opcode kernel. Base model: null. OCIL-Core 0.2.1; ICL graph `model.icl` is parsed/type checked and executed by a Torch training adapter. Offline deployment evaluates the same trained weights through the ICL VM with Python standard library only. This is not the unrecovered R4 model, an LLM, unrestricted source generation, or a clinical model.

Input: one of 16 explicit intents, eight effective Boolean context/state fields, and six numeric nuisance features. Output: one of 22 opcode/error classes. The controller visits a supplied plan of 1–32 steps. It is **not a learned autoregressive plan-length decoder**. Memory availability is derived from actual runtime state rather than trusting a caller's memory-present flag. Exact values, memory storage and numerical recovery are deterministic. Confidence is uncalibrated.

## Training and data
20 epochs, 1,080 optimizer updates per run, 20,000 training task roots/110,235 local node labels; 2,000 validation task roots. Three seeds 17, 29, 43 for native, flat and four ablations; 18 real runs. Model selection uses validation CE only. Numeric nuisance values are randomized in augmentation; observer/witness flags are not derived from number residues. No old closed/clinical bank or external model weights is used. Labels after a first error are auxiliary local supervision, not an actual continuing execution trace.

## Metrics (mean of three seeds)
| Variant | ID 2,000 | Long 2,000 | Flag-paired 4,000 |
|---|---:|---:|---:|
| native | 1.000000 | 1.000000 | 1.000000 |
| flat | 0.998500 | 0.996000 | 0.998250 |
| no_context | 0.727167 | 0.497833 | 0.626667 |
| no_witness | 0.917000 | 0.869500 | 0.866250 |
| no_memory | 0.947000 | 0.939500 | 0.940000 |
| no_invariance | 1.000000 | 1.000000 | 1.000000 |

Metric = **raw semantic opcode-prefix exact match across all supplied plans**, before a verifier can turn an incorrect action into a rejection. Positive/negative/per-intent/selective-risk details are in reports/evaluation. Grammar validity comes from the emitter and is not credited as learned syntax. Long-plan success uses deterministic composition and state execution; it does not establish learned long-horizon planning.

The input-program AST audit is split-disjoint after literal erasure. Specialized output strings, especially early errors, overlap across splits; the audit lists those overlaps. It would be wrong to present these results as novel source-program generation. The 602,112-case per-seed grid enumerates all effective Boolean contexts at 147 sampled numeric combinations, NOT all possible integers. It found no errors in that finite grid.

## Comparisons and negative findings
The flat baseline has 2,758 parameters. Training wall-time ratio native/flat is 0.448806; the requested ±10% budget match is not met. Even though the paired long-task difference is 0.004, confidence interval [0.002333, 0.005833] conditional on these seeds, **superiority is not established**. Removing the extra consistency loss gave the same perfect task score; no independent gain for that objective is demonstrated. Domain/semantic generalization beyond this finite task is untested.

## Recovery and authority
`restore` simulates loss and recovery of a known x by generating its witness inside the program. It is not recovery of unavailable information. Observer/witness Boolean flags describe synthetic scenarios, not authenticated external facts. Only an in-memory local journal can be permitted by an independent host setting; there is no shell/network/device/email/clinical adapter. Local console records files through host code, distinct from language-program capabilities. Hash checks are not signatures. A Python audit hook is not an OS sandbox.

## Reuse and distribution
Code, actual safe-tensor checkpoints, optimizer/RNG states, graph, raw predictions, source maps and tests are included. Keep private. No license grant or public publication decision is invented; source-study/third-party rights remain separate.
