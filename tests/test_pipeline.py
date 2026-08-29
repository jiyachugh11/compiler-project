"""Comprehensive integration tests for the CompilerPipeline module."""

import pytest
from compiler import AnalysisResult, CompilerPipeline
from compiler.symbol_table.scope import ScopeType
from compiler.symbol_table.symbol import SymbolRole


@pytest.fixture
def pipeline() -> CompilerPipeline:
    """Fixture providing a fresh CompilerPipeline instance."""
    return CompilerPipeline()


def test_empty_source_code(pipeline: CompilerPipeline) -> None:
    """Test pipeline execution on empty source code and whitespace."""
    result = pipeline.run("")

    assert isinstance(result, AnalysisResult)
    assert result.source_code == ""
    assert result.identifier_stream == []
    assert result.interned_identifiers == {}
    assert len(result.symbol_table.symbols) == 0
    assert len(result.scopes) == 1  # Global scope
    assert result.workload_metrics.total_identifiers == 0
    assert result.workload_metrics.unique_identifiers == 0


def test_simple_variable_declaration(pipeline: CompilerPipeline) -> None:
    """Test pipeline on a single variable declaration: int count = 0;."""
    source = "int count = 0;"
    result = pipeline.run(source)

    assert result.source_code == source
    assert result.identifier_stream == ["count"]
    assert result.interned_identifiers == {"count": 0}

    # Symbol table verification
    assert len(result.symbol_table.symbols) == 1
    sym = result.symbol_table.symbols[0]
    assert sym.name == "count"
    assert sym.data_type == "int"
    assert sym.role == SymbolRole.DECLARATION
    assert sym.scope_id == 0
    assert sym.scope_depth == 0
    assert sym.intern_id == 0
    assert sym.location.line == 1
    assert sym.location.column == 5

    # Metrics
    assert result.workload_metrics.total_identifiers == 1
    assert result.workload_metrics.unique_identifiers == 1
    assert result.workload_metrics.uniqueness_ratio == 1.0


def test_multiple_identifiers(pipeline: CompilerPipeline) -> None:
    """Test pipeline on multiple variable declarations and expressions."""
    source = "int a = 1; float b = 2.0; int c = a + 10;"
    result = pipeline.run(source)

    assert result.identifier_stream == ["a", "b", "c", "a"]
    assert result.interned_identifiers == {"a": 0, "b": 1, "c": 2}

    symbols = result.symbol_table.symbols
    assert len(symbols) == 4

    # Declarations
    assert symbols[0].name == "a" and symbols[0].role == SymbolRole.DECLARATION and symbols[0].data_type == "int"
    assert symbols[1].name == "b" and symbols[1].role == SymbolRole.DECLARATION and symbols[1].data_type == "float"
    assert symbols[2].name == "c" and symbols[2].role == SymbolRole.DECLARATION and symbols[2].data_type == "int"

    # Reference to 'a'
    assert symbols[3].name == "a" and symbols[3].role == SymbolRole.REFERENCE and symbols[3].intern_id == 0


def test_repeated_identifiers_and_intern_consistency(pipeline: CompilerPipeline) -> None:
    """Test repeated identifier occurrences receive identical intern_id values."""
    source = "count = count + x; x = count;"
    result = pipeline.run(source)

    assert result.identifier_stream == ["count", "count", "x", "x", "count"]
    assert result.interned_identifiers == {"count": 0, "x": 1}

    for sym in result.symbol_table.symbols:
        if sym.name == "count":
            assert sym.intern_id == 0
        elif sym.name == "x":
            assert sym.intern_id == 1

    assert result.workload_metrics.total_identifiers == 5
    assert result.workload_metrics.unique_identifiers == 2
    assert result.workload_metrics.repetition_ratio == pytest.approx(1.0 - (2 / 5.0))


def test_nested_scopes(pipeline: CompilerPipeline) -> None:
    """Test nested scopes hierarchy with curly braces and proper depth tracking."""
    source = """
    int global_var = 1;
    void my_func() {
        int local_var = 2;
        if (local_var > 0) {
            int inner_var = 3;
        }
    }
    """
    result = pipeline.run(source)

    # 3 scopes created: Global (0), Function (1), Block (2)
    assert len(result.scopes) == 3
    assert result.scopes[0].depth == 0
    assert result.scopes[0].scope_type == ScopeType.GLOBAL

    assert result.scopes[1].depth == 1
    assert result.scopes[1].scope_type == ScopeType.FUNCTION

    assert result.scopes[2].depth == 2
    assert result.scopes[2].scope_type == ScopeType.BLOCK

    assert result.workload_metrics.scope_count == 3
    assert result.workload_metrics.max_scope_depth == 2


def test_source_locations_preserved(pipeline: CompilerPipeline) -> None:
    """Test that accurate 1-indexed source line and column numbers are preserved on symbols."""
    source = (
        "int first = 1;\n"
        "float second = 2.0;\n"
    )
    result = pipeline.run(source)

    sym1 = result.symbol_table.symbols[0]
    assert sym1.name == "first"
    assert sym1.location.line == 1
    assert sym1.location.column == 5

    sym2 = result.symbol_table.symbols[1]
    assert sym2.name == "second"
    assert sym2.location.line == 2
    assert sym2.location.column == 7


def test_workload_metrics_pipeline_integration(pipeline: CompilerPipeline) -> None:
    """Test that pipeline produces complete WorkloadMetrics matching source workload."""
    source = "int x = 1; int y = x + x;"
    result = pipeline.run(source)

    metrics = result.workload_metrics
    assert metrics.total_identifiers == 4  # x, y, x, x
    assert metrics.unique_identifiers == 2  # x, y
    assert metrics.identifier_frequency == {"x": 3, "y": 1}
    assert metrics.min_identifier_length == 1
    assert metrics.max_identifier_length == 1
    assert metrics.average_identifier_length == 1.0


def test_source_code_preservation(pipeline: CompilerPipeline) -> None:
    """Test that original source code string is preserved verbatim in AnalysisResult."""
    source = "int a = 42;\n/* comment */\nint b = a;"
    result = pipeline.run(source)
    assert result.source_code == source


def test_realistic_c_function(pipeline: CompilerPipeline) -> None:
    """Test complete pipeline on a realistic C function with pointers, loops, and nested scopes."""
    source = """
    int compute_sum(int* arr, int length) {
        int total = 0;
        for (int i = 0; i < length; ++i) {
            total += arr[i];
        }
        return total;
    }
    """
    result = pipeline.run(source)

    # Identifiers in order
    expected_stream = [
        "compute_sum", "arr", "length",
        "total",
        "i", "i", "length", "i",
        "total", "arr", "i",
        "total"
    ]
    assert result.identifier_stream == expected_stream

    # Interning
    expected_unique = ["compute_sum", "arr", "length", "total", "i"]
    assert list(result.interned_identifiers.keys()) == expected_unique
    for idx, name in enumerate(expected_unique):
        assert result.interned_identifiers[name] == idx

    # Scopes
    assert len(result.scopes) == 3  # Global (0), compute_sum (1), for loop body (2)

    # Workload Metrics
    metrics = result.workload_metrics
    assert metrics.total_identifiers == 12
    assert metrics.unique_identifiers == 5
    assert metrics.identifier_frequency == {
        "compute_sum": 1,
        "arr": 2,
        "length": 2,
        "total": 3,
        "i": 4,
    }
    assert metrics.scope_count == 3
    assert metrics.max_scope_depth == 2
