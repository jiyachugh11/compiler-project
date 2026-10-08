"""Adaptive hash-function recommendation.

Each benchmarked function gets a weighted score (lower is better) over
min-max-normalised criteria:

    insert time, lookup time      measured (best of several runs)
    weighted probes               deterministic comparisons per lookup under the
                                  program's real identifier frequencies
    colliding pairs               bucket-collision damage (quadratic in chain length)
    full-hash collisions          identical 32-bit digests; the clearest sign of a poor hash
    avalanche shortfall           1 - avalanche_quality (robustness of mixing)
    memory                        rough estimate
    symbol-table replay time      only when Backend 1's scope/symbol data is available

The weights ADAPT to the workload (Backend 1's WorkloadMetrics):

    repetition_ratio >= 0.6                      -> lookups dominate: weight lookup/probes
    uniqueness_ratio >= 0.8 and >= 200 idents    -> big mostly-unique set: weight collisions
    otherwise                                    -> balanced

Functions in the "Baseline (poor)" family are ranked for comparison but are
never recommended. Ties are broken by registry order, so the result is
deterministic for identical measurements.
"""

from typing import Dict, List, Tuple

from hashing.interfaces import WorkloadMetricsLike
from hashing.models import HashFunctionResult, RankedFunction

BASELINE_FAMILY = "Baseline (poor)"
SYMTAB_WEIGHT = 0.15


def _normalize(values: List[float], rel_tol: float = 0.0, abs_tol: float = 0.0) -> List[float]:
    """Min-max normalise to [0, 1], treating near-ties as ties.

    Any value within ``max(rel_tol * best, abs_tol)`` of the best (lowest) value
    is counted as equal to it. Without this, min-max stretches differences that
    are pure noise (3 vs 4 collisions, 1.02x timing) across the full 0..1 range.
    Flat input maps to all zeros.
    """
    lo = min(values)
    band = max(rel_tol * abs(lo), abs_tol)
    adjusted = [lo if v - lo <= band else v for v in values]
    hi = max(adjusted)
    if hi == lo:
        return [0.0 for _ in values]
    return [(v - lo) / (hi - lo) for v in adjusted]


# (relative tolerance, absolute tolerance) per criterion: differences smaller
# than this are within measurement noise or sampling chance.
TOLERANCES = {
    "insert_time": (0.25, 0.0),
    "lookup_time": (0.25, 0.0),
    "probes": (0.05, 0.05),
    "collisions": (0.10, 1.0),
    "full_hash": (0.0, 1.0),
    "avalanche": (0.0, 0.05),
    "memory": (0.02, 0.0),
    "symtab_time": (0.25, 0.0),
}


class AdaptiveRecommender:
    """Recommends the best hash function for a workload + benchmark."""

    def recommend(
        self,
        results: List[HashFunctionResult],
        workload_metrics: WorkloadMetricsLike,
    ) -> Tuple[str, str]:
        name, reason, _, _ = self.recommend_detailed(results, workload_metrics)
        return name, reason

    def recommend_detailed(
        self,
        results: List[HashFunctionResult],
        workload_metrics: WorkloadMetricsLike,
    ) -> Tuple[str, str, List[RankedFunction], Dict[str, float]]:
        """Returns (name, reason, ranking, weights used)."""
        if not results:
            raise ValueError("Cannot recommend from an empty result set")

        weights = dict(self._weights_for(workload_metrics))
        has_symtab = all(r.symbol_table is not None for r in results)
        if has_symtab:
            weights = {k: v * (1 - SYMTAB_WEIGHT) for k, v in weights.items()}
            weights["symtab_time"] = SYMTAB_WEIGHT

        columns: Dict[str, List[float]] = {
            "insert_time": [r.insert_time_sec for r in results],
            "lookup_time": [r.lookup_time_sec for r in results],
            "probes": [r.weighted_avg_probes for r in results],
            "collisions": [float(r.colliding_pairs) for r in results],
            "full_hash": [float(r.full_hash_collisions) for r in results],
            "avalanche": [1.0 - r.avalanche_quality for r in results],
            "memory": [float(r.estimated_memory_bytes) for r in results],
        }
        if has_symtab:
            columns["symtab_time"] = [r.symbol_table.total_time_sec for r in results]
        normalized = {k: _normalize(v, *TOLERANCES[k]) for k, v in columns.items()}

        scored = []
        for i, r in enumerate(results):
            breakdown = {k: weights[k] * normalized[k][i] for k in weights}
            scored.append((sum(breakdown.values()), i, r, breakdown))

        scored.sort(key=lambda t: (t[0], t[1]))
        ranking = [
            RankedFunction(
                name=r.name,
                rank=pos,
                score=score,
                eligible=r.family != BASELINE_FAMILY,
                breakdown=breakdown,
            )
            for pos, (score, _, r, breakdown) in enumerate(scored, 1)
        ]

        eligible = [t for t in scored if t[2].family != BASELINE_FAMILY]
        pool = eligible or scored
        best_score, _, best, _ = pool[0]
        runner_up = pool[1][2].name if len(pool) > 1 else None

        reason = self._explain(best, runner_up, len(results), workload_metrics, weights)
        if scored[0][2].family == BASELINE_FAMILY:
            reason += (
                f" {scored[0][2].name} scored better numerically but is a deliberately poor "
                "baseline and is never recommended: with so few identifiers its flaws "
                "(clustering, full-hash collisions, no avalanche) have not had a chance to show."
            )
        level = self.confidence_for(workload_metrics)
        if level == "low":
            reason += (
                f" Confidence is LOW: only {workload_metrics.unique_identifiers} unique "
                "identifiers, so differences between functions are mostly within noise."
            )
        return best.name, reason, ranking, weights

    @staticmethod
    def confidence_for(wm: WorkloadMetricsLike) -> str:
        """How much the benchmark can distinguish functions on this workload."""
        if wm.unique_identifiers < 50:
            return "low"
        if wm.unique_identifiers < 200:
            return "medium"
        return "high"

    # ------------------------------------------------------------------ weights
    def _weights_for(self, wm: WorkloadMetricsLike) -> Dict[str, float]:
        if wm.repetition_ratio >= 0.6:
            return {"insert_time": 0.10, "lookup_time": 0.20, "probes": 0.20,
                    "collisions": 0.15, "full_hash": 0.10, "avalanche": 0.20, "memory": 0.05}
        if wm.uniqueness_ratio >= 0.8 and wm.total_identifiers >= 200:
            return {"insert_time": 0.10, "lookup_time": 0.10, "probes": 0.10,
                    "collisions": 0.30, "full_hash": 0.15, "avalanche": 0.20, "memory": 0.05}
        return {"insert_time": 0.15, "lookup_time": 0.15, "probes": 0.15,
                "collisions": 0.20, "full_hash": 0.10, "avalanche": 0.20, "memory": 0.05}

    # ---------------------------------------------------------------- explanation
    def _explain(
        self,
        best: HashFunctionResult,
        runner_up,
        n_candidates: int,
        wm: WorkloadMetricsLike,
        weights: Dict[str, float],
    ) -> str:
        parts = [f"{best.name} was selected from {n_candidates} candidates"
                 + (f" (runner-up: {runner_up})." if runner_up else ".")]
        parts.append(
            f"It produced {best.collisions} bucket collisions ({best.full_hash_collisions} "
            f"full-hash), max chain {best.max_chain_length}, "
            f"{best.weighted_avg_probes:.2f} comparisons per lookup under this program's "
            f"identifier frequencies, and avalanche quality {best.avalanche_quality:.2f} "
            f"(1.0 = ideal) at load factor {best.load_factor:.2f}."
        )
        if wm.repetition_ratio >= 0.6:
            parts.append(
                f"Repetition ratio is high ({wm.repetition_ratio:.2f}), so lookup speed and "
                "probe count were weighted most heavily."
            )
        elif wm.uniqueness_ratio >= 0.8 and wm.total_identifiers >= 200:
            parts.append(
                f"{wm.total_identifiers} identifiers with uniqueness ratio "
                f"{wm.uniqueness_ratio:.2f}, so collision avoidance was weighted most heavily."
            )
        else:
            parts.append("No strong repetition or uniqueness skew, so criteria were weighted evenly.")
        if "symtab_time" in weights:
            parts.append("Scoring also included a replay of this program's scoped symbol-table traffic.")
        if best.security is not None and best.security.structural_second_preimages_found:
            parts.append(
                "Note: this function admits cheap second preimages, so it suits trusted source "
                "code but not adversarial input (hash-flooding risk)."
            )
        return " ".join(parts)
