"""Structural interface contract between Backend 1 and Backend 2.

Backend 2 never imports Backend 1's concrete classes (AnalysisResult,
WorkloadMetrics, SymbolTable, Scope, ...). Instead it depends only on these
Protocols, which describe the minimum shape it needs. Any object with these
attributes -- Backend 1's real AnalysisResult, a test double, a future
refactor of Backend 1 -- satisfies the contract automatically (structural
typing), so Backend 2 keeps working even if Backend 1's internals change.

Fields Backend 2 actually uses:
    - identifier_stream
    - interned_identifiers
    - workload_metrics (and its sub-fields below)

Everything else Backend 1 produces (symbol_table, scopes, source_code) is
intentionally NOT part of this contract because Backend 2 has no use for it.
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
