"""Tests for the hash-table-backed scoped symbol table and its replay benchmark."""

from types import SimpleNamespace

import pytest

from hashing.adapters import SymbolEvent, extract_symbol_events
from hashing.functions import HASH_FUNCTIONS, djb2
from hashing.symbol_table_hashed import HashedSymbolTable, replay


def test_declare_and_resolve_in_same_scope():
    st = HashedSymbolTable(djb2)
    assert st.declare("x", {"type": "int"})
    info, hops, cmps = st.resolve("x")
    assert info == {"type": "int"} and hops == 1 and cmps >= 1


def test_redeclaration_in_same_scope_is_rejected():
    st = HashedSymbolTable(djb2)
    assert st.declare("x") is True
    assert st.declare("x") is False


def test_shadowing_and_outward_resolution():
    st = HashedSymbolTable(djb2)
    st.declare("g", "global_g")
    st.declare("x", "outer_x")
    st.enter_scope()
    st.declare("x", "inner_x")                 # shadows
    assert st.resolve("x")[0] == "inner_x"
    info, hops, _ = st.resolve("g")            # found one scope up
    assert info == "global_g" and hops == 2
    st.exit_scope()
    assert st.resolve("x")[0] == "outer_x"


def test_unresolved_name_walks_whole_chain():
    st = HashedSymbolTable(djb2)
    st.enter_scope()
    st.enter_scope()
    info, hops, _ = st.resolve("nope")
    assert info is None and hops == 3


def test_cannot_exit_global_scope():
    with pytest.raises(ValueError):
        HashedSymbolTable(djb2).exit_scope()


def test_sibling_scopes_are_isolated():
    st = HashedSymbolTable(djb2)
    a = st.enter_scope(); st.declare("tmp"); st.exit_scope()
    st.enter_scope()
    assert st.resolve("tmp")[0] is None
    assert a != st.current_scope_id


EVENTS = [
    SymbolEvent("add", 0, True),
    SymbolEvent("a", 1, True), SymbolEvent("b", 1, True),
    SymbolEvent("a", 1, False), SymbolEvent("b", 1, False),
    SymbolEvent("add", 0, False),          # resolved from global
    SymbolEvent("printf", 1, False),       # never declared -> unresolved
    SymbolEvent("a", 1, True),             # redeclaration
]
PARENTS = {0: None, 1: 0}


@pytest.mark.parametrize("name,fn", list(HASH_FUNCTIONS.items()))
def test_replay_is_hash_function_independent_in_outcome(name, fn):
    r = replay(fn, EVENTS, PARENTS, repeats=1)
    assert (r.declarations, r.redeclarations, r.resolutions, r.unresolved) == (3, 1, 4, 1)
    assert r.scopes == 2 and r.total_time_sec >= 0
    assert r.avg_scope_hops >= 1.0 and r.avg_comparisons >= 0


def test_replay_ignores_events_for_unknown_scopes():
    r = replay(djb2, [SymbolEvent("z", 99, True)], {0: None}, repeats=1)
    assert r.declarations == 0


def _fake_analysis(symbols, scopes):
    return SimpleNamespace(
        symbol_table=SimpleNamespace(symbols=symbols), scopes=scopes)


def test_adapter_reads_backend1_shape():
    role = lambda n: SimpleNamespace(name=n)   # noqa: E731
    syms = [SimpleNamespace(name="x", scope_id=1, role=role("DECLARATION")),
            SimpleNamespace(name="x", scope_id=1, role=role("REFERENCE"))]
    scopes = {0: SimpleNamespace(parent_id=None), 1: SimpleNamespace(parent_id=0)}
    events, parents = extract_symbol_events(_fake_analysis(syms, scopes))
    assert [e.is_declaration for e in events] == [True, False]
    assert parents == {0: None, 1: 0}


def test_adapter_returns_none_when_data_missing_or_malformed():
    assert extract_symbol_events(SimpleNamespace()) is None
    assert extract_symbol_events(_fake_analysis(None, {0: SimpleNamespace(parent_id=None)})) is None
    assert extract_symbol_events(_fake_analysis([object()], {0: SimpleNamespace(parent_id=None)})) is None
