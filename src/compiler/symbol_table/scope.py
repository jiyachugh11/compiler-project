"""Scope representation and hierarchy definitions."""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional


class ScopeType(Enum):
    """Types of lexical scopes."""

    GLOBAL = auto()
    FUNCTION = auto()
    BLOCK = auto()


@dataclass
class Scope:
    """Represents a lexical scope in the program hierarchy.

    Supports nesting, parent lookup, and local symbol mapping.
    """

    scope_id: int
    parent_id: Optional[int] = None
    depth: int = 0
    scope_type: ScopeType = ScopeType.GLOBAL
    symbol_names: List[str] = field(default_factory=list)
    child_scope_ids: List[int] = field(default_factory=list)
