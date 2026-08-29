"""Tests for hashing.benchmark.BenchmarkRunner."""

from hashing.benchmark import BenchmarkRunner, _default_bucket_count
from hashing.functions import HASH_FUNCTIONS
from hashing.models import HashFunctionResult


def test_default_bucket_count_targets_load_factor():
    assert _default_bucket_count(75, target_load_factor=0.75) == 100
    assert _default_bucket_count(0) == 1


def test_run_returns_one_result_per_hash_function():
    runner = BenchmarkRunner()
    stream = ["a", "b", "c", "a", "b", "a"]
    results = runner.run(stream)
    assert len(results) == len(HASH_FUNCTIONS)
    assert all(isinstance(r, HashFunctionResult) for r in results)
    assert {r.name for r in results} == set(HASH_FUNCTIONS.keys())


def test_items_inserted_matches_unique_count():
    runner = BenchmarkRunner()
    stream = ["x", "y", "x", "x", "z"]  # 3 unique
    results = runner.run(stream)
    for r in results:
        assert r.items_inserted == 3


def test_lookups_performed_matches_full_stream_length():
    runner = BenchmarkRunner()
    stream = ["x", "y", "x", "x", "z"]
    results = runner.run(stream)
    for r in results:
        assert r.lookups_performed == len(stream)


def test_fixed_bucket_count_is_respected():
    runner = BenchmarkRunner(bucket_count=17)
    results = runner.run(["a", "b", "c"])
    for r in results:
        assert r.bucket_count == 17


def test_empty_stream_does_not_crash():
    runner = BenchmarkRunner()
    results = runner.run([])
    assert len(results) == len(HASH_FUNCTIONS)
    for r in results:
        assert r.items_inserted == 0
        assert r.lookups_performed == 0


def test_all_timings_are_non_negative():
    runner = BenchmarkRunner()
    results = runner.run(["id_" + str(i) for i in range(100)])
    for r in results:
        assert r.insert_time_sec >= 0
        assert r.lookup_time_sec >= 0
        assert r.estimated_memory_bytes > 0
