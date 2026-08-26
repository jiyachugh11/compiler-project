"""Workload profiling and statistical metrics computation."""

from collections import Counter
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
        """Compute workload metrics for the given identifier stream and symbol table.

        Args:
            identifier_stream: Ordered list of identifier string occurrences.
            symbol_table: Optional SymbolTable instance providing lexical scope context.

        Returns:
            A populated WorkloadMetrics object.
        """
        total = len(identifier_stream)
        frequency: Dict[str, int] = dict(Counter(identifier_stream))
        unique_count = len(frequency)

        if total > 0:
            lengths = [len(ident) for ident in identifier_stream]
            min_len = min(lengths)
            max_len = max(lengths)
            avg_len = sum(lengths) / total
            uniqueness_ratio = unique_count / total
            repetition_ratio = 1.0 - uniqueness_ratio
        else:
            min_len = 0
            max_len = 0
            avg_len = 0.0
            uniqueness_ratio = 0.0
            repetition_ratio = 0.0

        if symbol_table is not None and symbol_table.scopes:
            scope_count = len(symbol_table.scopes)
            max_scope_depth = max((s.depth for s in symbol_table.scopes.values()), default=0)
            identifiers_per_scope: Dict[int, int] = {
                scope_id: 0 for scope_id in symbol_table.scopes
            }
            for symbol in symbol_table.symbols:
                if symbol.scope_id in identifiers_per_scope:
                    identifiers_per_scope[symbol.scope_id] += 1
                else:
                    identifiers_per_scope[symbol.scope_id] = 1
        else:
            scope_count = 0
            max_scope_depth = 0
            identifiers_per_scope = {}

        return WorkloadMetrics(
            total_identifiers=total,
            unique_identifiers=unique_count,
            average_identifier_length=avg_len,
            min_identifier_length=min_len,
            max_identifier_length=max_len,
            identifier_frequency=frequency,
            repetition_ratio=repetition_ratio,
            uniqueness_ratio=uniqueness_ratio,
            scope_count=scope_count,
            max_scope_depth=max_scope_depth,
            identifiers_per_scope=identifiers_per_scope,
        )
