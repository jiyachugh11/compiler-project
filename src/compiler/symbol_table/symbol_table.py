"""Symbol table manager supporting lexical scope hierarchy and shadowing."""

from typing import Dict, List, Optional
from compiler.symbol_table.scope import Scope, ScopeError, ScopeType
from compiler.symbol_table.symbol import Symbol


class SymbolTable:
    """Manages multi-scope symbol tables with an active lexical scope stack.

    Scope Hierarchy Rules:
    - Global scope is automatically created at initialization (scope_id=0, depth=0).
    - Entering a scope creates a child with incremented depth and pushes it onto the stack.
    - Exiting a scope pops it from the stack, returning focus to the parent scope.
    - Attempting to exit the global scope raises ScopeError.
    - Parent-child tree relationships are preserved across nested and sibling scopes.
    """

    def __init__(self) -> None:
        self.scopes: Dict[int, Scope] = {}
        self.symbols: List[Symbol] = []
        self._scope_stack: List[int] = []
        self._next_scope_id: int = 0

        # Initialize root global scope (scope_id=0, depth=0)
        global_scope = Scope(
            scope_id=self._next_scope_id,
            parent_id=None,
            depth=0,
            scope_type=ScopeType.GLOBAL,
        )
        self.scopes[global_scope.scope_id] = global_scope
        self._scope_stack.append(global_scope.scope_id)
        self._next_scope_id += 1

    @property
    def current_scope_id(self) -> int:
        """Return the ID of the currently active lexical scope."""
        return self._scope_stack[-1]

    def current_scope(self) -> Scope:
        """Return the currently active Scope object."""
        return self.scopes[self.current_scope_id]

    def get_scope(self, scope_id: int) -> Optional[Scope]:
        """Retrieve a scope by its unique scope_id."""
        return self.scopes.get(scope_id)

    def enter_scope(self, scope_type: ScopeType = ScopeType.BLOCK) -> Scope:
        """Create and enter a new lexical child scope.

        Args:
            scope_type: Classification of the new scope (e.g. FUNCTION, BLOCK).

        Returns:
            The newly created and activated child Scope.
        """
        parent = self.current_scope()
        new_scope = Scope(
            scope_id=self._next_scope_id,
            parent_id=parent.scope_id,
            depth=parent.depth + 1,
            scope_type=scope_type,
        )
        self.scopes[new_scope.scope_id] = new_scope
        parent.child_scope_ids.append(new_scope.scope_id)
        self._scope_stack.append(new_scope.scope_id)
        self._next_scope_id += 1
        return new_scope

    def exit_scope(self) -> Scope:
        """Exit the current lexical scope back to its enclosing parent scope.

        Returns:
            The Scope that was exited.

        Raises:
            ScopeError: If attempting to exit the global scope.
        """
        if len(self._scope_stack) <= 1:
            raise ScopeError("Cannot exit global scope: already at root scope level.")

        exited_scope_id = self._scope_stack.pop()
        return self.scopes[exited_scope_id]

    def insert(self, symbol: Symbol) -> None:
        """Insert a symbol into the current active scope."""
        raise NotImplementedError("Symbol insertion will be implemented in the next phase.")

    def lookup(self, name: str) -> Optional[Symbol]:
        """Look up a symbol by name following lexical scope chain (shadowing)."""
        raise NotImplementedError("Symbol lookup will be implemented in the next phase.")
