"""Tests for hashing.recommender.AdaptiveRecommender."""

from dataclasses import dataclass, field
from typing import Dict

import pytest

from hashing.models import HashFunctionResult
from hashing.recommender import AdaptiveRecommender, _normalize
from hashing.security import SecurityResult
from hashing.symbol_table_hashed import SymbolTableBenchResult


@dataclass
class FakeWM:
    """Stand-in satisfying WorkloadMetricsLike (no import of Backend 1)."""
    total_identifiers: int = 100
    unique_identifiers: int = 50
    average_identifier_length: float = 6.0
    min_identifier_length: int = 1
    max_identifier_length: int = 12
    identifier_frequency: Dict[str, int] = field(default_factory=dict)
    repetition_ratio: float = 0.5
    uniqueness_ratio: float = 0.5
    scope_count: int = 3
    max_scope_depth: int = 2
    identifiers_per_scope: Dict[int, int] = field(default_factory=dict)


def mk(name, ins=0.01, look=0.01, pairs=5, full=0, probes=1.2, aval=0.95, mem=1000, family="Classic string hash"):
    return HashFunctionResult(
        name=name, bucket_count=100, items_inserted=50, insert_time_sec=ins,
        lookup_time_sec=look, lookups_performed=100, collisions=pairs, max_chain_length=2,
        non_empty_buckets=40, load_factor=0.5, estimated_memory_bytes=mem,
        family=family, colliding_pairs=pairs, full_hash_collisions=full,
        weighted_avg_probes=probes, avalanche_quality=aval)


def test_normalize_basic_flat_and_tolerance():
    assert _normalize([5, 5, 5]) == [0.0, 0.0, 0.0]
    assert _normalize([0, 5, 10]) == [0.0, 0.5, 1.0]
    # 100 vs 110 are within a 25% band of the best -> tied; 200 still penalised
    assert _normalize([100, 110, 200], rel_tol=0.25) == [0.0, 0.0, 1.0]
    assert _normalize([3, 4], abs_tol=1) == [0.0, 0.0]


def test_clear_winner():
    good = mk("Good", ins=0.001, look=0.001, pairs=0, probes=1.0, aval=0.99)
    bad = mk("Bad", ins=0.1, look=0.1, pairs=50, probes=2.5, aval=0.4)
    name, reason = AdaptiveRecommender().recommend([bad, good], FakeWM())
    assert name == "Good" and "runner-up: Bad" in reason


def test_empty_results_raise():
    with pytest.raises(ValueError):
        AdaptiveRecommender().recommend([], FakeWM())


def test_baseline_is_ranked_but_never_recommended():
    base = mk("Base", ins=0.0001, look=0.0001, pairs=0, probes=1.0, aval=0.99, family="Baseline (poor)")
    real = mk("Real", ins=0.01, look=0.01, pairs=5)
    name, reason, ranking, _ = AdaptiveRecommender().recommend_detailed([real, base], FakeWM())
    assert name == "Real"
    assert ranking[0].name == "Base" and ranking[0].eligible is False
    assert "never recommended" in reason


def test_full_hash_collisions_are_penalised():
    clean = mk("Clean", full=0)
    dirty = mk("Dirty", full=40)
    assert AdaptiveRecommender().recommend([dirty, clean], FakeWM())[0] == "Clean"


def test_high_repetition_weights_lookup():
    a = mk("A", ins=0.05, look=0.001, probes=1.0)
    b = mk("B", ins=0.001, look=0.05, probes=2.0)
    name, reason = AdaptiveRecommender().recommend([a, b], FakeWM(repetition_ratio=0.9, uniqueness_ratio=0.1))
    assert name == "A" and "Repetition ratio is high" in reason


def test_high_uniqueness_weights_collisions():
    low = mk("LowCollision", ins=0.01, look=0.01, pairs=0, full=0)
    high = mk("HighCollision", ins=0.005, look=0.005, pairs=80, full=10)
    wm = FakeWM(uniqueness_ratio=0.95, total_identifiers=500, repetition_ratio=0.05)
    name, reason = AdaptiveRecommender().recommend([high, low], wm)
    assert name == "LowCollision" and "collision avoidance" in reason


def test_weights_always_sum_to_one_and_ranking_is_sorted():
    rec = AdaptiveRecommender()
    for wm in (FakeWM(repetition_ratio=0.9), FakeWM(uniqueness_ratio=0.9, total_identifiers=300), FakeWM()):
        assert sum(rec._weights_for(wm).values()) == pytest.approx(1.0)
    _, _, ranking, weights = rec.recommend_detailed([mk("A"), mk("B", pairs=30)], FakeWM())
    assert [r.rank for r in ranking] == [1, 2]
    assert ranking[0].score <= ranking[1].score and sum(weights.values()) == pytest.approx(1.0)


def test_symtab_replay_time_joins_scoring_when_present():
    def st(t):
        return SymbolTableBenchResult(2, 5, 0, 8, 0, 1.2, 1.3, 1, 2, t)
    a, b = mk("A"), mk("B")
    a.symbol_table, b.symbol_table = st(0.001), st(0.05)
    name, reason, _, weights = AdaptiveRecommender().recommend_detailed([b, a], FakeWM())
    assert name == "A" and "symtab_time" in weights and "symbol-table traffic" in reason
    assert sum(weights.values()) == pytest.approx(1.0)


def test_security_note_added_for_structurally_weak_winner():
    sec = SecurityResult(10, 5, 1.0, 1.0, 1.0, 1.0, 5, 5, 1.0, ("a", "b"), "weak")
    best = mk("Weak"); best.security = sec
    _, reason = AdaptiveRecommender().recommend([best, mk("Other", pairs=90, aval=0.3)], FakeWM())
    assert "cheap second preimages" in reason


def test_confidence_levels():
    c = AdaptiveRecommender.confidence_for
    assert c(FakeWM(unique_identifiers=10)) == "low"
    assert c(FakeWM(unique_identifiers=100)) == "medium"
    assert c(FakeWM(unique_identifiers=500)) == "high"


def test_low_confidence_is_stated_in_reason():
    _, reason = AdaptiveRecommender().recommend([mk("A")], FakeWM(unique_identifiers=8))
    assert "Confidence is LOW" in reason
