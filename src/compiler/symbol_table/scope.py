"""Scope representation, hierarchy definitions, and scope error handling."""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional


class ScopeError(Exception):
    """Exception raised for invalid scope operations."""

    pass


class ScopeType(Enum):
    """Types of lexical scopes."""

    GLOBAL = auto()
    FUNCTION = auto()
    BLOCK = auto()


@dataclass
class Scope:
    """Represents a lexical scope in the program hierarchy.

    Attributes:
        scope_id: Unique integer identifier for this scope.
        parent_id: ID of the enclosing parent scope (None for global scope).
        depth: Nesting level (0 for global scope, 1 for functions/top blocks, etc.).
        scope_type: Scope classification (GLOBAL, FUNCTION, BLOCK).
        symbol_names: List of symbol identifier names declared in this scope.
        child_scope_ids: List of IDs for direct child scopes.
    """

    scope_id: int
    parent_id: Optional[int] = None
    depth: int = 0
    scope_type: ScopeType = ScopeType.GLOBAL
    symbol_names: List[str] = field(default_factory=list)
    child_scope_ids: List[int] = field(default_factory=list)

    @property
    def is_global(self) -> bool:
        """Check if this scope is the global root scope."""
        return self.scope_type == ScopeType.GLOBAL or self.parent_id is None
