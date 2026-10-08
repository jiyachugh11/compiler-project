"""Empirical preimage / second-preimage analysis for the hash functions.

Definitions (for a hash h and an identifier x):
    Preimage resistance         given only a digest d, it is infeasible to find
                                any input y with h(y) = d.
    Second-preimage resistance  given x, it is infeasible to find y != x with
                                h(y) = h(x).
    Collision resistance        it is infeasible to find ANY pair x != y with
                                h(x) = h(y).

Honest scope
------------
None of the hash functions in this project are cryptographic; these
properties are not their design goals. A symbol table only needs good
*distribution*. We still measure them, because a hostile or machine-generated
source file can exploit a weak hash (a "hash-flooding" attack that forces all
identifiers into one chain and degrades lookups from O(1) to O(n)).

Two complementary measurements, both on realistic identifier strings:

1. Brute-force effort on a *truncated* digest (default 10 bits). Full 32-bit
   brute force is cheap on a real machine but too slow for an interactive
   pipeline, so we measure how many random candidates are needed to hit an
   n-bit digest. A random-oracle hash needs ~2^n trials on average, so
   ``effort_ratio ~ 1.0`` means "no weaker than brute force". This is a
   *relative* indicator, not a security proof, and it carries sampling error
   of roughly +/- 1/sqrt(targets) (about 20% at 24 targets), so ratios
   between ~0.6 and ~1.5 are indistinguishable from 1.0. Ratios well above 1
   mean the truncated digest is clustered (some digests are hard to hit).
   SHA-256 (truncated the same way) is the cryptographic reference point.

2. A bounded structural second-preimage search on the FULL 32-bit digest: for
   real identifiers from the workload, try local edits (transpositions, and
   two-adjacent-character substitutions where the first character moves by up
   to +/-3). If any edit yields the same 32-bit digest, the function has a
   cheap constructive second preimage (e.g. DJB2: bump one character by +1 and
   drop its neighbour by 33). Finding nothing does NOT prove resistance; it
   only means this bounded search found no shortcut.
"""

import hashlib
import random
import string
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Sequence, Tuple

ALPHABET = string.ascii_letters + string.digits + "_"
_FIRST = string.ascii_letters + "_"


@dataclass
class SecurityResult:
    bits_tested: int
    targets_tested: int
    preimage_mean_trials: float
    preimage_effort_ratio: float          # mean trials / 2^bits ; ~1.0 = brute force only
    second_preimage_mean_trials: float
    second_preimage_effort_ratio: float
    structural_identifiers_tested: int
    structural_second_preimages_found: int
    structural_success_rate: float        # fraction of tested identifiers with a full-digest second preimage
    structural_example: Optional[Tuple[str, str]]  # (original, colliding identifier)
    verdict: str


def _random_identifier(rng: random.Random) -> str:
    length = rng.randint(4, 10)
    return rng.choice(_FIRST) + "".join(rng.choice(ALPHABET) for _ in range(length - 1))


def _brute_force(
    fn: Callable[[str], int], mask: int, target: int, rng: random.Random,
    exclude: Optional[str], cap: int,
) -> int:
    """Random candidates until fn(c) & mask == target. Returns trials used
    (``cap`` if not found)."""
    for trial in range(1, cap + 1):
        cand = _random_identifier(rng)
        if cand != exclude and (fn(cand) & mask) == target:
            return trial
    return cap


def _neighbours(ident: str):
    """Local edits of ``ident``: adjacent transpositions and adjacent-pair
    substitutions (first char moved by -3..+3, second char any)."""
    n = len(ident)
    for i in range(n - 1):
        a, b = ident[i], ident[i + 1]
        if a != b:
            yield ident[:i] + b + a + ident[i + 2:]
        for d in range(-3, 4):
            a2 = chr(ord(a) + d)
            if a2 not in ALPHABET or (d == 0):
                continue
            for b2 in ALPHABET:
                yield ident[:i] + a2 + b2 + ident[i + 2:]


def structural_second_preimage(fn: Callable[[str], int], ident: str) -> Optional[str]:
    """First local edit of ``ident`` with an identical full 32-bit digest."""
    target = fn(ident)
    for cand in _neighbours(ident):
        if cand != ident and fn(cand) == target:
            return cand
    return None


def analyze(
    fn: Callable[[str], int],
    identifiers: Sequence[str],
    bits: int = 10,
    targets: int = 24,
    structural_samples: int = 10,
    seed: int = 2024,
) -> SecurityResult:
    """Run both measurements for one hash function (deterministic for a seed)."""
    mask = (1 << bits) - 1
    cap = 20 * (1 << bits)
    rng = random.Random(seed)

    pool = [i for i in dict.fromkeys(identifiers) if len(i) >= 2]
    # Top up with synthetic identifiers so tiny workloads still give a stable number.
    synth_rng = random.Random(seed + 1)
    while len(pool) < targets:
        pool.append(_random_identifier(synth_rng))
    chosen = pool[:targets]

    pre_trials: List[int] = []
    sec_trials: List[int] = []
    for x in chosen:
        digest = fn(x) & mask
        # Preimage: the attacker only knows the digest; blind random search.
        pre_trials.append(_brute_force(fn, mask, digest, rng, exclude=None, cap=cap))
        # Second preimage: the attacker also holds x (and must output y != x).
        sec_trials.append(_brute_force(fn, mask, digest, rng, exclude=x, cap=cap))

    space = float(1 << bits)
    pre_mean = sum(pre_trials) / len(pre_trials)
    sec_mean = sum(sec_trials) / len(sec_trials)

    found = 0
    example: Optional[Tuple[str, str]] = None
    tested = pool[:structural_samples]
    for x in tested:
        y = structural_second_preimage(fn, x)
        if y is not None:
            found += 1
            if example is None:
                example = (x, y)
    rate = found / len(tested) if tested else 0.0

    if found:
        verdict = (
            f"Structural weakness: cheap second preimages exist on the full 32-bit digest "
            f"({found}/{len(tested)} identifiers, e.g. '{example[0]}' vs '{example[1]}')."
        )
    else:
        verdict = "No shortcut found by bounded search; behaves like brute force (not a security proof)."

    return SecurityResult(
        bits_tested=bits,
        targets_tested=len(chosen),
        preimage_mean_trials=pre_mean,
        preimage_effort_ratio=pre_mean / space,
        second_preimage_mean_trials=sec_mean,
        second_preimage_effort_ratio=sec_mean / space,
        structural_identifiers_tested=len(tested),
        structural_second_preimages_found=found,
        structural_success_rate=rate,
        structural_example=example,
        verdict=verdict,
    )


def sha256_reference(s: str) -> int:
    """SHA-256 truncated to 32 bits: the cryptographic reference baseline."""
    return int.from_bytes(hashlib.sha256(s.encode("utf-8")).digest()[:4], "big")


def analyze_all(
    functions: Dict[str, Callable[[str], int]],
    identifiers: Sequence[str],
    **kwargs,
) -> Dict[str, SecurityResult]:
    return {name: analyze(fn, identifiers, **kwargs) for name, fn in functions.items()}
