"""Adaptive hash-function recommendation.

Scores each benchmarked hash function on a normalized, weighted combination
of speed, collision behavior, and memory, then adjusts the weighting based
on workload shape (from Backend 1's WorkloadMetrics):

    - High repetition_ratio (lots of repeated identifiers, e.g. loop
      counters reused everywhere) -> lookup speed matters more, since most
      accesses are lookups of a small hot set.
    - High uniqueness_ratio with a large identifier count (e.g. generated
      code, obfuscated symbols) -> collision avoidance matters more, since
      a poor distribution degrades every operation as the table fills.
    - Otherwise -> balanced weighting across insert time, lookup time, and
      collisions, with memory as a light tie-breaker.
"""

from typing import List, Tuple

from hashing.interfaces import WorkloadMetricsLike
from hashing.models import HashFunctionResult


def _normalize(values: List[float]) -> List[float]:
    """Min-max normalize to [0, 1]. Flat input (all equal) maps to all 0s
    so it doesn't distort the weighted score."""
    lo, hi = min(values), max(values)
    if hi == lo:
        return [0.0 for _ in values]
    return [(v - lo) / (hi - lo) for v in values]


class AdaptiveRecommender:
    """Recommends the best hash function for a given workload + benchmark."""

    def recommend(
        self,
        results: List[HashFunctionResult],
        workload_metrics: WorkloadMetricsLike,
    ) -> Tuple[str, str]:
        """
        Args:
            results: Output of BenchmarkRunner.run().
            workload_metrics: The workload_metrics field of AnalysisResult
                (or anything matching WorkloadMetricsLike).

        Returns:
            (recommended_function_name, human_readable_reason)
        """
        if not results:
            raise ValueError("Cannot recommend from an empty result set")

        w_insert, w_lookup, w_collision, w_memory = self._weights_for(workload_metrics)

        insert_scores = _normalize([r.insert_time_sec for r in results])
        lookup_scores = _normalize([r.lookup_time_sec for r in results])
        collision_scores = _normalize([r.collisions for r in results])
        memory_scores = _normalize([r.estimated_memory_bytes for r in results])

        combined = [
            w_insert * ins + w_lookup * look + w_collision * coll + w_memory * mem
            for ins, look, coll, mem in zip(
                insert_scores, lookup_scores, collision_scores, memory_scores
            )
        ]

        best_idx = min(range(len(results)), key=lambda i: combined[i])
        best = results[best_idx]

        reason = self._explain(best, results, workload_metrics, w_insert, w_lookup, w_collision)
        return best.name, reason

    def _weights_for(self, wm: WorkloadMetricsLike) -> Tuple[float, float, float, float]:
        """Return (insert_weight, lookup_weight, collision_weight, memory_weight)."""
        if wm.repetition_ratio >= 0.6:
            # Lots of repeated identifiers -> lookups dominate real usage.
            return (0.15, 0.45, 0.30, 0.10)
        if wm.uniqueness_ratio >= 0.8 and wm.total_identifiers >= 200:
            # Large, mostly-unique symbol set -> distribution quality matters most.
            return (0.20, 0.20, 0.50, 0.10)
        # Balanced default.
        return (0.30, 0.30, 0.30, 0.10)

    def _explain(
        self,
        best: HashFunctionResult,
        results: List[HashFunctionResult],
        wm: WorkloadMetricsLike,
        w_insert: float,
        w_lookup: float,
        w_collision: float,
    ) -> str:
        others = [r.name for r in results if r.name != best.name]
        parts = [
            f"{best.name} was selected out of {len(results)} candidates "
            f"({', '.join(others)})."
        ]
        parts.append(
            f"It had {best.collisions} collisions and a max chain length of "
            f"{best.max_chain_length} across {best.bucket_count} buckets "
            f"(load factor {best.load_factor:.2f})."
        )
        if wm.repetition_ratio >= 0.6:
            parts.append(
                f"Workload has a high repetition ratio ({wm.repetition_ratio:.2f}), "
                "so lookup speed was weighted most heavily."
            )
        elif wm.uniqueness_ratio >= 0.8 and wm.total_identifiers >= 200:
            parts.append(
                f"Workload has {wm.total_identifiers} identifiers with a high "
                f"uniqueness ratio ({wm.uniqueness_ratio:.2f}), so collision "
                "avoidance was weighted most heavily."
            )
        else:
            parts.append(
                "Workload didn't show a strong repetition or uniqueness skew, "
                "so insert time, lookup time, and collisions were weighted evenly."
            )
        return " ".join(parts)
