"""Generic hash table with separate chaining, parameterized by hash function.

One implementation is reused for every hash function under test, so any
difference in results is caused by the hash function and not the table.

Collision terminology (used consistently across the whole project)
------------------------------------------------------------------
* **Full-hash collision**  - two *distinct* keys a != b with h(a) == h(b)
  (the complete 32-bit digest is equal). A property of the hash function alone.
* **Bucket collision**     - two distinct keys a != b with
  h(a) mod m == h(b) mod m, i.e. they are assigned to the same bucket of an
  m-bucket table. A property of the hash function *and* the table size, and
  the one that actually slows a symbol table down.
  - ``collisions`` counts insertions of a new key into an already non-empty
    bucket (a key that finds its bucket occupied).
  - ``colliding_pairs()`` counts every unordered pair of keys sharing a bucket
    (= sum over buckets of C(chain_length, 2)).

Every full-hash collision is also a bucket collision, never the reverse.
"""

import sys
from typing import Callable, Dict, Generic, List, Optional, Tuple, TypeVar

K = TypeVar("K")
V = TypeVar("V")


class HashTable(Generic[K, V]):
    """Separate-chaining hash table with built-in collision instrumentation."""

    def __init__(self, bucket_count: int, hash_fn: Callable[[K], int]) -> None:
        if bucket_count <= 0:
            raise ValueError("bucket_count must be positive")
        self.bucket_count = bucket_count
        self.hash_fn = hash_fn
        self._buckets: List[List[Tuple[K, Optional[V]]]] = [[] for _ in range(bucket_count)]
        self._full_hashes: Dict[int, int] = {}  # digest -> number of distinct keys seen
        self.size = 0
        self.collisions = 0            # bucket collisions (new key, occupied bucket)
        self.full_hash_collisions = 0  # new key whose complete digest already existed

    # ------------------------------------------------------------------ core
    def insert(self, key: K, value: Optional[V] = None) -> None:
        """Insert or update a key."""
        digest = self.hash_fn(key)
        bucket = self._buckets[digest % self.bucket_count]

        for i, (k, _) in enumerate(bucket):
            if k == key:
                bucket[i] = (key, value)
                return

        if bucket:
            self.collisions += 1
        if digest in self._full_hashes:
            self.full_hash_collisions += 1
            self._full_hashes[digest] += 1
        else:
            self._full_hashes[digest] = 1

        bucket.append((key, value))
        self.size += 1

    def lookup(self, key: K) -> Optional[V]:
        for k, v in self._buckets[self.hash_fn(key) % self.bucket_count]:
            if k == key:
                return v
        return None

    def contains(self, key: K) -> bool:
        for k, _ in self._buckets[self.hash_fn(key) % self.bucket_count]:
            if k == key:
                return True
        return False

    def probes(self, key: K) -> Optional[int]:
        """Number of key comparisons a successful search for ``key`` needs
        (1 = found first in its chain), or None if the key is absent."""
        for pos, (k, _) in enumerate(self._buckets[self.hash_fn(key) % self.bucket_count], 1):
            if k == key:
                return pos
        return None

    def chain_length_for(self, key: K) -> int:
        """Length of the chain a search for ``key`` has to walk when it misses."""
        return len(self._buckets[self.hash_fn(key) % self.bucket_count])

    # ------------------------------------------------------------ statistics
    def load_factor(self) -> float:
        return self.size / self.bucket_count

    def chain_lengths(self) -> List[int]:
        return [len(b) for b in self._buckets]

    def max_chain_length(self) -> int:
        return max(self.chain_lengths())

    def non_empty_buckets(self) -> int:
        return sum(1 for b in self._buckets if b)

    def bucket_distribution(self) -> List[int]:
        """Alias of chain_lengths(), named for reporting/plotting use."""
        return self.chain_lengths()

    def colliding_pairs(self) -> int:
        """Unordered pairs of keys that share a bucket: sum of C(len, 2)."""
        return sum(n * (n - 1) // 2 for n in self.chain_lengths())

    def estimated_memory_bytes(self) -> int:
        """Rough memory estimate (bytes) of the bucket structure.

        An *approximation*: ``sys.getsizeof`` ignores some nested overhead, and
        for equal-size tables holding the same keys the number is nearly
        identical across hash functions (only chain structure differs). Use it
        for order-of-magnitude comparison, not as a profiler result.
        """
        total = sys.getsizeof(self._buckets)
        for bucket in self._buckets:
            total += sys.getsizeof(bucket)
            for item in bucket:
                total += sys.getsizeof(item)
                for element in item:
                    total += sys.getsizeof(element)
        return total
