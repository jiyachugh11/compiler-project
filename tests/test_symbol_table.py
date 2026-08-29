"""Comprehensive unit tests for the SymbolTable and lexical scope integration."""

import pytest
from compiler.lexer.tokens import SourceLocation
from compiler.symbol_table.scope import ScopeType
from compiler.symbol_table.symbol import Symbol, SymbolError, SymbolRole
from compiler.symbol_table.symbol_table import SymbolTable


@pytest.fixture
def symtab() -> SymbolTable:
    """Fixture providing a fresh SymbolTable instance with initialized global scope."""
    return SymbolTable()


def test_insert_declaration(symtab: SymbolTable) -> None:
    """Test inserting a declaration symbol with full metadata into the global scope."""
    loc = SourceLocation(line=1, column=5)
    symbol = Symbol(
        name="x",
        scope_id=0,
        scope_depth=0,
        location=loc,
        data_type="int",
        role=SymbolRole.DECLARATION,
    )
    result = symtab.insert(symbol)

    assert result == symbol
    assert symbol.name == "x"
    assert symbol.scope_id == 0
    assert symbol.scope_depth == 0
    assert symbol.location == loc
    assert symbol.data_type == "int"
    assert symbol.role == SymbolRole.DECLARATION
    assert symbol.intern_id is None
    assert "x" in symtab.current_scope().symbol_names
    assert len(symtab.symbols) == 1
    assert symtab.symbols[0] == symbol


def test_insert_declaration_helper(symtab: SymbolTable) -> None:
    """Test insert_declaration helper method creates and registers symbol properly."""
    loc = SourceLocation(line=3, column=10)
    sym = symtab.insert_declaration(name="count", location=loc, data_type="int")

    assert sym.name == "count"
    assert sym.scope_id == 0
    assert sym.scope_depth == 0
    assert sym.location == loc
    assert sym.data_type == "int"
    assert sym.role == SymbolRole.DECLARATION
    assert symtab.lookup("count") == sym


def test_insert_reference(symtab: SymbolTable) -> None:
    """Test inserting a reference symbol tracks occurrence without overriding declarations."""
    decl_loc = SourceLocation(line=1, column=1)
    ref_loc1 = SourceLocation(line=2, column=5)
    ref_loc2 = SourceLocation(line=3, column=8)

    decl = symtab.insert_declaration(name="total", location=decl_loc, data_type="float")
    ref1 = symtab.insert_reference(name="total", location=ref_loc1)
    ref2 = symtab.insert_reference(name="total", location=ref_loc2)

    assert ref1.role == SymbolRole.REFERENCE
    assert ref1.name == "total"
    assert ref1.scope_id == 0
    assert ref1.location == ref_loc1

    assert ref2.role == SymbolRole.REFERENCE
    assert ref2.name == "total"
    assert ref2.scope_id == 0
    assert ref2.location == ref_loc2

    # Lookup should still resolve to the declaration
    assert symtab.lookup("total") == decl

    # All occurrences are recorded in chronological order
    assert symtab.symbols == [decl, ref1, ref2]


def test_lookup_in_current_scope(symtab: SymbolTable) -> None:
    """Test symbol lookup restricted to current scope."""
    loc = SourceLocation(line=1, column=1)
    decl = symtab.insert_declaration(name="global_var", location=loc, data_type="int")

    assert symtab.lookup_current_scope("global_var") == decl
    assert symtab.lookup("global_var", current_scope_only=True) == decl

    # Enter a child scope without declaring global_var
    symtab.enter_scope(ScopeType.FUNCTION)
    assert symtab.lookup_current_scope("global_var") is None
    assert symtab.lookup("global_var", current_scope_only=True) is None

    # But lexical lookup still finds it
    assert symtab.lookup("global_var") == decl


def test_lookup_through_parent_scope(symtab: SymbolTable) -> None:
    """Test lexical lookup traversing upward through multiple parent scopes."""
    loc_g = SourceLocation(line=1, column=1)
    loc_f = SourceLocation(line=2, column=1)

    sym_g = symtab.insert_declaration("g", loc_g, data_type="int")

    symtab.enter_scope(ScopeType.FUNCTION)
    sym_f = symtab.insert_declaration("f", loc_f, data_type="void")

    symtab.enter_scope(ScopeType.BLOCK)

    # From inner block, both f (parent) and g (grandparent) must resolve
    assert symtab.lookup("g") == sym_g
    assert symtab.lookup("f") == sym_f


def test_missing_symbol_lookup(symtab: SymbolTable) -> None:
    """Test that looking up an undeclared symbol returns None."""
    assert symtab.lookup("non_existent") is None
    assert symtab.lookup_current_scope("non_existent") is None

    symtab.enter_scope(ScopeType.FUNCTION)
    assert symtab.lookup("non_existent") is None

    symtab.enter_scope(ScopeType.BLOCK)
    assert symtab.lookup("non_existent") is None


def test_variable_shadowing(symtab: SymbolTable) -> None:
    """Test variable shadowing: inner declaration shadows outer, unshadows on exit."""
    loc_global = SourceLocation(line=1, column=5)
    loc_func = SourceLocation(line=5, column=9)

    # Global: int x;
    global_x = symtab.insert_declaration("x", loc_global, data_type="int")
    assert symtab.lookup("x") == global_x
    assert symtab.lookup("x").scope_depth == 0
    assert symtab.lookup("x").scope_id == 0

    # Function: int x;
    symtab.enter_scope(ScopeType.FUNCTION)
    func_x = symtab.insert_declaration("x", loc_func, data_type="int")

    # Inside function, lookup("x") must return the function-level x
    assert symtab.lookup("x") == func_x
    assert symtab.lookup("x").scope_depth == 1
    assert symtab.lookup("x").scope_id == 1
    assert symtab.lookup("x") != global_x

    # After leaving function, lookup("x") must return the global x
    symtab.exit_scope()
    assert symtab.lookup("x") == global_x
    assert symtab.lookup("x").scope_depth == 0
    assert symtab.lookup("x").scope_id == 0


def test_multi_level_nested_shadowing(symtab: SymbolTable) -> None:
    """Test multi-level nested scopes shadowing across Global -> Func -> Block1 -> Block2."""
    loc = SourceLocation(line=1, column=1)

    sym_g = symtab.insert_declaration("val", loc, data_type="int")  # Depth 0
    assert symtab.lookup("val") == sym_g

    symtab.enter_scope(ScopeType.FUNCTION)
    sym_f = symtab.insert_declaration("val", loc, data_type="int")  # Depth 1
    assert symtab.lookup("val") == sym_f

    symtab.enter_scope(ScopeType.BLOCK)  # Depth 2 (no declaration, inherits Depth 1)
    assert symtab.lookup("val") == sym_f

    symtab.enter_scope(ScopeType.BLOCK)
    sym_b = symtab.insert_declaration("val", loc, data_type="int")  # Depth 3
    assert symtab.lookup("val") == sym_b

    # Unwind step-by-step
    symtab.exit_scope()
    assert symtab.lookup("val") == sym_f

    symtab.exit_scope()
    assert symtab.lookup("val") == sym_f

    symtab.exit_scope()
    assert symtab.lookup("val") == sym_g


def test_sibling_scopes_isolation(symtab: SymbolTable) -> None:
    """Test that declarations in sibling scopes do not leak into each other."""
    loc = SourceLocation(line=1, column=1)

    # Sibling A
    symtab.enter_scope(ScopeType.BLOCK)
    sym_a = symtab.insert_declaration("sibling_a_var", loc)
    assert symtab.lookup("sibling_a_var") == sym_a
    symtab.exit_scope()

    # Sibling B
    symtab.enter_scope(ScopeType.BLOCK)
    assert symtab.lookup("sibling_a_var") is None
    sym_b = symtab.insert_declaration("sibling_b_var", loc)
    assert symtab.lookup("sibling_b_var") == sym_b
    symtab.exit_scope()

    # Global
    assert symtab.lookup("sibling_a_var") is None
    assert symtab.lookup("sibling_b_var") is None


def test_symbols_remain_accessible_after_exiting_scope(symtab: SymbolTable) -> None:
    """Ensure symbols from exited scopes remain stored in symbol table for later analysis."""
    loc = SourceLocation(line=2, column=4)

    symtab.enter_scope(ScopeType.FUNCTION)
    func_scope_id = symtab.current_scope_id
    func_sym = symtab.insert_declaration("local_var", loc, data_type="int")
    func_ref = symtab.insert_reference("local_var", SourceLocation(line=3, column=5))
    symtab.exit_scope()

    # Current scope is global; lookup will not find local_var via lexical chain
    assert symtab.current_scope_id == 0
    assert symtab.lookup("local_var") is None

    # But symbols list still retains all symbols and references
    assert len(symtab.symbols) == 2
    assert func_sym in symtab.symbols
    assert func_ref in symtab.symbols

    # Specific scope query methods allow post-exit analysis
    assert symtab.lookup_in_scope("local_var", func_scope_id) == func_sym
    assert symtab.get_symbols(func_scope_id) == [func_sym, func_ref]
    assert len(symtab.get_symbols()) == 2


def test_duplicate_declaration_in_same_scope_raises_symbol_error(symtab: SymbolTable) -> None:
    """Test that declaring the same symbol twice in the same scope raises SymbolError."""
    loc1 = SourceLocation(line=1, column=5)
    loc2 = SourceLocation(line=2, column=5)

    symtab.insert_declaration("x", loc1, data_type="int")

    with pytest.raises(SymbolError) as exc_info:
        symtab.insert_declaration("x", loc2, data_type="int")

    assert "Duplicate declaration of symbol 'x' in scope 0" in str(exc_info.value)


def test_multiple_references_allowed_in_same_scope(symtab: SymbolTable) -> None:
    """Test that multiple references to the same identifier in the same scope are valid."""
    loc_decl = SourceLocation(line=1, column=1)
    symtab.insert_declaration("x", loc_decl, data_type="int")

    ref1 = symtab.insert_reference("x", SourceLocation(line=2, column=1))
    ref2 = symtab.insert_reference("x", SourceLocation(line=3, column=1))
    ref3 = symtab.insert_reference("x", SourceLocation(line=4, column=1))

    assert len(symtab.symbols) == 4
    assert symtab.get_symbols() == [symtab.symbols[0], ref1, ref2, ref3]


def test_symbol_metadata_preservation(symtab: SymbolTable) -> None:
    """Test that all symbol metadata fields are accurately preserved upon insertion."""
    symtab.enter_scope(ScopeType.FUNCTION)
    loc = SourceLocation(line=10, column=25)
    sym = Symbol(
        name="buffer_size",
        scope_id=0,  # Will be adjusted to current scope_id=1
        scope_depth=0,  # Will be adjusted to current depth=1
        location=loc,
        data_type="size_t",
        role=SymbolRole.DECLARATION,
        intern_id=42,
    )
    inserted = symtab.insert(sym)

    assert inserted.name == "buffer_size"
    assert inserted.scope_id == 1
    assert inserted.scope_depth == 1
    assert inserted.location == loc
    assert inserted.data_type == "size_t"
    assert inserted.role == SymbolRole.DECLARATION
    assert inserted.intern_id == 42
