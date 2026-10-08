"""Single source of truth for the terms used in reports, the frontend and the docs."""

from typing import Dict

DEFINITIONS: Dict[str, str] = {
    "full_hash_collision": (
        "Two distinct identifiers a != b whose complete 32-bit hash values are equal: "
        "h(a) == h(b). A property of the hash function alone; no table size can fix it."
    ),
    "bucket_collision": (
        "Two distinct identifiers that land in the same bucket of an m-bucket table: "
        "h(a) mod m == h(b) mod m. Depends on the hash function AND the table size. "
        "'collisions' counts insertions of a new identifier into an already occupied bucket. "
        "Every full-hash collision is a bucket collision, never the reverse."
    ),
    "colliding_pairs": (
        "Number of unordered identifier pairs that share a bucket: the sum over buckets of "
        "C(chain_length, 2). Unlike 'collisions' it grows quadratically with long chains."
    ),
    "collision_ratio_vs_ideal": (
        "colliding_pairs divided by n(n-1)/(2m), the value expected from a perfectly random "
        "hash. About 1.0 = random-like, above 1 = worse than random."
    ),
    "load_factor": "Stored identifiers divided by bucket count (n / m).",
    "weighted_avg_probes": (
        "Average key comparisons per successful lookup when identifiers are accessed with their "
        "real frequencies in the program (hot identifiers count more). Deterministic."
    ),
    "chi_square_normalized": (
        "Chi-square statistic of the chain lengths divided by (m-1). About 1.0 = uniform "
        "spread, much larger = clustering."
    ),
    "avalanche_quality": (
        "Flip one input bit and see which of the 32 output bits change. A good hash flips each "
        "about 50% of the time. Quality = 1 - 2 * mean |p - 0.5|; 1.0 is ideal."
    ),
    "collision_resistance": "Infeasible to find any pair x != y with h(x) = h(y).",
    "preimage_resistance": (
        "Given only a digest d, infeasible to find any input y with h(y) = d."
    ),
    "second_preimage_resistance": (
        "Given an input x, infeasible to find a different y with h(y) = h(x)."
    ),
    "effort_ratio": (
        "Mean random candidates needed to hit a truncated digest, divided by 2^bits. About 1.0 "
        "= no better than brute force. Sampling error is roughly +/-20%; this is a relative "
        "indicator, not a security proof."
    ),
    "structural_second_preimage": (
        "A cheap constructive second preimage found by a bounded local-edit search on the full "
        "32-bit digest. Its presence shows a real weakness; its absence proves nothing."
    ),
    "scope_hops": "Scopes visited while resolving a name outward from the current scope.",
}
