"""Unified Backend 1 Compiler & Static Analysis Pipeline."""

from dataclasses import dataclass
from typing import Dict, List
from compiler.interning.string_pool import StringPool
from compiler.lexer.lexer import Lexer
from compiler.profiler.workload import WorkloadMetrics, WorkloadProfiler
from compiler.symbol_table.scope import Scope
from compiler.symbol_table.symbol_table import SymbolTable


@dataclass
class AnalysisResult:
    """Complete output contract from Backend 1 to Backend 2.

    Preserves full workload fidelity for consistent hashing and benchmarking:
    - ordered identifier occurrence stream
    - unique / interned identifiers (string -> id mapping)
    - symbol table
    - scope information
    - workload statistics
    """

    identifier_stream: List[str]
    interned_identifiers: Dict[str, int]
    symbol_table: SymbolTable
    scopes: Dict[int, Scope]
    workload_metrics: WorkloadMetrics
    source_code: str


class CompilerPipeline:
    """Orchestrates Backend 1 stages:

    Source Code
    -> Lexer
    -> Identifier Extraction
    -> Scope Analysis
    -> Symbol Table
    -> String Interning
    -> Workload Profiling
    -> AnalysisResult
    """

    def __init__(self) -> None:
        self.lexer = Lexer()
        self.symbol_table = SymbolTable()
        self.string_pool = StringPool()
        self.profiler = WorkloadProfiler()

    def run(self, source_code: str) -> AnalysisResult:
        """Run the full compilation and static analysis pipeline on source code."""
        raise NotImplementedError("Pipeline orchestration will be implemented in the next phase.")
