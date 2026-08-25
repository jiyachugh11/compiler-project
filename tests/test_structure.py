"""Initial structure and import verification tests for Backend 1."""

import pytest
from compiler import AnalysisResult, CompilerPipeline
from compiler.interning.string_pool import StringPool
from compiler.lexer.lexer import Lexer, LexerError
from compiler.lexer.tokens import SourceLocation, Token, TokenType
from compiler.profiler.workload import WorkloadMetrics, WorkloadProfiler
from compiler.symbol_table.scope import Scope, ScopeError, ScopeType
from compiler.symbol_table.symbol import Symbol, SymbolRole
from compiler.symbol_table.symbol_table import SymbolTable


def test_package_imports() -> None:
    """Verify all top-level and subpackage exports are cleanly importable."""
    assert CompilerPipeline is not None
    assert AnalysisResult is not None
    assert Lexer is not None
    assert LexerError is not None
    assert Token is not None
    assert TokenType is not None
    assert SourceLocation is not None
    assert Scope is not None
    assert ScopeError is not None
    assert ScopeType is not None
    assert Symbol is not None
    assert SymbolRole is not None
    assert SymbolTable is not None
    assert StringPool is not None
    assert WorkloadMetrics is not None
    assert WorkloadProfiler is not None


def test_token_instantiation() -> None:
    """Verify Token and SourceLocation data structures."""
    loc = SourceLocation(line=1, column=5)
    token = Token(type=TokenType.IDENTIFIER, value="my_var", location=loc)
    assert token.is_identifier() is True
    assert token.value == "my_var"
    assert token.location.line == 1
    assert token.location.column == 5
    assert str(loc) == "1:5"


def test_symbol_instantiation() -> None:
    """Verify Symbol and Scope dataclass instantiation and fields."""
    loc = SourceLocation(line=2, column=10)
    symbol = Symbol(
        name="counter",
        scope_id=0,
        scope_depth=0,
        location=loc,
        data_type="int",
        role=SymbolRole.DECLARATION,
        intern_id=1,
    )
    assert symbol.name == "counter"
    assert symbol.data_type == "int"
    assert symbol.scope_id == 0
    assert symbol.scope_depth == 0
    assert symbol.role == SymbolRole.DECLARATION
    assert symbol.intern_id == 1

    scope = Scope(scope_id=0, parent_id=None, depth=0, scope_type=ScopeType.GLOBAL)
    assert scope.scope_id == 0
    assert scope.parent_id is None
    assert scope.depth == 0
    assert scope.scope_type == ScopeType.GLOBAL


def test_workload_metrics_instantiation() -> None:
    """Verify WorkloadMetrics structure adheres to required metric fields."""
    metrics = WorkloadMetrics(
        total_identifiers=10,
        unique_identifiers=4,
        average_identifier_length=5.2,
        min_identifier_length=1,
        max_identifier_length=12,
        identifier_frequency={"count": 3, "i": 4, "total": 2, "max_val": 1},
        repetition_ratio=0.6,
        uniqueness_ratio=0.4,
        scope_count=2,
        max_scope_depth=1,
        identifiers_per_scope={0: 6, 1: 4},
    )
    assert metrics.total_identifiers == 10
    assert metrics.unique_identifiers == 4
    assert metrics.average_identifier_length == 5.2
    assert metrics.min_identifier_length == 1
    assert metrics.max_identifier_length == 12
    assert metrics.repetition_ratio == 0.6
    assert metrics.uniqueness_ratio == 0.4
    assert metrics.scope_count == 2
    assert metrics.max_scope_depth == 1


def test_pipeline_instantiation() -> None:
    """Verify CompilerPipeline initialization and component wiring."""
    pipeline = CompilerPipeline()
    assert isinstance(pipeline.lexer, Lexer)
    assert isinstance(pipeline.symbol_table, SymbolTable)
    assert isinstance(pipeline.string_pool, StringPool)
    assert isinstance(pipeline.profiler, WorkloadProfiler)


def test_unimplemented_stubs_raise_not_implemented() -> None:
    """Verify stub methods in downstream modules raise NotImplementedError until implementation."""
    symbol_table = SymbolTable()
    loc = SourceLocation(line=1, column=1)
    sym = Symbol(name="x", scope_id=0, scope_depth=0, location=loc)

    with pytest.raises(NotImplementedError):
        symbol_table.insert(sym)

    with pytest.raises(NotImplementedError):
        symbol_table.lookup("x")

    string_pool = StringPool()
    with pytest.raises(NotImplementedError):
        string_pool.intern("x")

    profiler = WorkloadProfiler()
    with pytest.raises(NotImplementedError):
        profiler.compute_metrics(["x"])

    pipeline = CompilerPipeline()
    with pytest.raises(NotImplementedError):
        pipeline.run("int x = 1;")
