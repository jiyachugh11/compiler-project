"""Symbol table manager supporting lexical scope hierarchy and shadowing."""

from typing import Dict, List, Optional
from compiler.symbol_table.scope import Scope, ScopeType
from compiler.symbol_table.symbol import Symbol


class SymbolTable:
    """Manages multi-scope symbol tables with lexical scope stack.

    Supports:
    - Global scope (depth 0)
    - Function and block scopes (nested depths)
    - Lexical lookup with shadowing resolution
    """

    def __init__(self) -> None:
        self.scopes: Dict[int, Scope] = {}
        self.symbols: List[Symbol] = []
        self.current_scope_id: int = 0
        self._next_scope_id: int = 0

    def enter_scope(self, scope_type: ScopeType = ScopeType.BLOCK) -> Scope:
        """Enter a new lexical scope."""
        raise NotImplementedError("Scope management will be implemented in the next phase.")

    def exit_scope(self) -> None:
        """Exit the current lexical scope back to its parent."""
        raise NotImplementedError("Scope management will be implemented in the next phase.")

    def insert(self, symbol: Symbol) -> None:
        """Insert a symbol into the current active scope."""
        raise NotImplementedError("Symbol insertion will be implemented in the next phase.")

    def lookup(self, name: str) -> Optional[Symbol]:
        """Look up a symbol by name following lexical scope chain (shadowing)."""
        raise NotImplementedError("Symbol lookup will be implemented in the next phase.")
