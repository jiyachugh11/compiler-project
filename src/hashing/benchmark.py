"""Benchmarking suite: runs every registered hash function through the
generic HashTable on a real identifier workload.

Design
------
* Insertion is timed over the *unique* identifiers (a symbol table stores each
  identifier once).
* Lookup is timed over the *full* identifier_stream, repeats included, because
  a compiler re-resolves an identifier at every use; this is the access pattern
  ``repetition_ratio`` describes.
* All functions get tables with the same bucket count, built the same way.
* Timings are the BEST of ``repeats`` runs. Workloads from small programs take
  microseconds, so a single run is dominated by noise; the minimum is the
  standard low-noise estimator.
* ``weighted_avg_probes`` is a deterministic, noise-free companion to lookup
  time: average key comparisons per lookup using real identifier frequencies.
"""

import time
from collections import Counter
from typing import Callable, Dict, List, Optional

from hashing.functions import HASH_FUNCTIONS, HASH_INFO
from hashing.hash_table import HashTable
from hashing.metrics import (
    avalanche,
    avalanche_samples,
    distribution_stats,
    weighted_average_probes,
)
from hashing.models import HashFunctionResult


def _default_bucket_count(unique_count: int, target_load_factor: float = 0.75) -> int:
    """Bucket count that lands near target_load_factor once all unique
    identifiers are stored. Always at least 1."""
    if unique_count <= 0:
        return 1
    return max(1, int(unique_count / target_load_factor))


class BenchmarkRunner:
    """Runs the full hash function comparison for one identifier workload."""

    def __init__(
        self,
        hash_functions: Optional[Dict[str, Callable[[str], int]]] = None,
        bucket_count: Optional[int] = None,
        target_load_factor: float = 0.75,
        repeats: int = 5,
    ) -> None:
        self.hash_functions = hash_functions or HASH_FUNCTIONS
        self.bucket_count = bucket_count
        self.target_load_factor = target_load_factor
        self.repeats = max(1, repeats)

    def run(
        self,
        identifier_stream: List[str],
        frequency: Optional[Dict[str, int]] = None,
    ) -> List[HashFunctionResult]:
        """Benchmark every registered function against ``identifier_stream``.

        Args:
            identifier_stream: Ordered identifier occurrences (Backend 1).
            frequency: identifier -> occurrence count. Derived from the stream
                when omitted (Backend 1 supplies it as workload_metrics.identifier_frequency).
        """
        unique = list(dict.fromkeys(identifier_stream))
        freq = frequency if frequency is not None else dict(Counter(identifier_stream))
        bucket_count = self.bucket_count or _default_bucket_count(
            len(unique), self.target_load_factor
        )
        samples = avalanche_samples(unique)

        results: List[HashFunctionResult] = []
        for name, fn in self.hash_functions.items():
            insert_best = lookup_best = hash_best = float("inf")
            table: HashTable = HashTable(bucket_count=bucket_count, hash_fn=fn)

            for _ in range(self.repeats):
                table = HashTable(bucket_count=bucket_count, hash_fn=fn)

                start = time.perf_counter()
                for ident in unique:
                    table.insert(ident, True)
                insert_best = min(insert_best, time.perf_counter() - start)

                start = time.perf_counter()
                for ident in identifier_stream:
                    table.contains(ident)
                lookup_best = min(lookup_best, time.perf_counter() - start)

                start = time.perf_counter()
                for ident in unique:
                    fn(ident)
                hash_best = min(hash_best, time.perf_counter() - start)

            dist = distribution_stats(table.chain_lengths())
            probes = {k: table.probes(k) for k in unique}
            aval = avalanche(fn, samples)
            info = HASH_INFO.get(name)

            results.append(
                HashFunctionResult(
                    name=name,
                    bucket_count=bucket_count,
                    items_inserted=table.size,
                    insert_time_sec=insert_best,
                    lookup_time_sec=lookup_best,
                    lookups_performed=len(identifier_stream),
                    collisions=table.collisions,
                    max_chain_length=table.max_chain_length(),
                    non_empty_buckets=table.non_empty_buckets(),
                    load_factor=table.load_factor(),
                    estimated_memory_bytes=table.estimated_memory_bytes(),
                    bucket_distribution=table.bucket_distribution(),
                    family=info.family if info else "",
                    hash_only_ns_per_key=(hash_best / len(unique) * 1e9) if unique else 0.0,
                    full_hash_collisions=table.full_hash_collisions,
                    colliding_pairs=dist.colliding_pairs,
                    collision_ratio_vs_ideal=dist.collision_ratio_vs_ideal,
                    empty_bucket_ratio=dist.empty_bucket_ratio,
                    expected_empty_bucket_ratio=dist.expected_empty_bucket_ratio,
                    avg_chain_length_nonempty=dist.avg_chain_length_nonempty,
                    stddev_chain_length=dist.stddev_chain_length,
                    chi_square_normalized=dist.chi_square_normalized,
                    weighted_avg_probes=weighted_average_probes(probes, freq),
                    avalanche_quality=aval.quality,
                    avalanche_mean_flip_probability=aval.mean_flip_probability,
                    avalanche_worst_bit_bias=aval.worst_bit_bias,
                )
            )

        return results
