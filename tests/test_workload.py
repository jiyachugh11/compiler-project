"""Unit tests for the WorkloadProfiler module."""

import pytest
from compiler.lexer.tokens import SourceLocation
from compiler.profiler.workload import WorkloadMetrics, WorkloadProfiler
from compiler.symbol_table.scope import ScopeType
from compiler.symbol_table.symbol_table import SymbolTable


@pytest.fixture
def profiler() -> WorkloadProfiler:
    """Fixture providing a fresh WorkloadProfiler instance."""
    return WorkloadProfiler()


def test_empty_identifier_stream(profiler: WorkloadProfiler) -> None:
    """Test profiler with an empty identifier stream (no division by zero)."""
    metrics = profiler.compute_metrics([])

    assert isinstance(metrics, WorkloadMetrics)
    assert metrics.total_identifiers == 0
    assert metrics.unique_identifiers == 0
    assert metrics.average_identifier_length == 0.0
    assert metrics.min_identifier_length == 0
    assert metrics.max_identifier_length == 0
    assert metrics.identifier_frequency == {}
    assert metrics.repetition_ratio == 0.0
    assert metrics.uniqueness_ratio == 0.0
    assert metrics.scope_count == 0
    assert metrics.max_scope_depth == 0
    assert metrics.identifiers_per_scope == {}


def test_single_identifier_stream(profiler: WorkloadProfiler) -> None:
    """Test profiler with a single identifier."""
    metrics = profiler.compute_metrics(["count"])

    assert metrics.total_identifiers == 1
    assert metrics.unique_identifiers == 1
    assert metrics.min_identifier_length == 5
    assert metrics.max_identifier_length == 5
    assert metrics.average_identifier_length == 5.0
    assert metrics.identifier_frequency == {"count": 1}
    assert metrics.uniqueness_ratio == 1.0
    assert metrics.repetition_ratio == 0.0


def test_multiple_unique_identifiers(profiler: WorkloadProfiler) -> None:
    """Test stream where all identifiers are unique."""
    stream = ["a", "bb", "ccc", "dddd"]
    metrics = profiler.compute_metrics(stream)

    assert metrics.total_identifiers == 4
    assert metrics.unique_identifiers == 4
    assert metrics.min_identifier_length == 1
    assert metrics.max_identifier_length == 4
    assert metrics.average_identifier_length == (1 + 2 + 3 + 4) / 4.0
    assert metrics.identifier_frequency == {"a": 1, "bb": 1, "ccc": 1, "dddd": 1}
    assert metrics.uniqueness_ratio == 1.0
    assert metrics.repetition_ratio == 0.0


def test_repeated_identifiers_and_example_workload(profiler: WorkloadProfiler) -> None:
    """Test the example stream: ["count", "main", "x", "count", "x", "x"]."""
    stream = ["count", "main", "x", "count", "x", "x"]
    metrics = profiler.compute_metrics(stream)

    assert metrics.total_identifiers == 6
    assert metrics.unique_identifiers == 3
    assert metrics.identifier_frequency == {"count": 2, "main": 1, "x": 3}
    assert metrics.uniqueness_ratio == pytest.approx(3 / 6.0)
    assert metrics.repetition_ratio == pytest.approx(1.0 - (3 / 6.0))


def test_min_max_average_length_calculations(profiler: WorkloadProfiler) -> None:
    """Test accuracy of identifier length statistics across multiple different words."""
    stream = ["i", "total_sum", "i", "len", "total_sum"]
    # lengths: 1, 9, 1, 3, 9 -> total len = 23, count = 5
    metrics = profiler.compute_metrics(stream)

    assert metrics.min_identifier_length == 1
    assert metrics.max_identifier_length == 9
    assert metrics.average_identifier_length == pytest.approx(23 / 5.0)


def test_frequency_distribution_preserves_names_and_counts(profiler: WorkloadProfiler) -> None:
    """Test that all identifier names and their exact occurrence counts are preserved."""
    stream = ["alpha", "beta", "alpha", "gamma", "beta", "alpha", "delta"]
    metrics = profiler.compute_metrics(stream)

    expected_freq = {"alpha": 3, "beta": 2, "gamma": 1, "delta": 1}
    assert metrics.identifier_frequency == expected_freq


def test_uniqueness_and_repetition_ratios(profiler: WorkloadProfiler) -> None:
    """Test uniqueness and repetition ratio formulas:
    uniquenessRatio = uniqueCount / totalOccurrences
    repetitionRatio = 1 - uniquenessRatio
    """
    stream = ["x", "x", "x", "x", "y"]  # 5 total, 2 unique
    metrics = profiler.compute_metrics(stream)

    assert metrics.uniqueness_ratio == pytest.approx(2 / 5.0)  # 0.4
    assert metrics.repetition_ratio == pytest.approx(3 / 5.0)  # 0.6
    assert metrics.uniqueness_ratio + metrics.repetition_ratio == pytest.approx(1.0)


def test_scope_metrics_with_empty_symbol_table(profiler: WorkloadProfiler) -> None:
    """Test computing metrics with an empty SymbolTable (only global scope)."""
    symtab = SymbolTable()
    metrics = profiler.compute_metrics(["var1", "var2"], symbol_table=symtab)

    assert metrics.scope_count == 1
    assert metrics.max_scope_depth == 0
    assert metrics.identifiers_per_scope == {0: 0}


def test_scope_distribution_with_populated_symbol_table(profiler: WorkloadProfiler) -> None:
    """Test computing per-scope distribution across nested scopes."""
    symtab = SymbolTable()
    loc = SourceLocation(line=1, column=1)

    # Global scope (ID 0, depth 0): 2 symbols
    symtab.insert_declaration("g1", loc)
    symtab.insert_declaration("g2", loc)

    # Function scope (ID 1, depth 1): 3 symbols
    symtab.enter_scope(ScopeType.FUNCTION)
    symtab.insert_declaration("f1", loc)
    symtab.insert_reference("g1", loc)
    symtab.insert_reference("f1", loc)

    # Block scope (ID 2, depth 2): 1 symbol
    symtab.enter_scope(ScopeType.BLOCK)
    symtab.insert_declaration("b1", loc)

    # Exit back to global
    symtab.exit_scope()
    symtab.exit_scope()

    identifier_stream = ["g1", "g2", "f1", "g1", "f1", "b1"]
    metrics = profiler.compute_metrics(identifier_stream, symbol_table=symtab)

    assert metrics.total_identifiers == 6
    assert metrics.unique_identifiers == 4
    assert metrics.scope_count == 3
    assert metrics.max_scope_depth == 2
    assert metrics.identifiers_per_scope == {0: 2, 1: 3, 2: 1}


def test_profiler_without_symbol_table(profiler: WorkloadProfiler) -> None:
    """Test that omitting symbol_table produces safe default scope metrics."""
    metrics = profiler.compute_metrics(["foo", "bar"])

    assert metrics.scope_count == 0
    assert metrics.max_scope_depth == 0
    assert metrics.identifiers_per_scope == {}
