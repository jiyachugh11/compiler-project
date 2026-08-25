"""Workload profiling and statistical metrics computation."""

from dataclasses import dataclass
from typing import Dict, List, Optional
from compiler.symbol_table.symbol_table import SymbolTable


@dataclass
class WorkloadMetrics:
    """Workload characteristics extracted from source code.

    Directly feeds into Backend 2's benchmark suite.
    """

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


class WorkloadProfiler:
    """Computes statistical workload profiles from identifier streams and symbol tables."""

    def __init__(self) -> None:
        pass

    def compute_metrics(
        self,
        identifier_stream: List[str],
        symbol_table: Optional[SymbolTable] = None,
    ) -> WorkloadMetrics:
        """Compute workload metrics for the given identifier stream and symbol table."""
        raise NotImplementedError("Workload profiling will be implemented in the next phase.")
