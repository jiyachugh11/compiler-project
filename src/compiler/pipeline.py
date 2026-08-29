"""Unified Backend 1 Compiler & Static Analysis Pipeline."""

from dataclasses import dataclass
from typing import Dict, List, Optional, Set
from compiler.interning.string_pool import StringPool
from compiler.lexer.lexer import Lexer
from compiler.lexer.tokens import TokenType
from compiler.profiler.workload import WorkloadMetrics, WorkloadProfiler
from compiler.symbol_table.scope import Scope, ScopeType
from compiler.symbol_table.symbol import Symbol, SymbolRole
from compiler.symbol_table.symbol_table import SymbolTable


# C/C++ Type keywords and declaration specifiers
TYPE_KEYWORDS: Set[str] = {
    "auto", "bool", "_Bool", "char", "const", "double", "enum", "extern",
    "float", "inline", "int", "long", "register", "restrict", "short",
    "signed", "static", "struct", "typedef", "union", "unsigned", "void",
    "volatile", "size_t", "int8_t", "int16_t", "int32_t", "int64_t",
    "uint8_t", "uint16_t", "uint32_t", "uint64_t"
}


@dataclass
class AnalysisResult:
    """Complete output contract from Backend 1 to Backend 2.

    Preserves full workload fidelity for consistent hashing and benchmarking:
    - ordered identifier occurrence stream
    - unique / interned identifiers (string -> id mapping)
    - symbol table
    - scope information
    - workload statistics
    """

    identifier_stream: List[str]
    interned_identifiers: Dict[str, int]
    symbol_table: SymbolTable
    scopes: Dict[int, Scope]
    workload_metrics: WorkloadMetrics
    source_code: str


class CompilerPipeline:
    """Orchestrates Backend 1 stages:

    Source Code
    -> Lexer
    -> Identifier Extraction
    -> Scope Analysis
    -> Symbol Table
    -> String Interning
    -> Workload Profiling
    -> AnalysisResult
    """

    def __init__(self) -> None:
        self.lexer = Lexer()
        self.symbol_table = SymbolTable()
        self.string_pool = StringPool()
        self.profiler = WorkloadProfiler()

    def run(self, source_code: str) -> AnalysisResult:
        """Run the full compilation and static analysis pipeline on source code.

        Flow:
        1. Lexical Analysis: Tokenize source code into ordered tokens with source locations.
        2. Scope & Symbol Processing:
           - Track active scopes via curly braces ('{' enters FUNCTION/BLOCK scope, '}' exits).
           - Distinguish declarations from references using type specifiers and scope context.
           - Extract identifier occurrence stream preserving exact source order.
           - Intern each identifier into StringPool to obtain stable integer IDs.
           - Populate SymbolTable entries with source location, role, and intern_id metadata.
        3. Workload Profiling: Compute statistical metrics from identifier stream and scopes.
        4. Package and return the final AnalysisResult.

        Args:
            source_code: C/C++ source code string to analyze.

        Returns:
            Complete AnalysisResult contract object.
        """
        lexer = Lexer()
        symbol_table = SymbolTable()
        string_pool = StringPool()
        profiler = WorkloadProfiler()

        # 1. Lexical Analysis
        tokens = lexer.tokenize(source_code)

        identifier_stream: List[str] = []

        current_type: Optional[str] = None
        in_declaration: bool = False
        potential_func_signature: bool = False
        paren_depth: int = 0

        num_tokens = len(tokens)
        for i, token in enumerate(tokens):
            # Parentheses depth tracking
            if token.type == TokenType.LPAREN:
                paren_depth += 1
                continue
            elif token.type == TokenType.RPAREN:
                if paren_depth > 0:
                    paren_depth -= 1
                continue

            # Scope Management: Opening brace enters a new child scope
            if token.type == TokenType.LBRACE:
                scope_type = ScopeType.FUNCTION if potential_func_signature else ScopeType.BLOCK
                symbol_table.enter_scope(scope_type)
                potential_func_signature = False
                in_declaration = False
                current_type = None
                continue

            # Scope Management: Closing brace exits back to enclosing parent scope
            if token.type == TokenType.RBRACE:
                if len(symbol_table._scope_stack) > 1:
                    symbol_table.exit_scope()
                in_declaration = False
                current_type = None
                potential_func_signature = False
                continue

            # Semicolon: ends statement and resets declaration state
            if token.type == TokenType.SEMICOLON:
                in_declaration = False
                current_type = None
                potential_func_signature = False
                continue

            # Comma: preserves declaration state if declaring multiple variables
            if token.type == TokenType.COMMA:
                if in_declaration and current_type:
                    pass  # Keep in_declaration active for subsequent identifiers
                else:
                    in_declaration = False
                    current_type = None
                continue

            # Type keywords
            if (token.type == TokenType.KEYWORD or token.type == TokenType.IDENTIFIER) and token.value in TYPE_KEYWORDS:
                current_type = token.value
                in_declaration = True
                continue

            # Pointer modifier in declaration (e.g. int* ptr)
            if token.type == TokenType.OPERATOR and token.value == "*" and in_declaration:
                if current_type:
                    current_type += "*"
                continue

            # Identifier token
            if token.is_identifier():
                ident_name = token.value
                identifier_stream.append(ident_name)
                intern_id = string_pool.intern(ident_name)

                # Check if this identifier is part of a function signature (identifier followed by '(')
                is_followed_by_lparen = (i + 1 < num_tokens and tokens[i + 1].type == TokenType.LPAREN)
                if in_declaration and is_followed_by_lparen:
                    potential_func_signature = True

                curr_scope_id = symbol_table.current_scope_id
                already_declared_in_scope = ident_name in symbol_table._scope_symbols.get(curr_scope_id, {})

                if in_declaration and not already_declared_in_scope:
                    symbol = Symbol(
                        name=ident_name,
                        scope_id=curr_scope_id,
                        scope_depth=symbol_table.current_scope().depth,
                        location=token.location,
                        data_type=current_type,
                        role=SymbolRole.DECLARATION,
                        intern_id=intern_id,
                    )
                    symbol_table.insert(symbol)
                    # If not followed by comma, end declaration context for expression RHS (e.g. int x = a + b)
                    if i + 1 < num_tokens and tokens[i + 1].type not in (TokenType.COMMA, TokenType.LPAREN):
                        in_declaration = False
                else:
                    symbol = Symbol(
                        name=ident_name,
                        scope_id=curr_scope_id,
                        scope_depth=symbol_table.current_scope().depth,
                        location=token.location,
                        role=SymbolRole.REFERENCE,
                        intern_id=intern_id,
                    )
                    symbol_table.insert(symbol)
                continue

            # Other keywords (e.g. if, for, while, return) end declaration context
            if token.type == TokenType.KEYWORD and token.value not in TYPE_KEYWORDS:
                in_declaration = False
                current_type = None
                continue

        # 3. Workload Profiling
        workload_metrics = profiler.compute_metrics(identifier_stream, symbol_table)

        # 4. Result Packaging
        return AnalysisResult(
            identifier_stream=identifier_stream,
            interned_identifiers=string_pool.get_mapping(),
            symbol_table=symbol_table,
            scopes=dict(symbol_table.scopes),
            workload_metrics=workload_metrics,
            source_code=source_code,
        )
