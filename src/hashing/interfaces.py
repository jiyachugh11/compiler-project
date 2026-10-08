"""Structural interface contract between Backend 1 and Backend 2.

Backend 2 never imports Backend 1's concrete classes. It depends only on these
Protocols, which describe the minimum shape it needs, so any object with these
attributes (Backend 1's real AnalysisResult, a test double, a future refactor)
satisfies the contract automatically.

REQUIRED (core benchmark):
    identifier_stream, interned_identifiers, workload_metrics (+ fields below)

OPTIONAL (hash-table-backed symbol-table replay; skipped when absent). Read
only through hashing/adapters.py:
    symbol_table.symbols  ordered items with .name, .scope_id, .role.name
    scopes                {scope_id: obj with .parent_id}
"""

from typing import Dict, List, Protocol, runtime_checkable


@runtime_checkable
class WorkloadMetricsLike(Protocol):
    total_identifiers: int
    unique_identifiers: int
    average_identifier_length: float
    min_identifier_length: int
    max_identifier_length: int
    identifier_frequency: Dict[str, int]
    repetition_ratio: float
    uniqueness_ratio: float
    scope_count: int
    max_scope_depth: int
    identifiers_per_scope: Dict[int, int]


@runtime_checkable
class AnalysisResultLike(Protocol):
    identifier_stream: List[str]
    interned_identifiers: Dict[str, int]
    workload_metrics: WorkloadMetricsLike
