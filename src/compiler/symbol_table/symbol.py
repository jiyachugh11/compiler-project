"""Symbol definitions and metadata."""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional
from compiler.lexer.tokens import SourceLocation


class SymbolError(Exception):
    """Exception raised for invalid symbol table operations."""

    pass


class SymbolRole(Enum):
    """Role of a symbol occurrence in source code."""

    DECLARATION = auto()
    REFERENCE = auto()
    UNKNOWN = auto()


@dataclass
class Symbol:
    """Represents a symbol table entry with source & scope metadata.

    Attributes:
        name: Raw identifier name.
        data_type: Inferred or declared type (if reliably determinable, extensible later).
        scope_id: ID of the scope where this symbol occurs/resides.
        scope_depth: Nesting depth of the scope (0 for global).
        location: Source location (line, column).
        role: Declaration vs Reference.
        intern_id: Unique integer assigned by string interner.
    """

    name: str
    scope_id: int
    scope_depth: int
    location: SourceLocation
    data_type: Optional[str] = None
    role: SymbolRole = SymbolRole.UNKNOWN
    intern_id: Optional[int] = None
