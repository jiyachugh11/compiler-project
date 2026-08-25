"""Token definitions, token types, and source location tracking."""

from dataclasses import dataclass
from enum import Enum, auto


class TokenType(Enum):
    """Enumeration of recognized lexical token categories."""

    # Identifiers & Keywords
    IDENTIFIER = auto()
    KEYWORD = auto()

    # Literals
    LITERAL_INT = auto()
    LITERAL_FLOAT = auto()
    LITERAL_STRING = auto()
    LITERAL_CHAR = auto()

    # Operators
    OPERATOR = auto()

    # Delimiters & Punctuation
    DELIMITER = auto()
    LBRACE = auto()     # '{'
    RBRACE = auto()     # '}'
    LPAREN = auto()     # '('
    RPAREN = auto()     # ')'
    LBRACKET = auto()   # '['
    RBRACKET = auto()   # ']'
    SEMICOLON = auto()  # ';'
    COMMA = auto()      # ','
    DOT = auto()        # '.'
    ARROW = auto()      # '->'
    COLON = auto()      # ':'
    QUESTION = auto()   # '?'

    # Comments (if preserved or categorized)
    COMMENT = auto()

    # Stream control
    EOF = auto()
    UNKNOWN = auto()


@dataclass(frozen=True)
class SourceLocation:
    """Source position for tokens and symbols (1-indexed)."""

    line: int
    column: int

    def __str__(self) -> str:
        return f"{self.line}:{self.column}"

    def __repr__(self) -> str:
        return f"SourceLocation(line={self.line}, column={self.column})"


@dataclass(frozen=True)
class Token:
    """Representation of a lexical token."""

    type: TokenType
    value: str
    location: SourceLocation

    def is_identifier(self) -> bool:
        """Check if the token is an identifier."""
        return self.type == TokenType.IDENTIFIER

    def is_keyword(self) -> bool:
        """Check if the token is a keyword."""
        return self.type == TokenType.KEYWORD

    def is_literal(self) -> bool:
        """Check if the token is a literal value."""
        return self.type in (
            TokenType.LITERAL_INT,
            TokenType.LITERAL_FLOAT,
            TokenType.LITERAL_STRING,
            TokenType.LITERAL_CHAR,
        )

    def is_brace(self) -> bool:
        """Check if the token is an opening or closing scope brace."""
        return self.type in (TokenType.LBRACE, TokenType.RBRACE)

    def __repr__(self) -> str:
        return f"Token(type={self.type.name}, value={self.value!r}, loc={self.location})"
