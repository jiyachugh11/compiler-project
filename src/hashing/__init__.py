"""Backend 2: hash functions, hash tables, benchmarking, security analysis,
hash-table-backed symbol table and adaptive recommendation.

Consumes Backend 1's AnalysisResult (or anything matching AnalysisResultLike)
and produces a HashAnalysisReport.
"""

from hashing.models import HashAnalysisReport, HashFunctionResult, RankedFunction
from hashing.pipeline import HashAnalysisPipeline

__all__ = [
    "HashAnalysisPipeline",
    "HashAnalysisReport",
    "HashFunctionResult",
    "RankedFunction",
]
