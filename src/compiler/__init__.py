"""HashSense Compiler & Static Analysis Module.

Backend 1 component for lexical analysis, scope resolution,
symbol table management, string interning, and workload profiling.
"""

from compiler.pipeline import AnalysisResult, CompilerPipeline

__all__ = ["CompilerPipeline", "AnalysisResult"]
