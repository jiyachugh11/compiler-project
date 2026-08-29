"""Backend 2: Hash Functions, Hash Tables, Benchmarking & Adaptive Recommendation.

Consumes AnalysisResult (or anything matching AnalysisResultLike) produced by
Backend 1's CompilerPipeline and produces a HashAnalysisReport comparing
several hash functions on the actual identifier workload extracted from
source code.
"""

from hashing.pipeline import HashAnalysisPipeline
from hashing.models import HashAnalysisReport, HashFunctionResult

__all__ = [
    "HashAnalysisPipeline",
    "HashAnalysisReport",
    "HashFunctionResult",
]
