"""Pure metric functions: distribution quality and avalanche behaviour.

Everything here is a function of plain numbers / callables, so it can be unit
tested without building a table.
"""

import math
import random
import string
from dataclasses import dataclass
from typing import Callable, Dict, List, Sequence


# ---------------------------------------------------------------- distribution
@dataclass
class DistributionStats:
    """How evenly keys spread over buckets.

    Ideal-random reference values (n keys, m buckets, alpha = n/m):
        empty fraction            ~ exp(-alpha)
        colliding pairs           ~ n(n-1) / (2m)
        chi-square / (m-1)        ~ 1
    """

    empty_bucket_ratio: float
    expected_empty_bucket_ratio: float
    avg_chain_length_nonempty: float
    stddev_chain_length: float
    colliding_pairs: int
    collision_ratio_vs_ideal: float  # colliding_pairs / ideal; ~1 = random-like, >1 = worse
    chi_square_normalized: float     # ~1 = uniform, >>1 = clustered


def distribution_stats(chain_lengths: Sequence[int]) -> DistributionStats:
    m = len(chain_lengths)
    n = sum(chain_lengths)
    if m == 0:
        return DistributionStats(0.0, 0.0, 0.0, 0.0, 0, 0.0, 0.0)

    alpha = n / m
    empty = sum(1 for c in chain_lengths if c == 0)
    non_empty = [c for c in chain_lengths if c]
    mean = alpha
    var = sum((c - mean) ** 2 for c in chain_lengths) / m
    pairs = sum(c * (c - 1) // 2 for c in chain_lengths)
    ideal_pairs = n * (n - 1) / (2 * m) if m else 0.0
    chi2 = sum((c - mean) ** 2 / mean for c in chain_lengths) if mean > 0 else 0.0

    return DistributionStats(
        empty_bucket_ratio=empty / m,
        expected_empty_bucket_ratio=math.exp(-alpha),
        avg_chain_length_nonempty=(sum(non_empty) / len(non_empty)) if non_empty else 0.0,
        stddev_chain_length=math.sqrt(var),
        colliding_pairs=pairs,
        collision_ratio_vs_ideal=(pairs / ideal_pairs) if ideal_pairs > 0 else 0.0,
        chi_square_normalized=(chi2 / (m - 1)) if m > 1 else 0.0,
    )


def weighted_average_probes(
    probes_per_key: Dict[str, int], frequency: Dict[str, int]
) -> float:
    """Average comparisons per lookup when keys are accessed with the real
    workload frequencies (hot identifiers count more)."""
    total = sum(frequency.get(k, 0) for k in probes_per_key)
    if total == 0:
        return 0.0
    return sum(p * frequency.get(k, 0) for k, p in probes_per_key.items()) / total


# ------------------------------------------------------------------- avalanche
_IDENT_ALPHABET = string.ascii_letters + string.digits + "_"
MIN_AVALANCHE_SAMPLES = 64
OUTPUT_BITS = 32
INPUT_BITS_PER_CHAR = 7  # flip bits 0..6 so the result stays plain ASCII


def avalanche_samples(identifiers: Sequence[str], minimum: int = MIN_AVALANCHE_SAMPLES,
                      maximum: int = 256, seed: int = 12345) -> List[str]:
    """Workload identifiers, topped up with deterministic synthetic identifiers
    when the workload is too small for a stable statistic."""
    samples = list(dict.fromkeys(i for i in identifiers if i))[:maximum]
    rng = random.Random(seed)
    while len(samples) < minimum:
        length = rng.randint(3, 12)
        first = rng.choice(string.ascii_letters + "_")
        samples.append(first + "".join(rng.choice(_IDENT_ALPHABET) for _ in range(length - 1)))
    return samples


@dataclass
class AvalancheResult:
    mean_flip_probability: float  # ideal 0.5
    worst_bit_bias: float         # max |p_bit - 0.5| over the 32 output bits; ideal 0
    quality: float                # 1 - 2*mean|p_bit - 0.5| in [0,1]; 1 = ideal
    trials: int


def avalanche(fn: Callable[[str], int], samples: Sequence[str]) -> AvalancheResult:
    """Strict-avalanche test: flip one input bit, count how often each of the
    32 output bits changes. A good hash flips each output bit ~50% of the time.

    Flipping bits 0..6 of each character keeps the input printable-ASCII so all
    functions (some work on code points, some on UTF-8 bytes) see equivalent
    input.
    """
    flips = [0] * OUTPUT_BITS
    trials = 0
    for s in samples:
        base = fn(s)
        for pos, ch in enumerate(s):
            code = ord(ch)
            for bit in range(INPUT_BITS_PER_CHAR):
                mutated = s[:pos] + chr(code ^ (1 << bit)) + s[pos + 1:]
                diff = base ^ fn(mutated)
                trials += 1
                for b in range(OUTPUT_BITS):
                    if (diff >> b) & 1:
                        flips[b] += 1
    if trials == 0:
        return AvalancheResult(0.0, 0.5, 0.0, 0)
    probs = [f / trials for f in flips]
    devs = [abs(p - 0.5) for p in probs]
    return AvalancheResult(
        mean_flip_probability=sum(probs) / OUTPUT_BITS,
        worst_bit_bias=max(devs),
        quality=max(0.0, 1 - 2 * sum(devs) / OUTPUT_BITS),
        trials=trials,
    )
