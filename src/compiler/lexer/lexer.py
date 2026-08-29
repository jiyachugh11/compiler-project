"""Lexical analyzer for tokenizing source code into a stream of tokens."""

from typing import List, Optional, Set
from compiler.lexer.tokens import SourceLocation, Token, TokenType


class LexerError(Exception):
    """Exception raised for lexical analysis errors."""

    def __init__(self, message: str, location: SourceLocation) -> None:
        super().__init__(f"Lexer error at {location}: {message}")
        self.message = message
        self.location = location


# Standard C/C++ keywords
DEFAULT_KEYWORDS: Set[str] = {
    "auto", "break", "case", "char", "const", "continue", "default", "do",
    "double", "else", "enum", "extern", "float", "for", "goto", "if",
    "inline", "int", "long", "register", "restrict", "return", "short",
    "signed", "sizeof", "static", "struct", "switch", "typedef", "union",
    "unsigned", "void", "volatile", "while", "_Bool", "_Complex", "_Imaginary",
    "bool", "true", "false", "nullptr", "NULL"
}

# Multi-character operators and delimiters (ordered by length descending for greedy match)
MULTI_CHAR_OPS = [
    (">>=", TokenType.OPERATOR),
    ("<<=", TokenType.OPERATOR),
    ("...", TokenType.DELIMITER),
    ("->", TokenType.ARROW),
    ("++", TokenType.OPERATOR),
    ("--", TokenType.OPERATOR),
    ("<<", TokenType.OPERATOR),
    (">>", TokenType.OPERATOR),
    ("<=", TokenType.OPERATOR),
    (">=", TokenType.OPERATOR),
    ("==", TokenType.OPERATOR),
    ("!=", TokenType.OPERATOR),
    ("&&", TokenType.OPERATOR),
    ("||", TokenType.OPERATOR),
    ("+=", TokenType.OPERATOR),
    ("-=", TokenType.OPERATOR),
    ("*=", TokenType.OPERATOR),
    ("/=", TokenType.OPERATOR),
    ("%=", TokenType.OPERATOR),
    ("&=", TokenType.OPERATOR),
    ("|=", TokenType.OPERATOR),
    ("^=", TokenType.OPERATOR),
]

# Single-character tokens
SINGLE_CHAR_TOKENS = {
    "{": TokenType.LBRACE,
    "}": TokenType.RBRACE,
    "(": TokenType.LPAREN,
    ")": TokenType.RPAREN,
    "[": TokenType.LBRACKET,
    "]": TokenType.RBRACKET,
    ";": TokenType.SEMICOLON,
    ",": TokenType.COMMA,
    ".": TokenType.DOT,
    ":": TokenType.COLON,
    "?": TokenType.QUESTION,
    "+": TokenType.OPERATOR,
    "-": TokenType.OPERATOR,
    "*": TokenType.OPERATOR,
    "/": TokenType.OPERATOR,
    "%": TokenType.OPERATOR,
    "=": TokenType.OPERATOR,
    "<": TokenType.OPERATOR,
    ">": TokenType.OPERATOR,
    "!": TokenType.OPERATOR,
    "&": TokenType.OPERATOR,
    "|": TokenType.OPERATOR,
    "^": TokenType.OPERATOR,
    "~": TokenType.OPERATOR,
}


class Lexer:
    """Scans and tokenizes source code into a sequential stream of tokens.

    Features:
    - Distinguishes identifiers from keywords.
    - Handles integer, floating-point, string, and character literals.
    - Scans operators, braces, brackets, parentheses, and delimiters.
    - Skips whitespace and single/multi-line comments without polluting identifier stream.
    - Tracks 1-indexed line and column numbers.
    """

    def __init__(self, keywords: Optional[Set[str]] = None) -> None:
        self.keywords = keywords if keywords is not None else set(DEFAULT_KEYWORDS)
        self._source = ""
        self._pos = 0
        self._length = 0
        self._line = 1
        self._column = 1

    def tokenize(self, source_code: str, include_eof: bool = False) -> List[Token]:
        """Tokenize source code into an ordered list of tokens.

        Args:
            source_code: Raw source code string.
            include_eof: If True, appends an EOF token at the end of the list.

        Returns:
            List of scanned Token objects preserving source order.
        """
        self._source = source_code
        self._pos = 0
        self._length = len(source_code)
        self._line = 1
        self._column = 1

        tokens: List[Token] = []

        while not self._is_at_end():
            self._skip_whitespace_and_comments()
            if self._is_at_end():
                break

            start_line = self._line
            start_col = self._column
            start_loc = SourceLocation(line=start_line, column=start_col)
            ch = self._peek()

            # 1. Identifiers & Keywords
            if ch.isalpha() or ch == "_":
                token = self._scan_identifier_or_keyword(start_loc)
                tokens.append(token)
                continue

            # 2. Number literals (e.g. 123, 0x1F, 3.14, .5)
            if ch.isdigit() or (ch == "." and self._peek_next().isdigit()):
                token = self._scan_number(start_loc)
                tokens.append(token)
                continue

            # 3. String literals ("...")
            if ch == '"':
                token = self._scan_string(start_loc)
                tokens.append(token)
                continue

            # 4. Character literals ('...')
            if ch == "'":
                token = self._scan_char(start_loc)
                tokens.append(token)
                continue

            # 5. Multi-character operators and delimiters
            matched_multi = False
            for op_str, op_type in MULTI_CHAR_OPS:
                if self._match_prefix(op_str):
                    self._advance_n(len(op_str))
                    tokens.append(Token(type=op_type, value=op_str, location=start_loc))
                    matched_multi = True
                    break
            if matched_multi:
                continue

            # 6. Single-character operators and delimiters
            if ch in SINGLE_CHAR_TOKENS:
                token_type = SINGLE_CHAR_TOKENS[ch]
                self._advance()
                tokens.append(Token(type=token_type, value=ch, location=start_loc))
                continue

            # 7. Unrecognized character
            self._advance()
            tokens.append(Token(type=TokenType.UNKNOWN, value=ch, location=start_loc))

        if include_eof:
            eof_loc = SourceLocation(line=self._line, column=self._column)
            tokens.append(Token(type=TokenType.EOF, value="", location=eof_loc))

        return tokens

    # -------------------------------------------------------------------------
    # Helper Scanners
    # -------------------------------------------------------------------------

    def _scan_identifier_or_keyword(self, start_loc: SourceLocation) -> Token:
        """Scan an identifier or keyword."""
        start_pos = self._pos
        while not self._is_at_end() and (self._peek().isalnum() or self._peek() == "_"):
            self._advance()

        val = self._source[start_pos:self._pos]
        if val in self.keywords:
            return Token(type=TokenType.KEYWORD, value=val, location=start_loc)
        return Token(type=TokenType.IDENTIFIER, value=val, location=start_loc)

    def _scan_number(self, start_loc: SourceLocation) -> Token:
        """Scan integer or floating point literal."""
        start_pos = self._pos
        is_float = False

        # Hexadecimal (0x...) or Binary (0b...) or Octal (0o...)
        if self._peek() == "0" and self._pos + 1 < self._length:
            next_ch = self._source[self._pos + 1].lower()
            if next_ch == "x":
                self._advance_n(2)
                while not self._is_at_end() and (self._peek().isdigit() or self._peek().lower() in "abcdef"):
                    self._advance()
                self._consume_int_suffixes()
                val = self._source[start_pos:self._pos]
                return Token(type=TokenType.LITERAL_INT, value=val, location=start_loc)
            elif next_ch == "b":
                self._advance_n(2)
                while not self._is_at_end() and self._peek() in "01":
                    self._advance()
                self._consume_int_suffixes()
                val = self._source[start_pos:self._pos]
                return Token(type=TokenType.LITERAL_INT, value=val, location=start_loc)

        # Decimal integer or float
        while not self._is_at_end() and self._peek().isdigit():
            self._advance()

        # Fractional part
        if not self._is_at_end() and self._peek() == ".":
            # Check it's not a member access or ellipsis like "1..something"
            if self._pos + 1 < self._length and self._source[self._pos + 1] == ".":
                pass
            else:
                is_float = True
                self._advance()  # consume '.'
                while not self._is_at_end() and self._peek().isdigit():
                    self._advance()

        # Exponent part (e.g. 1e10, 3.14e-2)
        if not self._is_at_end() and self._peek().lower() == "e":
            is_float = True
            self._advance()
            if not self._is_at_end() and self._peek() in ("+", "-"):
                self._advance()
            while not self._is_at_end() and self._peek().isdigit():
                self._advance()

        # Type suffixes (f, F, l, L, u, U, etc.)
        if is_float:
            self._consume_float_suffixes()
            token_type = TokenType.LITERAL_FLOAT
        else:
            self._consume_int_suffixes()
            token_type = TokenType.LITERAL_INT

        val = self._source[start_pos:self._pos]
        return Token(type=token_type, value=val, location=start_loc)

    def _consume_int_suffixes(self) -> None:
        """Consume integer suffixes like u, l, ll, ul, etc."""
        while not self._is_at_end() and self._peek().lower() in ("u", "l", "z"):
            self._advance()

    def _consume_float_suffixes(self) -> None:
        """Consume float suffixes like f, F, l, L."""
        while not self._is_at_end() and self._peek().lower() in ("f", "l"):
            self._advance()

    def _scan_string(self, start_loc: SourceLocation) -> Token:
        """Scan string literal with escape sequence support."""
        start_pos = self._pos
        self._advance()  # consume opening '"'

        while not self._is_at_end() and self._peek() != '"':
            if self._peek() == "\\":
                self._advance()  # consume backslash
                if not self._is_at_end():
                    self._advance()  # consume escaped char
            elif self._peek() == "\n":
                # Line break in string
                self._advance()
            else:
                self._advance()

        if self._is_at_end():
            raise LexerError("Unterminated string literal", start_loc)

        self._advance()  # consume closing '"'
        val = self._source[start_pos:self._pos]
        return Token(type=TokenType.LITERAL_STRING, value=val, location=start_loc)

    def _scan_char(self, start_loc: SourceLocation) -> Token:
        """Scan character literal with escape sequence support."""
        start_pos = self._pos
        self._advance()  # consume opening "'"

        while not self._is_at_end() and self._peek() != "'":
            if self._peek() == "\\":
                self._advance()  # consume backslash
                if not self._is_at_end():
                    self._advance()  # consume escaped char
            elif self._peek() == "\n":
                self._advance()
            else:
                self._advance()

        if self._is_at_end():
            raise LexerError("Unterminated character literal", start_loc)

        self._advance()  # consume closing "'"
        val = self._source[start_pos:self._pos]
        return Token(type=TokenType.LITERAL_CHAR, value=val, location=start_loc)

    # -------------------------------------------------------------------------
    # Whitespace & Comment Handling
    # -------------------------------------------------------------------------

    def _skip_whitespace_and_comments(self) -> None:
        """Skip whitespace and single/multi-line comments."""
        while not self._is_at_end():
            ch = self._peek()

            # Whitespace
            if ch in (" ", "\t", "\r", "\v", "\f"):
                self._advance()
                continue
            elif ch == "\n":
                self._advance()
                continue

            # Comments
            if ch == "/" and self._pos + 1 < self._length:
                next_ch = self._source[self._pos + 1]
                # Single-line comment //
                if next_ch == "/":
                    self._advance_n(2)
                    while not self._is_at_end() and self._peek() != "\n":
                        self._advance()
                    continue
                # Multi-line comment /* ... */
                elif next_ch == "*":
                    comment_loc = SourceLocation(self._line, self._column)
                    self._advance_n(2)
                    closed = False
                    while not self._is_at_end():
                        if self._peek() == "*" and self._pos + 1 < self._length and self._source[self._pos + 1] == "/":
                            self._advance_n(2)
                            closed = True
                            break
                        self._advance()
                    if not closed:
                        raise LexerError("Unterminated block comment (/* ... */)", comment_loc)
                    continue

            # Neither whitespace nor comment
            break

    # -------------------------------------------------------------------------
    # Cursor Movement & Character Inspection
    # -------------------------------------------------------------------------

    def _is_at_end(self) -> bool:
        return self._pos >= self._length

    def _peek(self) -> str:
        if self._is_at_end():
            return "\0"
        return self._source[self._pos]

    def _peek_next(self) -> str:
        if self._pos + 1 >= self._length:
            return "\0"
        return self._source[self._pos + 1]

    def _advance(self) -> str:
        ch = self._source[self._pos]
        self._pos += 1
        if ch == "\n":
            self._line += 1
            self._column = 1
        else:
            self._column += 1
        return ch

    def _advance_n(self, count: int) -> None:
        for _ in range(count):
            self._advance()

    def _match_prefix(self, prefix: str) -> bool:
        """Check if remaining source starts with prefix without advancing."""
        return self._source.startswith(prefix, self._pos)
