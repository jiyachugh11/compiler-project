"""Benchmarking suite: runs every registered hash function through the
generic HashTable against a real identifier workload and records
performance + collision statistics.

Benchmark design:
    - Insertion is benchmarked over the *unique* identifiers (mirrors how a
      real symbol table only stores each identifier once).
    - Lookup is benchmarked over the *full* identifier_stream, including
      repeats, because a real compiler re-resolves the same identifier every
      time it's referenced -- that repetition is the actual access pattern
      workload_metrics.repetition_ratio is describing.
    - All hash functions run against tables of the same bucket_count, built
      the same way, so differences in the results reflect the hash function
      only.
"""

import time
from typing import Callable, Dict, List, Optional

from hashing.functions import HASH_FUNCTIONS
from hashing.hash_table import HashTable
from hashing.models import HashFunctionResult


def _default_bucket_count(unique_count: int, target_load_factor: float = 0.75) -> int:
    """Pick a bucket count so the table lands near target_load_factor once
    all unique identifiers are inserted. Always at least 1 bucket."""
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
    ) -> None:
        """
        Args:
            hash_functions: Mapping of name -> hash function. Defaults to
                the built-in registry (DJB2, FNV-1a, SDBM, Jenkins, CRC32).
            bucket_count: Fixed bucket count to use for every table. If
                None, it's computed per-run from the unique identifier count
                and target_load_factor.
            target_load_factor: Used only when bucket_count is None.
        """
        self.hash_functions = hash_functions or HASH_FUNCTIONS
        self.bucket_count = bucket_count
        self.target_load_factor = target_load_factor

    def run(self, identifier_stream: List[str]) -> List[HashFunctionResult]:
        """Benchmark every registered hash function against identifier_stream.

        Args:
            identifier_stream: Full ordered identifier occurrence stream
                from Backend 1's AnalysisResult.

        Returns:
            One HashFunctionResult per hash function.
        """
        unique_identifiers = list(dict.fromkeys(identifier_stream))  # de-dup, order-preserved
        bucket_count = self.bucket_count or _default_bucket_count(
            len(unique_identifiers), self.target_load_factor
        )

        results: List[HashFunctionResult] = []
        for name, fn in self.hash_functions.items():
            table: HashTable = HashTable(bucket_count=bucket_count, hash_fn=fn)

            start = time.perf_counter()
            for ident in unique_identifiers:
                table.insert(ident, True)
            insert_time = time.perf_counter() - start

            start = time.perf_counter()
            for ident in identifier_stream:
                table.contains(ident)
            lookup_time = time.perf_counter() - start

            results.append(
                HashFunctionResult(
                    name=name,
                    bucket_count=bucket_count,
                    items_inserted=table.size,
                    insert_time_sec=insert_time,
                    lookup_time_sec=lookup_time,
                    lookups_performed=len(identifier_stream),
                    collisions=table.collisions,
                    max_chain_length=table.max_chain_length(),
                    non_empty_buckets=table.non_empty_buckets(),
                    load_factor=table.load_factor(),
                    estimated_memory_bytes=table.estimated_memory_bytes(),
                    bucket_distribution=table.bucket_distribution(),
                )
            )

        return results
