"""Generic hash table with separate chaining, parameterized by hash function.

One implementation is reused across all hash functions under test -- only the
hash function passed to the constructor changes -- so any difference in
benchmark results reflects the hash function, not the table implementation.
"""

from typing import Callable, Generic, List, Optional, TypeVar

K = TypeVar("K")
V = TypeVar("V")


class HashTable(Generic[K, V]):
    """Hash table using separate chaining for collision resolution.

    Attributes:
        bucket_count: Number of buckets (fixed at construction time).
        size: Number of key-value pairs currently stored.
        collisions: Number of insertions that landed in an already
            non-empty bucket (i.e. shared a bucket index with an existing,
            different key).
    """

    def __init__(self, bucket_count: int, hash_fn: Callable[[K], int]) -> None:
        if bucket_count <= 0:
            raise ValueError("bucket_count must be positive")
        self.bucket_count = bucket_count
        self.hash_fn = hash_fn
        self._buckets: List[List[tuple]] = [[] for _ in range(bucket_count)]
        self.size = 0
        self.collisions = 0

    def _index(self, key: K) -> int:
        return self.hash_fn(key) % self.bucket_count

    def insert(self, key: K, value: Optional[V] = None) -> None:
        """Insert or update a key. Counts a collision if the bucket was
        already occupied by a *different* key at insertion time."""
        idx = self._index(key)
        bucket = self._buckets[idx]

        for i, (k, _) in enumerate(bucket):
            if k == key:
                bucket[i] = (key, value)
                return

        if len(bucket) > 0:
            self.collisions += 1

        bucket.append((key, value))
        self.size += 1

    def lookup(self, key: K) -> Optional[V]:
        """Return the value for key, or None if absent."""
        idx = self._index(key)
        for k, v in self._buckets[idx]:
            if k == key:
                return v
        return None

    def contains(self, key: K) -> bool:
        idx = self._index(key)
        return any(k == key for k, _ in self._buckets[idx])

    def load_factor(self) -> float:
        return self.size / self.bucket_count

    def chain_lengths(self) -> List[int]:
        """Length of every bucket's chain, in bucket order."""
        return [len(bucket) for bucket in self._buckets]

    def max_chain_length(self) -> int:
        lengths = self.chain_lengths()
        return max(lengths) if lengths else 0

    def non_empty_buckets(self) -> int:
        return sum(1 for bucket in self._buckets if bucket)

    def bucket_distribution(self) -> List[int]:
        """Alias of chain_lengths(), named for reporting/plotting use."""
        return self.chain_lengths()

    def estimated_memory_bytes(self) -> int:
        """Rough memory estimate in bytes.

        This is an approximation, not an exact measurement: Python's object
        model has per-object overhead (list headers, tuple headers, small-int
        caching, string interning) that `sys.getsizeof` does not fully
        capture for nested containers. Good enough for *relative* comparison
        between hash functions/tables built the same way; not a substitute
        for a memory profiler.
        """
        import sys

        total = sys.getsizeof(self._buckets)
        for bucket in self._buckets:
            total += sys.getsizeof(bucket)
            for item in bucket:
                total += sys.getsizeof(item)
                for element in item:
                    total += sys.getsizeof(element)
        return total
