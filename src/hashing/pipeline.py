"""Backend 2 orchestrator.

Mirrors Backend 1's CompilerPipeline: one entry point that takes the upstream
contract object (AnalysisResultLike) and returns the downstream contract
object (HashAnalysisReport).

    AnalysisResult (Backend 1)
        -> Hash functions (11)
        -> Common hash table + collision statistics
        -> Benchmarking (insert / lookup / probes / distribution / avalanche)
        -> Hash-table-backed scoped symbol-table replay      (optional)
        -> Preimage / second-preimage analysis                (optional)
        -> Adaptive recommendation
        -> HashAnalysisReport (consumed by the frontend)
"""

from typing import Optional

from hashing import security, symbol_table_hashed
from hashing.adapters import extract_symbol_events
from hashing.benchmark import BenchmarkRunner
from hashing.definitions import DEFINITIONS
from hashing.interfaces import AnalysisResultLike
from hashing.models import HashAnalysisReport
from hashing.recommender import AdaptiveRecommender


class HashAnalysisPipeline:
    """Orchestrates Backend 2 stages end-to-end."""

    def __init__(
        self,
        benchmark_runner: Optional[BenchmarkRunner] = None,
        recommender: Optional[AdaptiveRecommender] = None,
        include_security: bool = True,
        include_symbol_table: bool = True,
        security_options: Optional[dict] = None,
    ) -> None:
        """security_options is passed to security.analyze (bits, targets, structural_samples, seed)."""
        self.benchmark_runner = benchmark_runner or BenchmarkRunner()
        self.recommender = recommender or AdaptiveRecommender()
        self.include_security = include_security
        self.include_symbol_table = include_symbol_table
        self.security_options = security_options or {}

    def run(self, analysis: AnalysisResultLike) -> HashAnalysisReport:
        wm = analysis.workload_metrics
        stream = analysis.identifier_stream
        runner = self.benchmark_runner

        results = runner.run(stream, frequency=wm.identifier_frequency or None)

        if self.include_symbol_table:
            extracted = extract_symbol_events(analysis)
            if extracted is not None:
                events, parents = extracted
                for r in results:
                    r.symbol_table = symbol_table_hashed.replay(
                        runner.hash_functions[r.name], events, parents,
                        target_load=runner.target_load_factor, repeats=runner.repeats,
                    )

        security_reference = None
        if self.include_security:
            unique = list(dict.fromkeys(stream))
            for r in results:
                r.security = security.analyze(runner.hash_functions[r.name], unique, **self.security_options)
            security_reference = security.analyze(security.sha256_reference, unique, **self.security_options)

        name, reason, ranking, weights = self.recommender.recommend_detailed(results, wm)

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
            recommended_function=name,
            recommendation_reason=reason,
            workload_summary=workload_summary,
            ranking=ranking,
            weights=weights,
            security_reference=security_reference,
            definitions=dict(DEFINITIONS),
            confidence=self.recommender.confidence_for(wm),
        )
