"""Bounded AFC Phase-I finite-state recovery algorithm transfer.

Port source: INVARIANT_FINAL_PHASE_I, source/src/science.py:afc_finite_limits.
Finite arithmetic only (2..10 bits). Does NOT demonstrate physical/hardware
reversibility, zero dissipation, clinical effectiveness, or general laws.
"""
from __future__ import annotations

from typing import Any

CLAIM_BOUNDARY = (
    "Elementary finite-state injectivity and recovery examples with explicit "
    "side-information cost. Not a universal physical law, erasure-free hardware "
    "demonstration, clinical validation, or independent venture-domain experiments."
)
ORIGINAL_PHASE_I_ZIP_SHA256 = "469f3eedb6c26f601dc2357f029364a2b3974cfbd3d937385d1dfe5c2840231e"
ORIGINAL_RESULT_MEMBER_SHA256 = "02167c798d3f2e56fed9e9c0966f6ab3a151bd4e5e4747a5e6ed40472c844f2e"


def _bits(bits: int) -> int:
    if type(bits) is not int or not 2 <= bits <= 10:
        raise ValueError("AFC_FINITE_BITS_2_TO_10_ONLY")
    return bits


def encode_permutation(x: int, bits: int) -> int:
    """Exactly follows original fixed finite permutation y=(5x+3) mod 2^bits."""
    n = 1 << _bits(bits)
    if type(x) is not int or not 0 <= x < n:
        raise ValueError("AFC_FINITE_INPUT_OUT_OF_RANGE")
    return (5*x+3) % n


def decode_permutation(y: int, bits: int) -> int:
    n = 1 << _bits(bits)
    if type(y) is not int or not 0 <= y < n:
        raise ValueError("AFC_FINITE_INPUT_OUT_OF_RANGE")
    return ((y-3)*pow(5,-1,n)) % n


def quotient(x: int, bits: int) -> int:
    n = 1 << _bits(bits)
    if type(x) is not int or not 0 <= x < n:
        raise ValueError("AFC_FINITE_INPUT_OUT_OF_RANGE")
    kept = max(1,bits//2)
    return x % (1 << kept)


def recover_from_quotient(q: int, side: int, bits: int) -> int:
    """Original quotient + REQUIRED side-information; no silent recovery guess."""
    _bits(bits)
    kept = max(1,bits//2)
    if type(q) is not int or not 0 <= q < (1 << kept):
        raise ValueError("AFC_QUOTIENT_OUT_OF_RANGE")
    if type(side) is not int or not 0 <= side < (1 << (bits-kept)):
        raise ValueError("AFC_SIDE_INFORMATION_REQUIRED_OR_INVALID")
    return q + (1 << kept) * side


def finite_report(bits: int) -> dict[str, Any]:
    """Bounded deterministic report with original Phase-I field names."""
    _bits(bits)
    n = 1 << bits
    kept = max(1, bits//2)
    fibers: dict[int,list[int]] = {}
    perm=[]
    for x in range(n):
        perm.append(encode_permutation(x,bits))
        fibers.setdefault(quotient(x,bits),[]).append(x)
    inv_exact=all(decode_permutation(y,bits)==x for x,y in enumerate(perm))
    side_exact=all(recover_from_quotient(quotient(x,bits),x//(1<<kept),bits)==x for x in range(n))
    witness=next(v[:2] for v in fibers.values() if len(v)>1)
    return {
        'bits':bits,'states':n,'permutation_inverse_exact':inv_exact,
        'retained_bits':kept,'lost_bits':bits-kept,
        'best_uniform_exact_recovery_probability_without_side_information':len(fibers)/n,
        'collision_witness':witness,
        'side_information_bits_needed_for_full_uniform_recovery':bits-kept,
        'recovery_with_quotient_side_information_exact':side_exact,
    }


def product_diagnostic(bits: int) -> dict[str, Any]:
    """Read-only local product feature. The scientific claim remains scope-limited."""
    return {
        'schema':'invariant-os-afc-finite-diagnostic/4',
        'experiment':'afc_finite_limits',
        'research_programme':'AFC',
        'implementation':'DIRECT_FINITE_ALGORITHM_PORT',
        'scientific_validation':'SOURCE_BOUNDED_FINITE_ONLY',
        'source_zip_sha256':ORIGINAL_PHASE_I_ZIP_SHA256,
        'source_result_sha256':ORIGINAL_RESULT_MEMBER_SHA256,
        'result':finite_report(bits),
        'claim_boundary':CLAIM_BOUNDARY,
        'clinical_validation':False,
        'universal_physical_law':False,
        'physical_hardware_test':False,
    }
