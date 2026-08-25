"""Unit tests for the lexical scope management system."""

import pytest
from compiler.symbol_table import Scope, ScopeError, ScopeType, SymbolTable


@pytest.fixture
def symtab() -> SymbolTable:
    """Fixture providing a fresh SymbolTable instance with initialized global scope."""
    return SymbolTable()


def test_global_scope_creation(symtab: SymbolTable) -> None:
    """Verify that a global scope is automatically created upon initialization."""
    current = symtab.current_scope()
    assert current.scope_id == 0
    assert current.parent_id is None
    assert current.depth == 0
    assert current.scope_type == ScopeType.GLOBAL
    assert current.is_global is True
    assert symtab.current_scope_id == 0
    assert len(symtab.scopes) == 1


def test_enter_and_exit_child_scope(symtab: SymbolTable) -> None:
    """Test entering and exiting a single child scope."""
    child_scope = symtab.enter_scope(ScopeType.FUNCTION)

    # Verify child scope properties
    assert child_scope.scope_id == 1
    assert child_scope.parent_id == 0
    assert child_scope.depth == 1
    assert child_scope.scope_type == ScopeType.FUNCTION
    assert child_scope.is_global is False
    assert symtab.current_scope_id == 1
    assert symtab.current_scope() == child_scope

    # Verify parent links
    global_scope = symtab.get_scope(0)
    assert global_scope is not None
    assert 1 in global_scope.child_scope_ids

    # Exit back to global
    exited = symtab.exit_scope()
    assert exited == child_scope
    assert symtab.current_scope_id == 0
    assert symtab.current_scope().scope_type == ScopeType.GLOBAL


def test_nested_scopes(symtab: SymbolTable) -> None:
    """Test deeply nested scopes with correct parent links and depth increments."""
    # Global (depth 0, ID 0) -> Function (depth 1, ID 1) -> Loop (depth 2, ID 2) -> Inner Block (depth 3, ID 3)
    s1 = symtab.enter_scope(ScopeType.FUNCTION)
    assert s1.scope_id == 1
    assert s1.parent_id == 0
    assert s1.depth == 1

    s2 = symtab.enter_scope(ScopeType.BLOCK)
    assert s2.scope_id == 2
    assert s2.parent_id == 1
    assert s2.depth == 2

    s3 = symtab.enter_scope(ScopeType.BLOCK)
    assert s3.scope_id == 3
    assert s3.parent_id == 2
    assert s3.depth == 3

    assert symtab.current_scope_id == 3

    # Stepwise exit
    assert symtab.exit_scope().scope_id == 3
    assert symtab.current_scope_id == 2

    assert symtab.exit_scope().scope_id == 2
    assert symtab.current_scope_id == 1

    assert symtab.exit_scope().scope_id == 1
    assert symtab.current_scope_id == 0


def test_sibling_scopes(symtab: SymbolTable) -> None:
    """Test sibling scopes under the same parent scope."""
    # Enter and exit sibling A
    sibling_a = symtab.enter_scope(ScopeType.BLOCK)
    assert sibling_a.scope_id == 1
    assert sibling_a.parent_id == 0
    assert sibling_a.depth == 1
    symtab.exit_scope()

    # Enter and exit sibling B
    sibling_b = symtab.enter_scope(ScopeType.BLOCK)
    assert sibling_b.scope_id == 2
    assert sibling_b.parent_id == 0
    assert sibling_b.depth == 1
    symtab.exit_scope()

    # Verify both exist as children of global
    global_scope = symtab.get_scope(0)
    assert global_scope is not None
    assert global_scope.child_scope_ids == [1, 2]
    assert sibling_a.scope_id != sibling_b.scope_id
    assert sibling_a.parent_id == sibling_b.parent_id == 0


def test_scope_types(symtab: SymbolTable) -> None:
    """Test creating scopes of all supported ScopeType variants."""
    assert symtab.current_scope().scope_type == ScopeType.GLOBAL

    func_scope = symtab.enter_scope(ScopeType.FUNCTION)
    assert func_scope.scope_type == ScopeType.FUNCTION
    symtab.exit_scope()

    block_scope = symtab.enter_scope(ScopeType.BLOCK)
    assert block_scope.scope_type == ScopeType.BLOCK
    symtab.exit_scope()


def test_invalid_exit_from_global_scope_raises_scope_error(symtab: SymbolTable) -> None:
    """Test that attempting to exit the root global scope raises ScopeError."""
    with pytest.raises(ScopeError) as exc_info:
        symtab.exit_scope()
    assert "Cannot exit global scope" in str(exc_info.value)


def test_invalid_exit_after_popping_all_child_scopes(symtab: SymbolTable) -> None:
    """Test that after exiting all child scopes, a further exit raises ScopeError."""
    symtab.enter_scope(ScopeType.FUNCTION)
    symtab.enter_scope(ScopeType.BLOCK)
    symtab.exit_scope()
    symtab.exit_scope()

    assert symtab.current_scope_id == 0

    with pytest.raises(ScopeError):
        symtab.exit_scope()


def test_get_scope_by_id(symtab: SymbolTable) -> None:
    """Test retrieving scopes by ID even after exiting them."""
    s1 = symtab.enter_scope(ScopeType.FUNCTION)
    s2 = symtab.enter_scope(ScopeType.BLOCK)
    symtab.exit_scope()
    symtab.exit_scope()

    assert symtab.get_scope(0) == symtab.scopes[0]
    assert symtab.get_scope(1) == s1
    assert symtab.get_scope(2) == s2
    assert symtab.get_scope(999) is None
