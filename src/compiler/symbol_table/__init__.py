"""Symbol table and lexical scoping components."""

from compiler.symbol_table.scope import Scope, ScopeType
from compiler.symbol_table.symbol import Symbol, SymbolRole
from compiler.symbol_table.symbol_table import SymbolTable

__all__ = ["Scope", "ScopeType", "Symbol", "SymbolRole", "SymbolTable"]
