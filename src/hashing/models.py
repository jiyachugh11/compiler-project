"""Output data contracts produced by Backend 2.

HashAnalysisReport is the artefact handed to the frontend, analogous to
Backend 1's AnalysisResult. Everything is a plain dataclass, so
``dataclasses.asdict(report)`` gives JSON-ready data.

Backward compatibility: the first block of HashFunctionResult fields is the
original contract; everything after it was added after the 0th review and has
a default, so existing consumers keep working.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from hashing.security import SecurityResult
from hashing.symbol_table_hashed import SymbolTableBenchResult


@dataclass
class HashFunctionResult:
    """Benchmark + quality statistics for a single hash function."""

    # ---- original contract -------------------------------------------------
    name: str
    bucket_count: int
    items_inserted: int
    insert_time_sec: float
    lookup_time_sec: float
    lookups_performed: int
    collisions: int                    # bucket collisions (see DEFINITIONS)
    max_chain_length: int
    non_empty_buckets: int
    load_factor: float
    estimated_memory_bytes: int
    bucket_distribution: List[int] = field(default_factory=list)

    # ---- added after the 0th review ---------------------------------------
    family: str = ""
    hash_only_ns_per_key: float = 0.0           # cost of the hash function alone
    full_hash_collisions: int = 0               # identical 32-bit digests
    colliding_pairs: int = 0
    collision_ratio_vs_ideal: float = 0.0
    empty_bucket_ratio: float = 0.0
    expected_empty_bucket_ratio: float = 0.0
    avg_chain_length_nonempty: float = 0.0
    stddev_chain_length: float = 0.0
    chi_square_normalized: float = 0.0
    weighted_avg_probes: float = 0.0
    avalanche_quality: float = 0.0
    avalanche_mean_flip_probability: float = 0.0
    avalanche_worst_bit_bias: float = 0.0
    security: Optional[SecurityResult] = None
    symbol_table: Optional[SymbolTableBenchResult] = None


@dataclass
class RankedFunction:
    name: str
    rank: int
    score: float                       # lower is better
    eligible: bool                     # baselines are ranked but never recommended
    breakdown: Dict[str, float] = field(default_factory=dict)  # weighted contribution per criterion


@dataclass
class HashAnalysisReport:
    """Complete output contract from Backend 2 to the frontend."""

    per_function: List[HashFunctionResult]
    recommended_function: str
    recommendation_reason: str
    workload_summary: Dict
    ranking: List[RankedFunction] = field(default_factory=list)
    weights: Dict[str, float] = field(default_factory=dict)
    security_reference: Optional[SecurityResult] = None   # SHA-256 truncated, for comparison
    definitions: Dict[str, str] = field(default_factory=dict)
    confidence: str = ""   # "low" | "medium" | "high": can this workload tell the functions apart?
