"""Tests for hashing.benchmark.BenchmarkRunner."""

import pytest

from hashing.benchmark import BenchmarkRunner, _default_bucket_count
from hashing.functions import HASH_FUNCTIONS
from hashing.models import HashFunctionResult

FAST = dict(repeats=1)


def test_default_bucket_count():
    assert _default_bucket_count(75, 0.75) == 100
    assert _default_bucket_count(0) == 1


def test_one_result_per_function():
    results = BenchmarkRunner(**FAST).run(["a", "b", "c", "a", "b", "a"])
    assert [r.name for r in results] == list(HASH_FUNCTIONS)
    assert all(isinstance(r, HashFunctionResult) for r in results)


def test_counts_unique_inserted_and_full_stream_looked_up():
    stream = ["x", "y", "x", "x", "z"]
    for r in BenchmarkRunner(**FAST).run(stream):
        assert r.items_inserted == 3 and r.lookups_performed == 5


def test_fixed_bucket_count_respected():
    for r in BenchmarkRunner(bucket_count=17, **FAST).run(["a", "b", "c"]):
        assert r.bucket_count == 17


def test_empty_stream_is_safe():
    for r in BenchmarkRunner(**FAST).run([]):
        assert r.items_inserted == 0 and r.hash_only_ns_per_key == 0.0 and r.weighted_avg_probes == 0.0


def test_new_metrics_are_populated_and_consistent():
    stream = [f"id_{i}" for i in range(120)] * 2
    for r in BenchmarkRunner(**FAST).run(stream):
        assert r.family
        assert r.insert_time_sec >= 0 and r.lookup_time_sec >= 0 and r.hash_only_ns_per_key > 0
        assert r.full_hash_collisions <= r.collisions
        assert r.colliding_pairs >= r.collisions
        assert 0 <= r.avalanche_quality <= 1
        assert r.weighted_avg_probes >= 1.0
        assert sum(r.bucket_distribution) == r.items_inserted
        assert 0 <= r.empty_bucket_ratio <= 1


def test_explicit_frequency_changes_weighted_probes_only():
    stream = ["a", "b", "c", "d", "e", "f"]
    base = BenchmarkRunner(bucket_count=1, **FAST).run(stream)[0]        # one chain: probes 1..6
    hot_first = BenchmarkRunner(bucket_count=1, **FAST).run(stream, frequency={"a": 100, "f": 1})[0]
    hot_last = BenchmarkRunner(bucket_count=1, **FAST).run(stream, frequency={"a": 1, "f": 100})[0]
    assert hot_first.weighted_avg_probes < base.weighted_avg_probes < hot_last.weighted_avg_probes
    assert hot_first.collisions == base.collisions


def test_lose_lose_shows_many_full_hash_collisions():
    stream = [f"identifier_{i}" for i in range(200)]
    by = {r.name: r for r in BenchmarkRunner(**FAST).run(stream)}
    assert by["Lose-lose (baseline)"].full_hash_collisions > 100
    assert by["MurmurHash3"].full_hash_collisions == 0


def test_repeated_runs_give_identical_deterministic_metrics():
    stream = ["a", "b", "a", "c"] * 20
    r1 = BenchmarkRunner(**FAST).run(stream)
    r2 = BenchmarkRunner(**FAST).run(stream)
    key = lambda r: (r.name, r.collisions, r.colliding_pairs, r.weighted_avg_probes, r.avalanche_quality)  # noqa: E731
    assert [key(r) for r in r1] == [key(r) for r in r2]
