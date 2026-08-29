"""Tests for hashing.recommender.AdaptiveRecommender."""

from dataclasses import dataclass, field
from typing import Dict

import pytest

from hashing.models import HashFunctionResult
from hashing.recommender import AdaptiveRecommender, _normalize


@dataclass
class FakeWorkloadMetrics:
    """Minimal stand-in satisfying WorkloadMetricsLike for unit tests --
    deliberately NOT importing Backend 1's real WorkloadMetrics, to prove
    the recommender only depends on the structural interface."""

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


def make_result(name, insert_t, lookup_t, collisions, memory=1000):
    return HashFunctionResult(
        name=name,
        bucket_count=100,
        items_inserted=50,
        insert_time_sec=insert_t,
        lookup_time_sec=lookup_t,
        lookups_performed=100,
        collisions=collisions,
        max_chain_length=2,
        non_empty_buckets=40,
        load_factor=0.5,
        estimated_memory_bytes=memory,
        bucket_distribution=[1] * 100,
    )


def test_normalize_flat_input_returns_zeros():
    assert _normalize([5, 5, 5]) == [0.0, 0.0, 0.0]


def test_normalize_basic_range():
    assert _normalize([0, 5, 10]) == [0.0, 0.5, 1.0]


def test_recommend_picks_clear_winner():
    results = [
        make_result("Good", insert_t=0.001, lookup_t=0.001, collisions=0),
        make_result("Bad", insert_t=0.1, lookup_t=0.1, collisions=50),
    ]
    recommender = AdaptiveRecommender()
    name, reason = recommender.recommend(results, FakeWorkloadMetrics())
    assert name == "Good"
    assert "Good" in reason
    assert "Bad" in reason  # mentioned as one of the other candidates


def test_recommend_raises_on_empty_results():
    recommender = AdaptiveRecommender()
    with pytest.raises(ValueError):
        recommender.recommend([], FakeWorkloadMetrics())


def test_high_repetition_weights_lookup_heavily():
    # Function A: fast lookup, slower insert, few collisions.
    # Function B: fast insert, slow lookup.
    results = [
        make_result("A", insert_t=0.05, lookup_t=0.001, collisions=1),
        make_result("B", insert_t=0.001, lookup_t=0.05, collisions=1),
    ]
    wm = FakeWorkloadMetrics(repetition_ratio=0.9, uniqueness_ratio=0.1)
    recommender = AdaptiveRecommender()
    name, reason = recommender.recommend(results, wm)
    assert name == "A"
    assert "repetition ratio" in reason


def test_high_uniqueness_large_workload_weights_collisions_heavily():
    results = [
        make_result("LowCollision", insert_t=0.01, lookup_t=0.01, collisions=0),
        make_result("HighCollision", insert_t=0.005, lookup_t=0.005, collisions=80),
    ]
    wm = FakeWorkloadMetrics(
        uniqueness_ratio=0.95, total_identifiers=500, repetition_ratio=0.05
    )
    recommender = AdaptiveRecommender()
    name, reason = recommender.recommend(results, wm)
    assert name == "LowCollision"
    assert "uniqueness ratio" in reason
