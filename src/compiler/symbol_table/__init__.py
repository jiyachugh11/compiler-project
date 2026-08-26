"""Symbol table and lexical scoping components."""

from compiler.symbol_table.scope import Scope, ScopeError, ScopeType
from compiler.symbol_table.symbol import Symbol, SymbolError, SymbolRole
from compiler.symbol_table.symbol_table import SymbolTable

__all__ = [
    "Scope",
    "ScopeError",
    "ScopeType",
    "Symbol",
    "SymbolError",
    "SymbolRole",
    "SymbolTable",
]
