"""Unit tests for the Lexer module."""

import pytest
from compiler.lexer import Lexer, LexerError, SourceLocation, Token, TokenType


@pytest.fixture
def lexer() -> Lexer:
    """Fixture providing a default Lexer instance."""
    return Lexer()


def test_empty_and_whitespace(lexer: Lexer) -> None:
    """Test tokenizing empty and whitespace-only strings."""
    assert lexer.tokenize("") == []
    assert lexer.tokenize("   \t\n \r\n  ") == []


def test_identifiers_and_keywords(lexer: Lexer) -> None:
    """Test distinction between keywords and regular identifiers."""
    source = "int count = 0; while (count < max_val) { _counter1++; }"
    tokens = lexer.tokenize(source)

    # Filter identifier and keyword tokens
    id_and_kw = [(t.type, t.value) for t in tokens if t.is_identifier() or t.is_keyword()]

    expected = [
        (TokenType.KEYWORD, "int"),
        (TokenType.IDENTIFIER, "count"),
        (TokenType.KEYWORD, "while"),
        (TokenType.IDENTIFIER, "count"),
        (TokenType.IDENTIFIER, "max_val"),
        (TokenType.IDENTIFIER, "_counter1"),
    ]
    assert id_and_kw == expected


def test_keywords_vs_prefixed_identifiers(lexer: Lexer) -> None:
    """Test that identifiers with keyword prefixes/suffixes are not misidentified."""
    source = "integer if_condition return_val while123 _for"
    tokens = lexer.tokenize(source)

    assert len(tokens) == 5
    for token in tokens:
        assert token.type == TokenType.IDENTIFIER
    assert [t.value for t in tokens] == ["integer", "if_condition", "return_val", "while123", "_for"]


def test_integer_literals(lexer: Lexer) -> None:
    """Test decimal, hex, binary, and suffixed integer literals."""
    source = "0 42 1000 0x1A 0XFF 0b1011 255u 100L 50UL"
    tokens = lexer.tokenize(source)

    assert all(t.type == TokenType.LITERAL_INT for t in tokens)
    assert [t.value for t in tokens] == [
        "0", "42", "1000", "0x1A", "0XFF", "0b1011", "255u", "100L", "50UL"
    ]


def test_floating_point_literals(lexer: Lexer) -> None:
    """Test standard floats, exponents, leading dots, and float suffixes."""
    source = "3.14159 .5 0.0 1e6 2.5e-3 4.2E+10 1.0f 0.5F"
    tokens = lexer.tokenize(source)

    assert all(t.type == TokenType.LITERAL_FLOAT for t in tokens)
    assert [t.value for t in tokens] == [
        "3.14159", ".5", "0.0", "1e6", "2.5e-3", "4.2E+10", "1.0f", "0.5F"
    ]


def test_string_literals(lexer: Lexer) -> None:
    """Test string literals including escape sequences."""
    source = r'"hello world" "string with \"quotes\"" "line\nbreak"'
    tokens = lexer.tokenize(source)

    assert all(t.type == TokenType.LITERAL_STRING for t in tokens)
    assert len(tokens) == 3
    assert tokens[0].value == '"hello world"'
    assert tokens[1].value == r'"string with \"quotes\""'
    assert tokens[2].value == r'"line\nbreak"'


def test_character_literals(lexer: Lexer) -> None:
    """Test character literals including escapes."""
    source = r"'a' 'Z' '\n' '\t' '\'' '\\' '0'"
    tokens = lexer.tokenize(source)

    assert all(t.type == TokenType.LITERAL_CHAR for t in tokens)
    assert [t.value for t in tokens] == ["'a'", "'Z'", r"'\n'", r"'\t'", r"'\''", r"'\\'", "'0'"]


def test_operators_and_maximal_munch(lexer: Lexer) -> None:
    """Test operators, multi-char operators, and maximal-munch greedy resolution."""
    source = "+ - * / % ++ -- == != <= >= << >> <<= >>= && || -> = += -= *= /= %="
    tokens = lexer.tokenize(source)

    assert all(t.type in (TokenType.OPERATOR, TokenType.ARROW) for t in tokens)
    assert [t.value for t in tokens] == [
        "+", "-", "*", "/", "%", "++", "--", "==", "!=", "<=", ">=",
        "<<", ">>", "<<=", ">>=", "&&", "||", "->", "=", "+=", "-=", "*=", "/=", "%="
    ]


def test_delimiters_and_groupers(lexer: Lexer) -> None:
    """Test braces, brackets, parens, semicolons, commas, and dots."""
    source = "{ } ( ) [ ] ; , . : ?"
    tokens = lexer.tokenize(source)

    expected_types = [
        TokenType.LBRACE,
        TokenType.RBRACE,
        TokenType.LPAREN,
        TokenType.RPAREN,
        TokenType.LBRACKET,
        TokenType.RBRACKET,
        TokenType.SEMICOLON,
        TokenType.COMMA,
        TokenType.DOT,
        TokenType.COLON,
        TokenType.QUESTION,
    ]
    assert [t.type for t in tokens] == expected_types
    assert [t.value for t in tokens] == ["{", "}", "(", ")", "[", "]", ";", ",", ".", ":", "?"]


def test_single_and_multi_line_comments_ignored(lexer: Lexer) -> None:
    """Test that comments do not generate identifier tokens or pollute stream."""
    source = """
    // Single-line comment: int ignored_var = 1;
    int actual_var = 10; /* inline block comment with fake_id */
    /*
     * Multi-line comment
     * int inside_comment = 99;
     */
    return actual_var; // trailing comment
    """
    tokens = lexer.tokenize(source)
    identifiers = [t.value for t in tokens if t.is_identifier()]

    assert identifiers == ["actual_var", "actual_var"]
    assert "ignored_var" not in identifiers
    assert "fake_id" not in identifiers
    assert "inside_comment" not in identifiers


def test_line_and_column_tracking(lexer: Lexer) -> None:
    """Test precise 1-indexed source location reporting."""
    source = (
        "int a = 5;\n"       # Line 1: 'int' @ 1:1, 'a' @ 1:5, '=' @ 1:7, '5' @ 1:9, ';' @ 1:10
        "float b = 3.14;\n"  # Line 2: 'float' @ 2:1, 'b' @ 2:7, '=' @ 2:9, '3.14' @ 2:11, ';' @ 2:15
        "   return a + b;"   # Line 3: 3 leading spaces, 'return' @ 3:4, 'a' @ 3:11
    )
    tokens = lexer.tokenize(source)

    # Check Line 1 token positions
    assert tokens[0].value == "int"
    assert tokens[0].location == SourceLocation(line=1, column=1)

    assert tokens[1].value == "a"
    assert tokens[1].location == SourceLocation(line=1, column=5)

    assert tokens[2].value == "="
    assert tokens[2].location == SourceLocation(line=1, column=7)

    assert tokens[3].value == "5"
    assert tokens[3].location == SourceLocation(line=1, column=9)

    assert tokens[4].value == ";"
    assert tokens[4].location == SourceLocation(line=1, column=10)

    # Check Line 2 token positions
    assert tokens[5].value == "float"
    assert tokens[5].location == SourceLocation(line=2, column=1)

    assert tokens[6].value == "b"
    assert tokens[6].location == SourceLocation(line=2, column=7)

    assert tokens[7].value == "="
    assert tokens[7].location == SourceLocation(line=2, column=9)

    assert tokens[8].value == "3.14"
    assert tokens[8].location == SourceLocation(line=2, column=11)

    assert tokens[9].value == ";"
    assert tokens[9].location == SourceLocation(line=2, column=15)

    # Check Line 3 token positions (with indentation)
    assert tokens[10].value == "return"
    assert tokens[10].location == SourceLocation(line=3, column=4)

    assert tokens[11].value == "a"
    assert tokens[11].location == SourceLocation(line=3, column=11)

    assert tokens[12].value == "+"
    assert tokens[12].location == SourceLocation(line=3, column=13)

    assert tokens[13].value == "b"
    assert tokens[13].location == SourceLocation(line=3, column=15)

    assert tokens[14].value == ";"
    assert tokens[14].location == SourceLocation(line=3, column=16)


def test_adjacent_tokens_without_spaces(lexer: Lexer) -> None:
    """Test expressions with minimal whitespace."""
    source = "x++ +y->val"
    tokens = lexer.tokenize(source)

    expected = [
        (TokenType.IDENTIFIER, "x"),
        (TokenType.OPERATOR, "++"),
        (TokenType.OPERATOR, "+"),
        (TokenType.IDENTIFIER, "y"),
        (TokenType.ARROW, "->"),
        (TokenType.IDENTIFIER, "val"),
    ]
    assert [(t.type, t.value) for t in tokens] == expected


def test_unterminated_string_raises_lexer_error(lexer: Lexer) -> None:
    """Test that an unclosed string literal raises LexerError."""
    source = 'int x = "unclosed string;'
    with pytest.raises(LexerError) as exc_info:
        lexer.tokenize(source)
    assert "Unterminated string literal" in str(exc_info.value)
    assert exc_info.value.location.line == 1
    assert exc_info.value.location.column == 9


def test_unterminated_block_comment_raises_lexer_error(lexer: Lexer) -> None:
    """Test that an unclosed block comment raises LexerError."""
    source = "int x = 1; /* unclosed comment starts here..."
    with pytest.raises(LexerError) as exc_info:
        lexer.tokenize(source)
    assert "Unterminated block comment" in str(exc_info.value)
    assert exc_info.value.location.line == 1


def test_complete_c_function_lexing(lexer: Lexer) -> None:
    """Test tokenizing a realistic C function with scopes, types, loops, and pointers."""
    source = """
    int compute_sum(int* arr, int length) {
        int total = 0;
        for (int i = 0; i < length; ++i) {
            total += arr[i];
        }
        return total;
    }
    """
    tokens = lexer.tokenize(source)

    # Verify braces
    braces = [t for t in tokens if t.is_brace()]
    assert len(braces) == 4  # Outer { }, Inner for { }
    assert braces[0].type == TokenType.LBRACE
    assert braces[1].type == TokenType.LBRACE
    assert braces[2].type == TokenType.RBRACE
    assert braces[3].type == TokenType.RBRACE

    # Extract all identifiers in order
    identifiers = [t.value for t in tokens if t.is_identifier()]
    assert identifiers == [
        "compute_sum", "arr", "length",
        "total",
        "i", "i", "length", "i",
        "total", "arr", "i",
        "total"
    ]
