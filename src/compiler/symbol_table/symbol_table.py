"""Symbol table manager supporting lexical scope hierarchy and shadowing."""

from typing import Dict, List, Optional
from compiler.lexer.tokens import SourceLocation
from compiler.symbol_table.scope import Scope, ScopeError, ScopeType
from compiler.symbol_table.symbol import Symbol, SymbolError, SymbolRole


class SymbolTable:
    """Manages multi-scope symbol tables with an active lexical scope stack.

    Scope Hierarchy Rules:
    - Global scope is automatically created at initialization (scope_id=0, depth=0).
    - Entering a scope creates a child with incremented depth and pushes it onto the stack.
    - Exiting a scope pops it from the stack, returning focus to the parent scope.
    - Attempting to exit the global scope raises ScopeError.
    - Parent-child tree relationships are preserved across nested and sibling scopes.
    - Symbols declared in exited scopes remain preserved for downstream analysis.
    """

    def __init__(self) -> None:
        self.scopes: Dict[int, Scope] = {}
        self.symbols: List[Symbol] = []
        self._scope_stack: List[int] = []
        self._next_scope_id: int = 0
        self._scope_symbols: Dict[int, Dict[str, Symbol]] = {}

        # Initialize root global scope (scope_id=0, depth=0)
        global_scope = Scope(
            scope_id=self._next_scope_id,
            parent_id=None,
            depth=0,
            scope_type=ScopeType.GLOBAL,
        )
        self.scopes[global_scope.scope_id] = global_scope
        self._scope_symbols[global_scope.scope_id] = {}
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
        self._scope_symbols[new_scope.scope_id] = {}
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

    def insert(self, symbol: Symbol) -> Symbol:
        """Insert a symbol into the current active scope.

        Args:
            symbol: Symbol object containing metadata (name, role, location, etc.).

        Returns:
            The inserted Symbol object.

        Raises:
            SymbolError: If a declaration duplicates an existing symbol name
                         in the current active scope.
        """
        current = self.current_scope()
        symbol.scope_id = current.scope_id
        symbol.scope_depth = current.depth

        if symbol.role == SymbolRole.DECLARATION:
            if symbol.name in self._scope_symbols[current.scope_id]:
                raise SymbolError(
                    f"Duplicate declaration of symbol '{symbol.name}' in scope {current.scope_id}."
                )
            self._scope_symbols[current.scope_id][symbol.name] = symbol
            if symbol.name not in current.symbol_names:
                current.symbol_names.append(symbol.name)
        elif symbol.role == SymbolRole.REFERENCE:
            # References are tracked in the symbol list without creating declarations
            pass
        else:
            # Default / UNKNOWN role: register as scope symbol if not already present
            if symbol.name not in self._scope_symbols[current.scope_id]:
                self._scope_symbols[current.scope_id][symbol.name] = symbol
                if symbol.name not in current.symbol_names:
                    current.symbol_names.append(symbol.name)

        self.symbols.append(symbol)
        return symbol

    def insert_declaration(
        self,
        name: str,
        location: SourceLocation,
        data_type: Optional[str] = None,
    ) -> Symbol:
        """Create and insert a declaration symbol into the current active scope.

        Args:
            name: Identifier name.
            location: Source code location (line, column).
            data_type: Optional declared or inferred type.

        Returns:
            The created and inserted Symbol.
        """
        current = self.current_scope()
        symbol = Symbol(
            name=name,
            scope_id=current.scope_id,
            scope_depth=current.depth,
            location=location,
            data_type=data_type,
            role=SymbolRole.DECLARATION,
        )
        return self.insert(symbol)

    def insert_reference(
        self,
        name: str,
        location: SourceLocation,
    ) -> Symbol:
        """Create and insert a reference symbol into the current active scope.

        Args:
            name: Identifier name.
            location: Source code location (line, column).

        Returns:
            The created and inserted Symbol.
        """
        current = self.current_scope()
        symbol = Symbol(
            name=name,
            scope_id=current.scope_id,
            scope_depth=current.depth,
            location=location,
            role=SymbolRole.REFERENCE,
        )
        return self.insert(symbol)

    def lookup(self, name: str, current_scope_only: bool = False) -> Optional[Symbol]:
        """Look up a symbol by name following the lexical scope chain (shadowing).

        Traverses from the currently active scope upward to enclosing parent scopes
        until a matching declaration is found or the root global scope is exhausted.

        Args:
            name: The identifier name to look up.
            current_scope_only: If True, search only the current active scope.

        Returns:
            The matching Symbol if found, or None if not found.
        """
        curr_scope_id: Optional[int] = self.current_scope_id
        while curr_scope_id is not None:
            scope_symbols = self._scope_symbols.get(curr_scope_id, {})
            if name in scope_symbols:
                return scope_symbols[name]
            if current_scope_only:
                break
            scope = self.scopes.get(curr_scope_id)
            if scope is None:
                break
            curr_scope_id = scope.parent_id
        return None

    def lookup_current_scope(self, name: str) -> Optional[Symbol]:
        """Look up a symbol by name in the current active scope only.

        Args:
            name: The identifier name to look up.

        Returns:
            The matching Symbol if declared in current scope, else None.
        """
        return self.lookup(name, current_scope_only=True)

    def lookup_in_scope(self, name: str, scope_id: int) -> Optional[Symbol]:
        """Look up a symbol declared in a specific scope by its scope_id.

        Args:
            name: Identifier name.
            scope_id: Unique scope ID.

        Returns:
            The matching Symbol if declared in that scope, else None.
        """
        return self._scope_symbols.get(scope_id, {}).get(name)

    def get_symbols(self, scope_id: Optional[int] = None) -> List[Symbol]:
        """Retrieve symbols, optionally filtered by scope_id.

        Args:
            scope_id: If specified, return symbols belonging to that scope.
                      If None, return all recorded symbols across all scopes.

        Returns:
            List of Symbol entries.
        """
        if scope_id is None:
            return list(self.symbols)
        return [s for s in self.symbols if s.scope_id == scope_id]
