"""Backend 2 orchestrator.

Mirrors Backend 1's CompilerPipeline: one entry point that takes the
upstream contract object (AnalysisResultLike) and returns the downstream
contract object (HashAnalysisReport).

    AnalysisResult (Backend 1)
        -> Hash Functions
        -> Hash Tables
        -> Benchmarking
        -> Performance Metrics
        -> Adaptive Recommendation
        -> HashAnalysisReport (Backend 2, consumed by frontend)
"""

from typing import Optional

from hashing.benchmark import BenchmarkRunner
from hashing.interfaces import AnalysisResultLike
from hashing.models import HashAnalysisReport
from hashing.recommender import AdaptiveRecommender


class HashAnalysisPipeline:
    """Orchestrates Backend 2 stages end-to-end."""

    def __init__(
        self,
        benchmark_runner: Optional[BenchmarkRunner] = None,
        recommender: Optional[AdaptiveRecommender] = None,
    ) -> None:
        self.benchmark_runner = benchmark_runner or BenchmarkRunner()
        self.recommender = recommender or AdaptiveRecommender()

    def run(self, analysis: AnalysisResultLike) -> HashAnalysisReport:
        """Run hash function benchmarking + recommendation on a Backend 1
        AnalysisResult (or any object matching AnalysisResultLike).

        Args:
            analysis: Object exposing identifier_stream, interned_identifiers,
                and workload_metrics (see hashing.interfaces).

        Returns:
            Complete HashAnalysisReport for the frontend.
        """
        results = self.benchmark_runner.run(analysis.identifier_stream)
        recommended_name, reason = self.recommender.recommend(
            results, analysis.workload_metrics
        )

        wm = analysis.workload_metrics
        workload_summary = {
            "total_identifiers": wm.total_identifiers,
            "unique_identifiers": wm.unique_identifiers,
            "average_identifier_length": wm.average_identifier_length,
            "uniqueness_ratio": wm.uniqueness_ratio,
            "repetition_ratio": wm.repetition_ratio,
            "scope_count": wm.scope_count,
        }

        return HashAnalysisReport(
            per_function=results,
            recommended_function=recommended_name,
            recommendation_reason=reason,
            workload_summary=workload_summary,
        )
