"""Output data contracts produced by Backend 2.

HashAnalysisReport is the final artifact handed to the frontend team,
analogous to Backend 1's AnalysisResult. It's a plain dataclass so it can be
serialized with `dataclasses.asdict()` straight to JSON.
"""

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class HashFunctionResult:
    """Benchmark + collision statistics for a single hash function."""

    name: str
    bucket_count: int
    items_inserted: int
    insert_time_sec: float
    lookup_time_sec: float
    lookups_performed: int
    collisions: int
    max_chain_length: int
    non_empty_buckets: int
    load_factor: float
    estimated_memory_bytes: int
    bucket_distribution: List[int] = field(default_factory=list)


@dataclass
class HashAnalysisReport:
    """Complete output contract from Backend 2 to the frontend."""

    per_function: List[HashFunctionResult]
    recommended_function: str
    recommendation_reason: str
    workload_summary: Dict
